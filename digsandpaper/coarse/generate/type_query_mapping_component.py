from digsandpaper.sandpaper_utils import load_json_file

__name__ = "TypeQueryMapping"
name = __name__


class TypeQueryMapping(object):

    name = "TypeQueryMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_query_mappings"]
        if isinstance(file, dict):
            self.type_query_mapping = file
        else:
            self.type_query_mapping = load_json_file(file)

    def add_types_to_filters(self, f):
        if "type" in f:
            t = f["type"]
            if t in self.type_query_mapping:
                f["query_type"] = self.type_query_mapping[t]
        if "clauses" in f:
            for clause in f["clauses"]:
                self.add_types_to_filters(clause)

    def generate_where(self, where):
        where_clauses = where["clauses"]

        if "type" in where:
            t = where["type"]
            if t in self.type_query_mapping:
                where["query_type"] = self.type_query_mapping[t]

        for clause in where_clauses:
            if "type" not in clause:
                continue
            t = clause["type"]
            
            if "clauses" in clause:
                self.generate_where(clause)
            if t in self.type_query_mapping:
                clause["query_type"] = self.type_query_mapping[t]

        if "filters" in where:
            filters = where["filters"]
            for f in filters:
                self.add_types_to_filters(f)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        self.generate_where(where)        
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == TypeQueryMapping.name:
        return TypeQueryMapping(component_config)
    else:
        raise ValueError("Unsupported type query mapping component {}".
                         format(component_name))
