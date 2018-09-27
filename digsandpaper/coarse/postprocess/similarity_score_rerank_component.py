from operator import itemgetter

__name__ = "DocumentsRerank"
name = __name__


class SimilarityScoreRerank(object):
    name = "SimilarityScoreRerank"
    component_type = __name__

    def __init__(self, config):
        self.config = config

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
                        sentence_id = int(sd_dict[document['_id']]['sentence_id'])
                        if sentence_id == 0:
                            matched_sentence = document['_source']['knowledge_graph']['title'][0]['value']
                        else:
                            matched_sentence = document['_source']['split_sentences'][sentence_id-1]
                        document['_source']['matched_sentence'] = matched_sentence
                        document['_score'] = sd_dict[document['_id']]['score']
                order = self.config.get("sort", 'desc')
                reverse = order == 'desc'
                return sorted(documents, key=itemgetter('_score'), reverse=reverse)
        return documents

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
                sentence = doc['_source']['matched_sentence']
                # also add matched sentence to knowledge graph
                doc['_source']['knowledge_graph']['matched_sentence'] = [{'key': sentence, 'value': sentence}]

                paragraph = SimilarityScoreRerank.get_description(doc)
                if paragraph:
                    high_para = SimilarityScoreRerank.create_highlighted_sentences(sentence, paragraph)
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
    def create_highlighted_sentences(sentence, paragraph):
        high_para = ''
        index = paragraph.find(sentence)
        if index == -1:
            return None

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
            result["hits"]["hits"] = self.add_highlights_docs(reranked_docs)
            return result
        else:
            results = []
            for r in result:
                documents = r["hits"]["hits"]
                reranked_docs = self.score_rerank(clauses, documents)
                r["hits"]["hits"] = self.add_highlights_docs(reranked_docs)
                results.append(r)
            return results


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == SimilarityScoreRerank.name:
        return SimilarityScoreRerank(component_config)
    else:
        raise ValueError("Unsupported document ranker {}".
                         format(component_name))
