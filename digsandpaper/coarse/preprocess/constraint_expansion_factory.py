import json
import codecs
import copy
from jsonpath_rw_ext import parse

__name__ = "ConstraintExpansion"
name = __name__

def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class IdentityConstraintExpander(object):

    name = "IdentityConstraintExpander"
    component_type = __name__

    def preprocess(self, query):
        return query


class DictConstraintExpander(object):

    name = "DictConstraintExpander"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["dict_constraint_mappings"]
        self.dict_constraint_mappings = load_json_file(file)

    def preprocess(self, query):
        where = query["SPARQL"]["where"]
        where_clauses = where["clauses"]
        filters = where["filters"]
        new_where_clauses = list()
        new_filters = list()

        for clause in where_clauses:
            if "constraint" not in clause:
                continue
            expanded_values = self.dict_constraint_mappings.get(
                clause["type"], {}).get(clause["constraint"], [])
            for expanded_value in expanded_values:
                new_clause = copy.copy(clause)
                new_clause["constraint"] = expanded_value
                new_clause["isOptional"] = True
                new_where_clauses.append(new_clause)

        for f in filters:
            if "constraint" not in f or "type" not in f:
                continue
            expanded_values = self.dict_constraint_mappings.get(
                f["type"], {}).get(f["constraint"], [])
            for expanded_value in expanded_values:
                new_filter = copy.copy(f)
                new_filter["constraint"] = expanded_value
                new_filter["isOptional"] = True
                new_filters.append(new_filter)

        where_clauses.extend(new_where_clauses)
        filters.extend(new_filters)

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == IdentityConstraintExpander.name:
        return IdentityConstraintExpander()
    elif component_name == DictConstraintExpander.name:
        return DictConstraintExpander(component_config)
    else:
        raise ValueError("Unsupported constraint expansion {}".
                         format(component_name))
