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
        self.predicate_range_mappings = load_json_file(predicate_range_file)

    def preprocess(self, query):
        for match in clause_jsonpath.find(query["SPARQL"]["where"]):
            clause = match.value
            clause["type"] = self.predicate_range_mappings.get(
                clause["predicate"], "owl:Thing")
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
