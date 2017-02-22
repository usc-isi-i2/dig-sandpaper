import json
import codecs
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections

__name__ = "ExecuteQueryComponent"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class ExecuteElasticsearchQuery(object):

    name = "ExecuteElasticsearchQuery"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        if "endpoints" in self.config:
            self.endpoints = self.config["endpoints"]
        else:
            self.host = self.config["host"]
            self.port = self.config["port"]
            self.endpoints = ["{}:{}".format(self.host, self.port)]
        connections.create_connection(hosts=self.endpoints)

        return

    def execute(self, query):
        s = Search().from_dict(query["ELASTICSEARCH"]["search"])\
                    .index(query["ELASTICSEARCH"]["index"])\
                    .doc_type(query["ELASTICSEARCH"]["doc_type"])
        response = s.execute()
        return response


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ExecuteElasticsearchQuery.name:
        return ExecuteElasticsearchQuery(component_config)
    else:
        raise ValueError("Unsupported query execution component {}".
                         format(component_name))
