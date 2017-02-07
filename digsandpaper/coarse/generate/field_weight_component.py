import json
import codecs

__name__ = "FieldWeightMapping"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class FieldWeightMapping(object):

    name = "FieldWeightMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["field_weight_mappings"]
        self.field_weight_mapping = load_json_file(file)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        where_clauses = where["clauses"]
        filters = where["filters"]

        for clause in where_clauses:
            if "fields" not in clause:
                continue
            for field in clause["fields"]:
                if field["name"] in self.field_weight_mapping:
                    field["weight"] = self.field_weight_mapping[field["name"]]

        for f in filters:
            if "fields" not in f:
                continue
            for field in f["fields"]:
                if field["name"] in self.field_weight_mapping:
                    field["weight"] = self.field_weight_mapping[field["name"]]

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == FieldWeightMapping.name:
        return FieldWeightMapping(component_config)
    else:
        raise ValueError("Unsupported type field mapping component {}".
                         format(component_name))
