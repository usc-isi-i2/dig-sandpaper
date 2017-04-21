import json
import codecs

__name__ = "TypeQueryMapping"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class TypeQueryMapping(object):

    name = "TypeQueryMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_query_mappings"]
        self.type_query_mapping = load_json_file(file)

    def add_types_to_filters(self, f):
        if "type" in f:
            t = f["type"]
            if t in self.type_query_mapping:
                f["query_type"] = self.type_query_mapping[t]
        if "clauses" in f:
            for clause in f["clauses"]:
                self.add_types_to_filters(clause)

    def generate_where(self, where):
        where_clauses = where["clauses"]
        
        if "type" in where:
            t = where["type"]
            if t in self.type_query_mapping:
                where["query_type"] = self.type_query_mapping[t]

        for clause in where_clauses:
            if "type" not in clause:
                continue
            t = clause["type"]
            if t in self.type_query_mapping:
                if "clauses" in clause:
                    self.generate_where(clause)
                else:
                    clause["query_type"] = self.type_query_mapping[t]

        if "filters" in where:
            filters = where["filters"]
            for f in filters:
                self.add_types_to_filters(f)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        self.generate_where(where)        
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == TypeQueryMapping.name:
        return TypeQueryMapping(component_config)
    else:
        raise ValueError("Unsupported type query mapping component {}".
                         format(component_name))
