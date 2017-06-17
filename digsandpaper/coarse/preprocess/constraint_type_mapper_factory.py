import json
import codecs
from jsonpath_rw_ext import parse

__name__ = "ConstraintTypeMapper"
name = __name__

clause_jsonpath = parse("clauses[*]")


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class TopConstraintTypeMapper(object):

    name = "TopConstraintTypeMapper"
    component_type = __name__

    def preprocess(self, query):
        for clause in clause_jsonpath.find(query):
            clause["type"] = "owl:Thing"
        return query


class PredicateDictConstraintTypeMapper(object):

    name = "PredicateDictConstraintTypeMapper"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        predicate_range_file = self.config["predicate_range_mappings"]
        if isinstance(predicate_range_file, dict):
            self.predicate_range_mappings = predicate_range_file
        else:
            self.predicate_range_mappings = load_json_file(predicate_range_file)

    def preprocess_filter(self, f, clause_variable_to_type):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                for c in f["clauses"]:
                    self.preprocess_filter(c,
                                           clause_variable_to_type)
            elif isinstance(f["clauses"], dict):
                self.preprocess_filter(f["clauses"])
        else:
            f["type"] = clause_variable_to_type.get(f["variable"],
                                                    "owl:Thing")

    def preprocess(self, query):
        clause_variable_to_type = {}
        for match in clause_jsonpath.find(query["SPARQL"]["where"]):
            clause = match.value
            clause["type"] = self.predicate_range_mappings.get(
                clause["predicate"], "owl:Thing")
            if "variable" in clause:
                clause_variable_to_type[clause["variable"]] = clause["type"]

        if "filters" in query["SPARQL"]["where"]:
            for f in query["SPARQL"]["where"]["filters"]:
                self.preprocess_filter(f, clause_variable_to_type)

        for s in query["SPARQL"]["select"]["variables"]:
            s["type"] = clause_variable_to_type.get(s["variable"], "owl:Thing")

        if "group-by" in query["SPARQL"]:
            if "variables" in query["SPARQL"]["group-by"]:
                for v in query["SPARQL"]["group-by"]["variables"]:
                    v["type"] = clause_variable_to_type.get(v["variable"], "owl:Thing")

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == TopConstraintTypeMapper.name:
        return TopConstraintTypeMapper()
    elif component_name == PredicateDictConstraintTypeMapper.name:
        return PredicateDictConstraintTypeMapper(component_config)
    else:
        raise ValueError("Unsupported constraint type mapper {}".
                         format(component_name))
