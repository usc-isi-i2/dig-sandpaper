from digsandpaper.sandpaper_utils import load_json_file

__name__ = "TypeFieldMapping"
name = __name__


class TypeFieldGroupByMapping(object):
    name = "TypeFieldGroupByMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_field_mappings"]
        if isinstance(file, dict):
            self.type_field_mapping = file
        else:
            self.type_field_mapping = load_json_file(file)

    def generate_where(self, where, is_root):
        where_clauses = where["clauses"]

        for clause in where_clauses:
            if "clauses" in clause:
                self.generate_where(clause, False)
            else:
                if not is_root and "constraint" not in clause:
                    clause["agg_fields"] = []
                    if "type" in clause:
                        t = clause["type"]
                        if t in self.type_field_mapping:
                            fields_array_or_str = self.type_field_mapping[t]
                            if isinstance(fields_array_or_str, str):
                                clause["agg_fields"].append({"name": fields_array_or_str})
                            else:
                                for field in fields_array_or_str:
                                    clause["agg_fields"].append({"name": field})

    def add_fields(self, c):
        t = c["type"]
        if t in self.type_field_mapping:
            c["fields"] = []
            tfm = self.type_field_mapping[t]
            if isinstance(tfm, str):
                c["fields"].append({"name": tfm})
            else:
                for field in tfm:
                    c["fields"].append({"name": field})

    def generate(self, query):
        select = query["SPARQL"]["select"]
        groupby = query["SPARQL"]["group-by"]
        if query["type"].lower() == "aggregation":

            if "variables" in groupby:
                for v in groupby["variables"]:
                    self.add_fields(v)

            for s in select["variables"]:
                self.add_fields(s)

        if "order-by" in query["SPARQL"]:
            orderby = query["SPARQL"]["order-by"]
            if "values" in orderby:
                for v in orderby["values"]:
                    self.add_fields(v)

        where = query["SPARQL"]["where"]
        self.generate_where(where, True)
        return query


class TypeFieldMapping(object):

    name = "TypeFieldMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_field_mappings"]
        if isinstance(file, dict):
            self.type_field_mapping = file
        else:
            self.type_field_mapping = load_json_file(file)

    def add_types_to_filters(self, f):
        if "type" in f:
            t = f["type"]
            if t in self.type_field_mapping:
                f["fields"] = []
                for field in self.type_field_mapping[t]:
                    f["fields"].append({"name": field})
        if "clauses" in f:
            for clause in f["clauses"]:
                self.add_types_to_filters(clause)

    def generate_where(self, where):
        where_clauses = where["clauses"]

        if "type" in where:
            t = where["type"]
            if t in self.type_field_mapping:
                where["fields"] = []
                for field in self.type_field_mapping[t]:
                        where["fields"].append({"name": field})

        for clause in where_clauses:
            if "clauses" in clause:
                self.generate_where(clause)
            else:
                clause["fields"] = []
                if "type" in clause:
                    t = clause["type"]
                    if t in self.type_field_mapping:
                        for field in self.type_field_mapping[t]:
                            clause["fields"].append({"name": field})

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
    if component_name == TypeFieldMapping.name:
        return TypeFieldMapping(component_config)
    elif component_name == TypeFieldGroupByMapping.name:
        return TypeFieldGroupByMapping(component_config)
    else:
        raise ValueError("Unsupported type field mapping component {}".
                         format(component_name))
