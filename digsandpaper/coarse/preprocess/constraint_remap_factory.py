from digsandpaper.sandpaper_utils import load_json_file
import requests
from etk.extractors.glossary_extractor import GlossaryExtractor
from etk.crf_tokenizer import CrfTokenizer
import uuid

__name__ = "ConstraintReMapping"
name = __name__


class ConstraintReMapSimilarity(object):
    name = "ConstraintReMapSimilarity"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        filename = "__constraint_remap_similarity"
        file = self.config["constraint_remap_config"]
        if isinstance(file, dict):
            self.constraint_remap_config = file
        else:
            self.constraint_remap_config = load_json_file(file)
        self.tokenizer = CrfTokenizer()
        self.glossary_extractor = GlossaryExtractor(self.constraint_remap_config['countries_list'],
                                                    "glossary_extractor",
                                                    tokenizer=self.tokenizer,
                                                    case_sensitive=False, ngrams=self.constraint_remap_config['ngrams'])

    def call_doc_similarity(self, keywords, rerank_by_doc, start_date, end_date):
        """
        :param keywords: a string, a query, A dark knight
        :return: similar docs as returned by the vector similarity service
        """
        payload = {'query': keywords, 'k': self.constraint_remap_config['k'], 'rerank_by_doc': rerank_by_doc}
        if start_date is not None:
            payload['start_date'] = start_date
        if end_date is not None:
            payload['end_date'] = end_date

        """
        if rerank_by_doc is true then the results are returned as:
        [ {
            'doc_id': str(doc_id),
            'id_score_tups': [(str(faiss_id), diff_score <float32>) ],
            'score': doc_relevance <float32>
          } 
        ]
        
        otherwise the results are:
        [ {
            'score': diff_score <float32>, 
            'sentence_id': str(<int64>)
          } 
        ]
        """
        similar_docs = list()
        try:
            response = requests.get(self.constraint_remap_config['similarity_url'], params=payload)
            if response.status_code == 200:
                similar_docs.extend(response.json())
        except Exception as e:
            print('Error: {}, while calling document similarity for query: {}'.format(e, keywords))

        if rerank_by_doc:
            for similar_doc in similar_docs:
                similar_doc['sentence_id'] = [divmod(int(x[0]), 10000)[1] for x in similar_doc['id_score_tups']]

        else:
            for similar_doc in similar_docs:
                doc_id, real_sentence_id = divmod(int(similar_doc['sentence_id']), 10000)
                similar_doc['sentence_id'] = real_sentence_id
                similar_doc['doc_id'] = str(doc_id)
        return similar_docs

    def extract_using_glossary(self, text):

        tokens = self.tokenizer.tokenize(text)

        extractions = [i.value for i in self.glossary_extractor.extract(tokens)]
        return extractions

    def add_country_clause(self, where):
        clauses = where.get('clauses', None)

        if clauses:
            keywords_clause = None
            constraint_countries = []
            for clause in clauses:
                if clause.get('predicate', '') == 'keywords':
                    keywords_clause = clause
                elif clause.get('predicate', '') == 'country' and 'constraint' in clause:
                    constraint_countries.append(clause['constraint'].lower())

            if keywords_clause:
                extracted_countries = keywords_clause['extracted_countries']
                for country in extracted_countries:
                    if country.lower() not in constraint_countries:
                        clauses.append({'constraint': country.lower(), 'isOptional': False, 'predicate': 'country',
                                        '_id': uuid.uuid4().hex, 'type': 'country'})

            where['clauses'] = clauses
        return where

    @staticmethod
    def get_date_range_query(filters):
        start_date = None
        end_date = None
        if not isinstance(filters, list):
            filters = [filters]

        for filter in filters:
            if 'clauses' in filter:
                clauses = filter['clauses']
                if not isinstance(clauses, list):
                    clauses = [clauses]
                for clause in clauses:
                    if clause.get('variable', '') == '?event_date_filter' and clause.get('operator', '') == '>=':
                        start_date_iso = clause.get('constraint')
                        start_date = start_date_iso.split('T')[0]
                    elif clause.get('variable', '') == '?event_date_filter' and clause.get('operator', '') == '<=':
                        end_date_iso = clause.get('constraint')
                        end_date = end_date_iso.split('T')[0]
        return start_date, end_date

    @staticmethod
    def subtract_lists(similar_articles, blacklisted_articles):
        """
        Helper function to perform a set subtract between the list of articles returned by faiss and blacklisted
        articles for the given IFP by users
        :param similar_articles:  list of similar articles to the query as returned by FAISS
        :param blacklisted_articles: blacklisted articles for this query as set by users on SAGE
        :return: similar_articles - blacklisted_articles
        """

        return list(set(similar_articles) - set(blacklisted_articles))

    def preprocess_clause(self, clause, start_date=None, end_date=None):
        if "constraint" not in clause:
            if "clauses" in clause:
                for c in clause["clauses"]:
                    self.preprocess_clause(c, start_date=start_date, end_date=end_date)

        if "constraint" in clause:
            predicate = clause.get('predicate', "")
            if predicate and predicate == "keywords":
                rerank_by_doc = clause.get('rerank_by_doc', 'false').lower() == 'true'
                all_similar_docs = self.call_doc_similarity(clause['constraint'], rerank_by_doc, start_date, end_date)

                all_similar_doc_ids = [x['doc_id'] for x in all_similar_docs]
                similar_docs = list()
                blacklisted_doc_ids = clause.get('black_list', [])
                if len(blacklisted_doc_ids) > 0:
                    white_doc_ids = self.subtract_lists(all_similar_doc_ids, blacklisted_doc_ids)
                    similar_docs.extend([doc for doc in all_similar_docs if doc['doc_id'] in white_doc_ids])
                else:
                    similar_docs = all_similar_docs

                clause['type'] = '_id'
                clause["similar_docs"] = similar_docs
                clause["rerank_by_doc"] = rerank_by_doc
                clause['values'] = [x['doc_id'] for x in similar_docs]
                clause['extracted_countries'] = self.extract_using_glossary(clause['constraint'])
                clause.pop('constraint', None)

    def preprocess(self, query):
        where = query["SPARQL"]["where"]
        start_date, end_date = self.get_date_range_query(where.get('filters', list()))
        self.preprocess_clause(where, start_date=start_date, end_date=end_date)
        where = self.add_country_clause(query["SPARQL"]["where"])
        query["SPARQL"]["where"] = where
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ConstraintReMapSimilarity.name:
        return ConstraintReMapSimilarity(component_config)
    else:
        raise ValueError("Unsupported constraint remap component {}".
                         format(component_name))
