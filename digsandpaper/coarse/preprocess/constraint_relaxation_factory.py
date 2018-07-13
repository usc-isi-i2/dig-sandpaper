__name__ = "ConstraintRelaxation"
name = __name__


class CombinePredicatesConstraintRelaxer(object):

    name = "CombinePredicatesConstraintRelaxer"
    component_type = __name__

    def preprocess_filter(self, f):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                return ' '.join([self.preprocess_filter(c)
                                 for c in f["clauses"]]).strip()
            elif isinstance(f["clauses"], dict):
                return ' '.join(self.preprocess_filter(f["clauses"])).strip()
        else:
            return f.get("constraint", "")

    def preprocess_clauses(self, clause):
        constraint = clause.get("constraint", "")
        constraints = ""
        filter_constraints = ""
        if "clauses" in clause:
            constraints = ' '.join(self.preprocess_clauses(c)
                                   for c in clause["clauses"]).strip()

        if "filters" in clause:
            filters = clause["filters"]
            filter_constraints = ' '.join([self.preprocess_filter(f) for f in filters])
        return '{} {} {}'.format(constraint, constraints, filter_constraints)

    def preprocess(self, query):
        where = query["SPARQL"]["where"]

        constraints = self.preprocess_clauses(where)
        new_clause = {"constraint": constraints,
                      "isOptional": False,
                      "predicate": "text",
                      "type": "owl:Thing",
                      "id": "123"}

        where["clauses"] = list()
        where["clauses"].append(new_clause)
        where["filters"] = list()

        return query


class IsOptionalConstraintRelaxer(object):

    name = "IsOptionalConstraintRelaxer"
    component_type = __name__

    def preprocess_filter(self, f):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                f["clauses"] = [self.preprocess_filter(c)
                                for c in f["clauses"]]
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

    def preprocess_clauses(self, clause):
        if "clauses" in clause:
            sub_clauses = clause["clauses"]

            for sub_clause in sub_clauses:
                if "constraint" not in sub_clause:
                    if "clauses" in sub_clause:
                        self.preprocess_clauses(sub_clause)
                    continue
                if not sub_clause.get("isOptional", False):
                    sub_clause["isOptional"] = True

        if "filters" in clause:
            filters = clause["filters"]
            clause["filters"] = [self.preprocess_filter(f) for f in filters]

    def preprocess(self, query):
        where = query["SPARQL"]["where"]

        self.preprocess_clauses(where)

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == IsOptionalConstraintRelaxer.name:
        return IsOptionalConstraintRelaxer()
    if component_name == CombinePredicatesConstraintRelaxer.name:
        return CombinePredicatesConstraintRelaxer()
    else:
        raise ValueError("Unsupported constraint Relaxer {}".
                         format(component_name))
