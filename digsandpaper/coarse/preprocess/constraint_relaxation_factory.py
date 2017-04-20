import json
import codecs
import copy
import uuid
from jsonpath_rw_ext import parse

__name__ = "ConstraintRelaxation"
name = __name__


class IsOptionalConstraintRelaxer(object):

    name = "IsOptionalConstraintRelaxer"
    component_type = __name__

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
            if not f.get("isOptional", False):
                f["isOptional"] = True
            return f

    def preprocess_clauses(self, where):
        where_clauses = where["clauses"]
        
        new_where_clauses = list()
        
        for clause in where_clauses:
            if "constraint" not in clause:
                if "clauses" in clause:
                    self.preprocess_clauses(clause)
                continue
            if not clause.get("isOptional", False):
                clause["isOptional"] = True

    def preprocess(self, query):
        where = query["SPARQL"]["where"]

        if "clauses" in where:
            self.preprocess_clauses(where)
        
        if "filters" in where:
            filters = where["filters"]
            where["filters"] = [self.preprocess_filter(f) for f in filters]

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == IsOptionalConstraintRelaxer.name:
        return IsOptionalConstraintRelaxer()
    else:
        raise ValueError("Unsupported constraint Relaxer {}".
                         format(component_name))
