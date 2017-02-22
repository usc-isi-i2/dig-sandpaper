import json
import requests
import time


def initialize_elasticsearch(documents,
                             es_config={'host': 'localhost',
                                        'port': 9200}):

    if "endpoints" in es_config:
        endpoints = es_config["endpoints"]
    else:
        host = es_config["host"]
        port = es_config["port"]
        endpoints = ["http://{}:{}".format(host, port)]
    requests.put('{}/dig-sandpaper-test'.format(endpoints[0]), data="{}")
    time.sleep(5)

    for i, document in enumerate(documents):
        url = '{}/dig-sandpaper-test/ads/{}'.format(endpoints[0], i)
        requests.put(url,
                     data=json.dumps(document))
        time.sleep(5)


def reset_elasticsearch(es_config={'host': 'localhost', 'port': 9200}):
    requests.delete('http://localhost:9200/dig-sandpaper-test')
    time.sleep(5)
