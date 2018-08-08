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
        # similarity_url = '{}?query={}&k={}'.format(self.constraint_remap_config['similarity_url'],
        #                                            keywords, self.constraint_remap_config['k'])
        # similar_docs = list()
        # try:
        #     response = requests.get(similarity_url)
        #     if response.status_code == 200:
        #         similar_docs.extend(response.json())
        # except Exception as e:
        #     print('Error: {}, while calling document similarity for query: {}'.format(e, keywords))

        similar_docs = [
            {
                "doc_id": "376bb709f21c0d639be8e354026aa1092c34671bc73fb909377db2cd8b7bf7df",
                "score": 0.88,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "ed85fa9269d02fa9e360bff82b8dd9af0be51319f1f918bfb22be578104d1031",
                "score": 0.86,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "16c19707455a2bd5f7d5cec469f512ca3a07559409a5a1b164a9ef13fd8a90cc",
                "score": 0.85,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "f59e376140c150f20b4698f8bcca5dc1d1c8a3653d38788842891000579bab49",
                "score": 0.77,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "6236905504cbfdb4747244bc1559b15166e52ddb4598acbe1f21df6764f77cc9",
                "score": 0.72,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "d3f9a7bdbd913347dc0d70bf28f97a6d1985eff0bc989b857ba2fdbaea9ae8f7",
                "score": 0.66,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "e8edc4cba8caeaad9975ed00eca960120688652918c28bce4bbe3655b043b0f7",
                "score": 0.5,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "85657fc04e1e93f8083ee9c91783988d03e087e13f3fc744d3adc43564aae69b",
                "score": 0.44,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "2aa50c9230dd59a54983b99de75004584a9786579d6004021b8d849d9dbc9d6b",
                "score": 0.32,
                "sentence": "Some sentence"
            },
            {
                "doc_id": "4e20cc7681b5c9bbea28b04cfa44a7846699ec40f8982ce678b60981f9f19545",
                "score": 0.09,
                "sentence": "Some sentence"
            }
        ]
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
