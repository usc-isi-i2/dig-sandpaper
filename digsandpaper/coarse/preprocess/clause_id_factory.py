import uuid

__name__ = "ClauseIdMapper"
name = __name__


class UUIDClauseIdMapper(object):

    name = "UUIDClauseIdMapper"
    component_type = __name__

    def preprocess_filter(self, f):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                for c in f["clauses"]:
                    self.preprocess_filter(c)
            elif isinstance(f["clauses"], dict):
                self.preprocess_filter(f["clauses"])
        else:
            f["_id"] = uuid.uuid4().hex

    def preprocess(self, query):
        where = query["SPARQL"]["where"]
        clauses = where.get("clauses", [])
        filters = where.get("filters", [])
        for clause in clauses:
            clause["_id"] = uuid.uuid4().hex
            if "clauses" in clause:
                for c in clause["clauses"]:
                    c["_id"] = uuid.uuid4().hex
                for f in clause.get("filters", []):
                    self.preprocess_filter(f)
        for f in filters:
            self.preprocess_filter(f)
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == UUIDClauseIdMapper.name:
        return UUIDClauseIdMapper()
    else:
        raise ValueError("Unsupported clause id mapper {}".
                         format(component_name))
