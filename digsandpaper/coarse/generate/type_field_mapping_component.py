import json
import codecs

__name__ = "TypeFieldMapping"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class TypeFieldMapping(object):

    name = "TypeFieldMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_field_mappings"]
        self.type_field_mapping = load_json_file(file)

    def add_types_to_filters(self, f):
        if "type" in f:
            t = f["type"]
            if t in self.type_field_mapping:
                f["fields"] = []
                for field in self.type_field_mapping[t]:
                    f["fields"].append({"name": field})
        if "clauses" in f:
            for clause in f["clauses"]:
                self.add_types_to_filters(clause)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        where_clauses = where["clauses"]
        filters = where["filters"]

        for clause in where_clauses:
            if "type" not in clause:
                continue
            t = clause["type"]
            if t in self.type_field_mapping:
                clause["fields"] = []
                for field in self.type_field_mapping[t]:
                    clause["fields"].append({"name": field})

        for f in filters:
            self.add_types_to_filters(f)

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == TypeFieldMapping.name:
        return TypeFieldMapping(component_config)
    else:
        raise ValueError("Unsupported type field mapping component {}".
                         format(component_name))
