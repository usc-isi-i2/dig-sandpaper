from digsandpaper.sandpaper_utils import load_json_file

__name__ = "TypeIndexMapping"
name = __name__


class TypeIndexMapping(object):

    name = "TypeIndexMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_index_mappings"]
        if isinstance(file, dict):
            self.type_index_mappings = file
        else:
            self.type_index_mappings = load_json_file(file)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        t = where["type"]
        if t in self.type_index_mappings:
            if "ELASTICSEARCH" not in query:
                query["ELASTICSEARCH"] = {}
            if isinstance(query["ELASTICSEARCH"], dict):
                query["ELASTICSEARCH"]["index"] = self.type_index_mappings[t]
            elif isinstance(query["ELASTICSEARCH"], list):
                for es in query["ELASTICSEARCH"]:
                    es["index"] = self.type_index_mappings[es["type"]]
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == TypeIndexMapping.name:
        return TypeIndexMapping(component_config)
    else:
        raise ValueError("Unsupported type index mapping component {}".
                         format(component_name))
