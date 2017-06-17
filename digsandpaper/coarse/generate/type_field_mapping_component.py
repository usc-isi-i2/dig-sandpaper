import json
import codecs

__name__ = "TypeFieldMapping"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules

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

    def generate(self, query):
        select = query["SPARQL"]["select"]
        groupby = query["SPARQL"]["group-by"]
        if query["type"].lower() == "aggregation":

            if "variables" in groupby:
                for v in groupby["variables"]:
                    t = v["type"]
                    if t in self.type_field_mapping:
                        v["fields"] = []
                        for field in self.type_field_mapping[t]:
                            v["fields"].append({"name": field})

            for s in select["variables"]:
                t = s["type"]
                if t in self.type_field_mapping:
                    s["fields"] = []
                    for field in self.type_field_mapping[t]:
                        s["fields"].append({"name": field})                

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
            if "type" not in clause:
                continue
            t = clause["type"]
            if t in self.type_field_mapping:
                if "clauses" in clause:
                    self.generate_where(clause)
                else:
                    clause["fields"] = []
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
