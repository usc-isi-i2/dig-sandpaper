from digsandpaper.sandpaper_utils import load_json_file
import requests

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

    def call_doc_similarity(self, keywords):
        """
        The commented out code is what this function will do when ready, right now return a list of similar docs
        :param keywords:
        :return:
        """
        payload = {'query': keywords, 'k': self.constraint_remap_config['k']}

        similar_docs = list()
        try:
            response = requests.get(self.constraint_remap_config['similarity_url'], params=payload)
            if response.status_code == 200:
                similar_docs.extend(response.json())
        except Exception as e:
            print('Error: {}, while calling document similarity for query: {}'.format(e, keywords))

        for similar_doc in similar_docs:
            doc_id, real_sentence_id = divmod(int(similar_doc['sentence_id']), 10000)
            similar_doc['sentence_id'] = str(real_sentence_id)
            similar_doc['doc_id'] = str(doc_id)
        return similar_docs

    def preprocess_clause(self, clause):
        if "constraint" not in clause:
            if "clauses" in clause:
                for c in clause["clauses"]:
                    self.preprocess_clause(c)

        if "constraint" in clause:
            predicate = clause.get('predicate', "")
            if predicate and predicate == "keywords":
                similar_docs = self.call_doc_similarity(clause['constraint'])
                clause['type'] = '_id'
                clause["similar_docs"] = similar_docs
                clause['values'] = [x['doc_id'] for x in similar_docs]
                clause.pop('constraint', None)

    def preprocess(self, query):
        where = query["SPARQL"]["where"]
        self.preprocess_clause(where)
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ConstraintReMapSimilarity.name:
        return ConstraintReMapSimilarity(component_config)
    else:
        raise ValueError("Unsupported constraint remap component {}".
                         format(component_name))
