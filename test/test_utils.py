import json
import requests
import time
import os
import codecs

_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def load_json_file(file_name):
    rules = json.load(codecs.open(os.path.join(_location__,
                                               file_name),
                                  'r', 'utf-8'))
    return rules


def initialize_elasticsearch_with_config(es_config={'host': 'localhost',
                                        'port': 9200}):
    if "endpoints" in es_config:
        endpoints = es_config["endpoints"]
    else:
        host = es_config["host"]
        port = es_config["port"]
        endpoints = ["http://{}:{}".format(host, port)]
    requests.put('{}/dig-sandpaper-test'.format(endpoints[0]), data="{}")
    time.sleep(5)
    return endpoints

def initialize_elasticsearch_doc_types(documents_by_type, 
                                       es_config):
    endpoints = initialize_elasticsearch_with_config(es_config)
    for (t, docs) in documents_by_type.iteritems():
      initialize_elasticsearch_docs(endpoints, docs, t)

def initialize_elasticsearch_docs(endpoints, documents, t="ads"):
    for i, document in enumerate(documents):
        url = '{}/dig-sandpaper-test/{}/{}'.format(endpoints[0], t, i)
        requests.put(url,
                     data=json.dumps(document))
        time.sleep(5)

def initialize_elasticsearch(documents,
                             es_config):

    endpoints = initialize_elasticsearch_with_config(es_config)
    initialize_elasticsearch_docs(endpoints, documents)



def reset_elasticsearch(es_config={'host': 'localhost', 'port': 9200}):
    requests.delete('http://localhost:9200/dig-sandpaper-test')
    time.sleep(5)


def load_sub_configuration(coarse_or_fine,
                           component,
                           test_case_number,
                           file_suffix="_config.json"):
    return load_json_file("{}/{}/{}{}".format(coarse_or_fine,
                                              component,
                                              test_case_number,
                                              file_suffix))


def load_engine_configuration(test_case_number):
    config = {}
    coarse_config = {}
    coarse_config["preprocess"] = load_sub_configuration("coarse",
                                                         "preprocess",
                                                         test_case_number)
    coarse_config["parameterize"] = load_sub_configuration("coarse",
                                                           "parameterize",
                                                           test_case_number)
    coarse_config["generate"] = load_sub_configuration("coarse",
                                                       "generate",
                                                       test_case_number)
    generate_config_part_two = load_sub_configuration("coarse",
                                                      "generate",
                                                      test_case_number,
                                                      "_config_step_two.json")
    generate_components = coarse_config["generate"]["components"]
    generate_components.extend(generate_config_part_two["components"])

    coarse_config["execute"] = load_sub_configuration("coarse",
                                                      "execute",
                                                      test_case_number)
    config["coarse"] = coarse_config
    config["fine"] = {}
    return config
