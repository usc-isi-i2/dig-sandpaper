from operator import itemgetter
import datetime
import json

__name__ = "DocumentsRerank"
name = __name__


class SimilarityScoreRerank(object):
    name = "SimilarityScoreRerank"
    component_type = __name__

    def __init__(self, config):
        self.config = config

    def remove_blacklisted_documents(self, clauses, documents):
        """
        This function is implemented because of the sage issue # 123
        https://github.com/isi-usc-edu/sage-issue-tracker/issues/123

        This will come into picture when the whole query is wrapped in double quotes and we have black listed
        articles for that IFP. Currently black listed articles are ignored if the predicate is not "keywords
        This is the best place to do this as we have the black listed articles and the results available
        """
        whitelist_articles = list()
        for clause in clauses:
            blacklist_doc_ids = clause.get('black_list', [])
            for document in documents:
                if document['_id'] not in blacklist_doc_ids:
                    whitelist_articles.append(document)
        return whitelist_articles

    def score_rerank(self, clauses, documents):
        for clause in clauses:
            sd_dict = {}
            if "similar_docs" in clause:
                similar_docs = clause['similar_docs']
                for similar_doc in similar_docs:
                    sd_dict[similar_doc['doc_id']] = {
                        'score': similar_doc['score'],
                        'sentence_id': similar_doc['sentence_id']
                    }

                # re rank the results now
                for document in documents:
                    if document['_id'] in sd_dict:
                        document['_source']['similarity_score'] = sd_dict[document['_id']]['score']
                        sentence_ids = sd_dict[document['_id']]['sentence_id']
                        matched_sentences = list()
                        if not isinstance(sentence_ids, list):
                            sentence_ids = [sentence_ids]
                        for sentence_id in sentence_ids:
                            if sentence_id == 0:
                                title = document['_source']['knowledge_graph']['title'][0]['value']
                                matched_sentences.append(title)
                                # add this to highlights as well
                                if 'highlight' not in document:
                                    document['highlight'] = dict()
                                document['highlight']['knowledge_graph.title.value'] = [title]
                            else:
                                try:
                                    matched_sentences.append(document['_source']['split_sentences'][sentence_id - 1])
                                except:
                                    document['_to_be_deleted'] = True
                        document['_source']['matched_sentence'] = matched_sentences
                        document['_score'] = sd_dict[document['_id']]['score']
                        document['_sorting_score'] = -1 * float(sd_dict[document['_id']]['score'])
                        event_date = self.get_event_date(document)
                        document['_sorting_date'] = event_date if event_date else datetime.datetime.now().isoformat()

                for document in documents:
                    if document.get('_to_be_deleted', False):
                        documents.remove(document)

                # sort by relevance vs sort by recent
                if clause.get('resort_by', 'recent').lower() == 'recent':
                    sorted_clipped_documents = sorted(documents, key=itemgetter('_sorting_date', '_sorting_score'),
                                                      reverse=True)
                elif clause.get('resort_by', 'recent').lower() == 'relevance':
                    sorted_clipped_documents = sorted(documents, key=itemgetter('_sorting_score'), reverse=True)
                else:
                    sorted_clipped_documents = sorted(documents, key=itemgetter('_sorting_date', '_sorting_score'),
                                                      reverse=True)
                # return at most 30 documents, save mobile data for users
                cut_off_number = min(30, len(sorted_clipped_documents))
                return sorted_clipped_documents[:cut_off_number]
        return documents

    @staticmethod
    def get_event_date(document):
        event_date = None
        try:
            kg = document['_source']['knowledge_graph']
            if 'event_date' in kg and len(kg['event_date']) > 0:
                event_date = kg['event_date'][0]['value']

        except:
            return None
        return event_date

    @staticmethod
    def add_highlights_docs(docs):
        """
        "highlight": {
          "knowledge_graph.title.value": [
            "Before 1 January 2018, will <em>South</em> <em>Korea</em> file a World Trade Organization dispute against the United States related to solar panels?"
          ]
        }
        """
        if not isinstance(docs, list):
            docs = [docs]

        for doc in docs:
            if 'matched_sentence' in doc['_source']:
                matched_sentences = doc['_source']['matched_sentence']
                for sentence in matched_sentences:
                    # also add matched sentence to knowledge graph
                    doc['_source']['knowledge_graph']['matched_sentence'] = [{'key': sentence, 'value': sentence}]

                paragraph = SimilarityScoreRerank.get_description(doc)
                if paragraph:
                    high_para = SimilarityScoreRerank.create_highlighted_sentences(matched_sentences, paragraph)
                    if high_para:
                        if 'highlight' not in doc:
                            doc['highlight'] = dict()
                        doc['highlight']['knowledge_graph.description.value'] = [high_para]
        return docs

    @staticmethod
    def get_description(doc):
        if 'knowledge_graph' in doc['_source']:
            if 'description' in doc['_source']['knowledge_graph']:
                if len(doc['_source']['knowledge_graph']['description']) > 0:
                    return doc['_source']['knowledge_graph']['description'][0]['value']
        return None

    @staticmethod
    def create_highlighted_sentences(sentences, paragraph):
        high_para = ''
        if not isinstance(sentences, list):
            sentences = [sentences]
        for sentence in sentences:
            index = paragraph.find(sentence.strip())
            if index == -1:
                continue

            high_para += paragraph[0:index]
            n = len(sentence)
            high_para += '<em>{}</em>'.format(sentence)
            high_para += paragraph[index + n:]
        return high_para

    def postprocess(self, query, result):
        clauses = query["SPARQL"]["where"]["clauses"]
        if not isinstance(result, list):
            documents = result["hits"]["hits"]
            reranked_docs = self.score_rerank(clauses, documents)
            reranked_highlighted_docs = self.add_highlights_docs(reranked_docs)
            result["hits"]["hits"] = self.remove_blacklisted_documents(clauses, reranked_highlighted_docs)
            return result
        else:
            results = []
            for r in result:
                documents = r["hits"]["hits"]
                reranked_docs = self.score_rerank(clauses, documents)
                reranked_highlighted_docs = self.add_highlights_docs(reranked_docs)
                r["hits"]["hits"] = self.remove_blacklisted_documents(clauses, reranked_highlighted_docs)
                results.append(r)
            return results


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == SimilarityScoreRerank.name:
        return SimilarityScoreRerank(component_config)
    else:
        raise ValueError("Unsupported document ranker {}".
                         format(component_name))
