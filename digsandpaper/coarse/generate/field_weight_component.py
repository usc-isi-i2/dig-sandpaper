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
        if isinstance(file, dict):
            self.field_weight_mapping = file
        else:
            self.field_weight_mapping = load_json_file(file)

    def find_weight(self, field_path, nested_field_weight_mapping):
        if not isinstance(field_path, list) or len(field_path) == 0:
            return None
        if field_path[0] in nested_field_weight_mapping:
            next = nested_field_weight_mapping[field_path[0]]
            if isinstance(next, dict):
                return self.find_weight(field_path[1:], next)
            return next
        elif "*" in nested_field_weight_mapping:
            next = nested_field_weight_mapping["*"]
            if isinstance(next, dict):
                return self.find_weight(field_path[1:], next)
            return next
        else:
            return None

    def find_weight_for_filter(self, f):
        if "fields" not in f:
            if "clauses" in f:
                for clause in f["clauses"]:
                    self.find_weight_for_filter(clause)
        else:
            for field in f["fields"]:
                weight = self.find_weight(field["name"].split("."), self.field_weight_mapping)
                if weight:
                    field["weight"] = weight

    def generate_where(self, where):
        where_clauses = where["clauses"]
        

        for clause in where_clauses:
            if "fields" not in clause:
                continue
            if "clauses" in clause:
                self.generate_where(clause)
            else:
                for field in clause["fields"]:
                    weight = self.find_weight(field["name"].split("."), self.field_weight_mapping)
                    if weight:
                        field["weight"] = weight
        if "filters" in where:
            filters = where["filters"]
            for f in filters:
                self.find_weight_for_filter(f)

        return where

    def generate(self, query):
        where = query["SPARQL"]["where"]
        self.generate_where(where)
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == FieldWeightMapping.name:
        return FieldWeightMapping(component_config)
    else:
        raise ValueError("Unsupported type field mapping component {}".
                         format(component_name))
