__name__ = "ConstraintRelaxation"
name = __name__


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
    else:
        raise ValueError("Unsupported constraint Relaxer {}".
                         format(component_name))
