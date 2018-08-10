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
                        'sentence': similar_doc['sentence']
                    }

                # re rank the results now
                for document in documents:
                    if document['_id'] in sd_dict:
                        document['_source']['similarity_score'] = sd_dict[document['_id']]['score']
                        document['_source']['matched_sentence'] = sd_dict[document['_id']]['sentence']
                        document['_score'] = sd_dict[document['_id']]['score']
                order = self.config.get("sort", 'desc')
                reverse = order == 'desc'
                return sorted(documents, key=itemgetter('_score'), reverse=reverse)
        return documents

    def postprocess(self, query, result):
        clauses = query["SPARQL"]["where"]["clauses"]
        if not isinstance(result, list):
            documents = result["hits"]["hits"]
            result["hits"]["hits"] = self.score_rerank(clauses, documents)
            return result
        else:
            results = []
            for r in result:
                documents = r["hits"]["hits"]
                r["hits"]["hits"] = self.score_rerank(clauses, documents)
                results.append(r)
            return results


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == SimilarityScoreRerank.name:
        return SimilarityScoreRerank(component_config)
    else:
        raise ValueError("Unsupported document ranker {}".
                         format(component_name))
