import json
import codecs

__name__ = "TypeDocTypeMapping"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class TypeDocTypeMapping(object):

    name = "TypeDocTypeMapping"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["type_doc_type_mappings"]
        self.type_doc_type_mappings = load_json_file(file)

    def generate(self, query):
        where = query["SPARQL"]["where"]
        t = where["type"]

        if t in self.type_doc_type_mappings:
            if "ELASTICSEARCH" not in query:
                query["ELASTICSEARCH"] = {}
            if isinstance(query["ELASTICSEARCH"], dict):
                query["ELASTICSEARCH"]["doc_type"] = self.type_doc_type_mappings[t]
            elif isinstance(query["ELASTICSEARCH"], list):
                for es in query["ELASTICSEARCH"]:
                    es["doc_type"] = self.type_doc_type_mappings[es["type"]]
        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == TypeDocTypeMapping.name:
        return TypeDocTypeMapping(component_config)
    else:
        raise ValueError("Unsupported type doc type mapping component {}".
                         format(component_name))
