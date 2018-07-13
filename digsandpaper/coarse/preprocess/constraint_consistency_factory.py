from digsandpaper.sandpaper_utils import load_json_file
from types import ModuleType


__name__ = "ConstraintConsistency"
name = __name__


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
        if isinstance(file, dict):
            self.constraint_type_transformations_to_compile = file
        else:
            self.constraint_type_transformations_to_compile = load_json_file(file)
        self.constraint_type_transformations = {}
        self.constraint_type_transformations["owl:Thing"] = compile("value",
                                                                    filename,
                                                                    'eval')
        for key, value in self.constraint_type_transformations_to_compile.items():
            compiled_transformation = compile(value, filename, 'eval')
            self.constraint_type_transformations[key] = compiled_transformation

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
            compiled_transformation = self.constraint_type_transformations.get(
                f.get("type", "owl:Thing"),
                self.constraint_type_transformations.get("owl:Thing"))
            data = {}
            data["value"] = f["constraint"]
            f["constraint"] = eval(
                compiled_transformation, self.module.__dict__, data)
            return f

    def preprocess_clause(self, clause):
        if "constraint" not in clause:
            if "clauses" in clause:
                for c in clause["clauses"]:
                    self.preprocess_clause(c)

        if "constraint" in clause:
            compiled_transformation = self.constraint_type_transformations.get(
                clause.get("type", "owl:Thing"),
                self.constraint_type_transformations.get("owl:Thing"))
            data = {}
            data["value"] = clause["constraint"]
            clause["constraint"] = eval(
                compiled_transformation, self.module.__dict__, data)

        if "filters" in clause:
            filters = clause["filters"]
            clause["filters"] = [self.preprocess_filter(f)
                                 for f in filters]

    def preprocess(self, query):
        where = query["SPARQL"]["where"]
        self.preprocess_clause(where)
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
