import json
import codecs
from jsonpath_rw_ext import parse
import compiler
from types import ModuleType


__name__ = "ConstraintConsistency"
name = __name__

clause_jsonpath = parse("filters[*]|clauses[*]")


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class IdentityConstraintConsistency(object):

    name = "IdentityConstraintConsistency"
    component_type = __name__

    def preprocess(self, query):
        return query


class ConstraintTypeTransformations(object):

    name = "ConstraintTypeTransformations"
    component_type = __name__
    module = ModuleType("__constraint_type_transformations")

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        filename = "__constraint_type_transformations"
        file = self.config["constraint_type_transformations"]
        self.constraint_type_transformations_to_compile = load_json_file(file)
        self.constraint_type_transformations = {}
        self.constraint_type_transformations["owl:Thing"] = compiler\
            .compile("value",
                     filename,
                     'eval')
        for key, value in self.constraint_type_transformations_to_compile.iteritems():
            compiled_transformation = compiler.compile(
                value, filename, 'eval')
            self.constraint_type_transformations[key] = compiled_transformation

    def preprocess_clause(self, clause):
        if "constraint" not in clause:
            if "clauses" in clause:
                for c in clause["clauses"]:
                    self.preprocess_clause(c)
            return

        compiled_transformation = self.constraint_type_transformations.get(
            clause.get("type", "owl:Thing"), 
            self.constraint_type_transformations.get("owl:Thing"))
        data = {}
        data["value"] = clause["constraint"]
        clause["constraint"] = eval(
            compiled_transformation, self.module.__dict__, data)                

    def preprocess(self, query):
        for clause in clause_jsonpath.find(query["SPARQL"]["where"]):
            self.preprocess_clause(clause.value)

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == IdentityConstraintConsistency.name:
        return IdentityConstraintConsistency()
    elif component_name == ConstraintTypeTransformations.name:
        return ConstraintTypeTransformations(component_config)
    else:
        raise ValueError("Unsupported constraint consistency component {}".
                         format(component_name))
