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

    def preprocess_filter(self, f):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                f["clauses"] = [self.preprocess_filter(c) for c in f["clauses"]]
                return f
            elif isinstance(f["clauses"], dict):
                f["clauses"] = self.preprocess_filter(f["clauses"])
                return f
        else:
            if "constraint" not in f or "type" not in f:
                return f
            new_filters = []
            expanded_values = self.dict_constraint_mappings.get(
                f["type"], {}).get(f["constraint"], [])
            for expanded_value in expanded_values:
                new_filter = copy.copy(f)
                new_filter["constraint"] = expanded_value
                new_filter["isOptional"] = True
                new_filters.append(new_filter)
            if len(new_filters) > 0:
                new_filters.append(f)
                return {"operator": "or", "clauses": new_filters}
            else:
                return f

    def preprocess(self, query):
        where = query["SPARQL"]["where"]


        if "clauses" in where:
            where_clauses = where["clauses"]
            
            new_where_clauses = list()
            
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
            where_clauses.extend(new_where_clauses)
        
        if "filters" in where:
            filters = where["filters"]
            where["filters"] = [self.preprocess_filter(f) for f in filters]

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
