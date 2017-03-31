import json

class FineEngine(object):

    def __init__(self, config):
        self.config = config
        self._initialize()

    def _initialize(self):
        self.name = ""

    def find_value(self, doc, field_elements):
        while len(field_elements) > 1:
            field_element = field_elements.pop(0)
            if '[' in field_element:
                if not field_element.startswith('['):
                    array_field_elements = field_element.split('[', 1)
                    array_field_element = array_field_elements[0]
                    doc = doc[array_field_element]
                    field_element = array_field_elements[1]
                array_elements = field_element.split(']')
                for array_element in array_elements:
                    if not array_element:
                        continue
                    if array_element.startswith('['):
                        array_element = array_element[1:]
                    if array_element.isdigit() and isinstance(doc, list):
                        doc = doc[int(array_element)]
                    else:
                        doc = doc[array_element]
            else:
                if field_element not in doc:
                    doc[field_element] = {}
                doc = doc[field_element]
        field_element = field_elements[0]

        return doc.get(field_element, None)

    def execute(self, expanded_queries, coarse_results):
        for (query, results) in zip(expanded_queries, coarse_results):
            if query.get("type") == "Point Fact":
                sparql = query.get("SPARQL")
                select = sparql.get("select")
                variables = select.get("variables")
                where = sparql.get("where")
                clauses = where.get("clauses")

                result = results.to_dict()
                for hit in result["hits"]["hits"]:

                    answers = {}
                    for v in variables:
                        potential_matched_clauses = []
                        if where["variable"] == v["variable"]:
                            potential_matched_clauses.append({"fields":[{"name":"doc_id","weight":1.0}]})
                        for c in clauses:
                            if c.get("variable") == v["variable"]:
                                potential_matched_clauses.append(c)

                        best_field = ""
                        best_weight = 0.0
                        best_value = None
                        for c in potential_matched_clauses:
                            for field in c.get("fields", []):
                                name = field["name"]
                                weight = field.get("weight", 1.0)
                                field_elements = name.split(".")
                                value = self.find_value(hit["_source"], field_elements)
                                if value:
                                    if weight > best_weight:
                                        best_field = name
                                        best_weight = weight
                                        best_value = value
                            if best_value:
                               answers[v["variable"]] = best_value
                    if len(answers) == len(variables):
                        return answers
        return {}
