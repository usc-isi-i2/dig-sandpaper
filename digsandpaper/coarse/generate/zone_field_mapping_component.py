import json
import codecs

__name__ = "ZoneFieldMapping"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class ZoneFieldMapping(object):

    name = "ZoneFieldMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["zone_field_mappings"]
        self.zone_field_mapping = load_json_file(file)

    def in_zones(self, zones, field):
        for zone in zones:
            if field in self.zone_field_mapping[str(zone)]:
                return True
        return False

    def generate_clauses(self, where, zones):
        where_clauses = where["clauses"]
        for clause in where_clauses:
            if "clauses" in clause:
                self.generate_clauses(clause, zones)
            if "fields" in clause:
                clause["fields"] = [field for field in clause["fields"]
                                    if self.in_zones(zones, field["name"])]

    def generate_filter(self, f, zones):
        if "fields" in f:
            f["fields"] = [field for field in f["fields"]
                           if self.in_zones(zones, field["name"])]
        elif "clauses" in f:
            for clause in f["clauses"]:
                self.generate_filter(clause, zones)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        
        zones = query["zone"]

        self.generate_clauses(where, zones)

        if "filters" in where:
            filters = where["filters"]    
            for f in filters:
                self.generate_filter(f, zones)

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ZoneFieldMapping.name:
        return ZoneFieldMapping(component_config)
    else:
        raise ValueError("Unsupported type field mapping component {}".
                         format(component_name))
