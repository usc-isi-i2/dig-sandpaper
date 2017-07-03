import json
import codecs
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections

__name__ = "ExecuteQueryComponent"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class ExecuteElasticsearchQuery(object):

    name = "ExecuteElasticsearchQuery"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        if "endpoints" in self.config:
            self.endpoints = self.config["endpoints"]
        else:
            self.host = self.config["host"]
            self.port = self.config["port"]
            self.endpoints = ["{}:{}".format(self.host, self.port)]
        connections.create_connection(hosts=self.endpoints,
                                      timeout=self.config.get("timeout",15),
                                      retry_on_timeout=True,
                                      maxsize=25)

        return

    def replace_range_operator(self, v, op, new_value):
        if op in v:
            if v[op].startswith("__placeholder__"):
                 v[op] = v[op].replace("__placeholder__", new_value.split()[0])         

    def replace_value(self, doc, clause_id, new_value):
        for (k,v) in doc.iteritems():
            if isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        self.replace_value(e, clause_id, new_value)
            if isinstance(v, dict):
                if "_name" in v and v["_name"].startswith(clause_id):
                    if "query" in v:
                        if v["query"] == "__placeholder__":
                            v["query"] = new_value
                    self.replace_range_operator(v, "lt", new_value)
                    self.replace_range_operator(v, "lte", new_value)
                    self.replace_range_operator(v, "gt", new_value)
                    self.replace_range_operator(v, "gte", new_value)
                self.replace_value(v, clause_id, new_value)


    # assumes results is set
    def find_values(self, doc, field_elements, results):
        while len(field_elements) > 1:
            field_element = field_elements[0]
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
                    return
                next_doc = doc[field_element]
                if isinstance(next_doc, list):
                    for d in next_doc:
                        self.find_values(d, field_elements[1:],results)
                        return
                self.find_values(next_doc, field_elements[1:], results)
                return
        field_element = field_elements[0]

        if field_element in doc:
            results.add(doc[field_element])

    def get_previous_results(self, previous_query, previous_results):
        fields = previous_query["clause_fields"]
        if "variable_to_clause_id" in previous_query:
            to_insert_by_variable = {}
            for hit in previous_results["hits"]["hits"]:
                for field in fields:
                    variable = field["variable"]
                    to_insert = to_insert_by_variable.get(variable, set())
                    name = field["name"]
                    field_elements = name.split(".")
                    self.find_values(hit["_source"], field_elements, to_insert)
                    to_insert_by_variable[variable] = to_insert
            for variable in to_insert_by_variable.keys():
                to_insert_by_variable[variable] = list(to_insert_by_variable[variable])
            return to_insert_by_variable
        else:
            to_insert = set()
            for hit in previous_results["hits"]["hits"]:
                for field in fields:
                    name = field["name"]
                    field_elements = name.split(".")
                    self.find_values(hit["_source"], field_elements, to_insert)
            return list(to_insert)

    def execute_search(self, query):
        s = Search().from_dict(query["search"])\
                        .index(query["index"])\
                        .doc_type(query["doc_type"])
        return s.execute()

    def execute(self, query):
        if isinstance(query["ELASTICSEARCH"], dict):
            return self.execute_search(query["ELASTICSEARCH"])
        elif isinstance(query["ELASTICSEARCH"], list):
            all_results = []
            previous_results = None
            previous_query = None
            for query in query["ELASTICSEARCH"]:
                if "clause_fields" not in query:
                    if previous_results and previous_query:
                        previous_results_dict = previous_results.to_dict()
                        to_insert = self.get_previous_results(previous_query, previous_results_dict)
                        if isinstance(to_insert, dict):
                            for var, clause_ids in previous_query["variable_to_clause_id"].iteritems():
                                for clause_id in clause_ids:
                                    print "replacing {}".format(clause_id)
                                    self.replace_value(query, clause_id, " ".join(to_insert[var]))
                        else:
                            clause_id = previous_query["clause_id"]
                            self.replace_value(query, clause_id, " ".join(to_insert))
                    all_results.append(self.execute_search(query))
                    if len(all_results) == 1:
                        return all_results[0]
                    return all_results
                else:
                    previous_results = self.execute_search(query)
                    all_results.append(previous_results)
                    previous_query = query

        return response


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ExecuteElasticsearchQuery.name:
        return ExecuteElasticsearchQuery(component_config)
    else:
        raise ValueError("Unsupported query execution component {}".
                         format(component_name))
