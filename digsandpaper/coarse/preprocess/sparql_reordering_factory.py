import json
import codecs
from jsonpath_rw_ext import parse
import compiler
from types import ModuleType


__name__ = "SparqlReordering"
name = __name__



def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules

class SparqlRootUnnesting(object):

    name = "SparqlRootUnnesting"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["root_info"]
        self.root_info = load_json_file(file)
        self.root_type = self.root_info["root_type"] # "ad"
        self.root_predicates = self.root_info["root_predicates"] # [price, name, blah]
        self.inverse_predicates = self.root_info["inverse_predicates"] # {cluster: ad}
        return

    def preprocess_clause(self, clause):
        if "constraint" not in clause:
            if "clauses" in clause:
                for c in clause["clauses"]:
                    self.preprocess_clause(c)
            return
        return
     

    def preprocess(self, query):
        where = query["SPARQL"]["where"]
        t = where["type"]
        if where["type"] == self.root_type:
            return query
        if not where["type"] in self.inverse_predicates:
            return query
        clauses = where["clauses"]
        new_where = None
        sub_where = None
        for clause in clauses:
            if clause["predicate"] in self.inverse_predicates[t]:
                new_where = {"type": self.root_type, 
                             "variable": clause["variable"], 
                             "clauses": [],
                             "_id": clause["_id"]}                
                sub_where = {"type": where["type"], 
                             "variable": where["variable"],
                             "clauses": [],
                             "_id": clause["_id"]}
                new_where["clauses"].append(sub_where)

        if new_where:
            for clause in clauses:
                predicate = clause["predicate"]
                if predicate in self.root_predicates:
                    new_where["clauses"].append(clause)
                else:
                    sub_where["clauses"].append(clause)
            query["SPARQL"]["where"] = new_where

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == SparqlRootUnnesting.name:
        return SparqlRootUnnesting(component_config)
    else:
        raise ValueError("Unsupported sparql reordering component {}".
                         format(component_name))
