from digsandpaper.sandpaper_utils import load_json_file

__name__ = "ConstraintTypeMapper"
name = __name__


class PredicateDictConstraintTypeMapper(object):

    name = "PredicateDictConstraintTypeMapper"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        predicate_range_file = self.config.get("predicate_range_mappings", None)
        if isinstance(predicate_range_file, dict):
            self.predicate_range_mappings = predicate_range_file
        elif predicate_range_file:
            self.predicate_range_mappings = load_json_file(predicate_range_file)
        else:
            self.predicate_range_mappings = {}

    def preprocess_filter(self, f, clause_variable_to_type):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                for c in f["clauses"]:
                    self.preprocess_filter(c,
                                           clause_variable_to_type)
            elif isinstance(f["clauses"], dict):
                self.preprocess_filter(f["clauses"])
        if "filters" in f:
            f["filters"] = [self.preprocess_filter(sub_f, clause_variable_to_type)
                            for sub_f in f["filters"]]

        if "predicate" in f:
            f["type"] = self.predicate_range_mappings.get(f["predicate"],
                                                          "owl:Thing")
        elif "variable" in f:
            f["type"] = clause_variable_to_type.get(f["variable"],
                                                    "owl:Thing")
        return f

    def preprocess_clause(self, clause, clause_variable_to_type):
        if "clauses" in clause:
            if "type" in clause:
                clause_variable_to_type[clause["variable"]] = clause["type"]
            for c in clause["clauses"]:
                self.preprocess_clause(c, clause_variable_to_type)
        else:
            t = self.predicate_range_mappings.get(clause["predicate"],
                                                  "owl:Thing")
            clause["type"] = t
            if "variable" in clause:
                clause_variable_to_type[clause["variable"]] = clause["type"]

    def preprocess(self, query):
        clause_variable_to_type = {}
        where = query["SPARQL"]["where"]
        self.preprocess_clause(where, clause_variable_to_type)

        self.preprocess_filter(where, clause_variable_to_type)

        for s in query["SPARQL"]["select"]["variables"]:
            s["type"] = clause_variable_to_type.get(s["variable"], "owl:Thing")

        if "group-by" in query["SPARQL"]:
            if "variables" in query["SPARQL"]["group-by"]:
                for v in query["SPARQL"]["group-by"]["variables"]:
                    v["type"] = clause_variable_to_type.get(v["variable"],
                                                            "owl:Thing")

        if "order-by" in query["SPARQL"]:
            if "values" in query["SPARQL"]["order-by"]:
                for v in query["SPARQL"]["order-by"]["values"]:
                    v["type"] = clause_variable_to_type.get(v["variable"],
                                                            "owl:Thing")
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == PredicateDictConstraintTypeMapper.name:
        return PredicateDictConstraintTypeMapper(component_config)
    else:
        raise ValueError("Unsupported constraint type mapper {}".
                         format(component_name))
