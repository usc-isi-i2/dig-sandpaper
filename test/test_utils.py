import json
import requests
import time


def initialize_elasticsearch(documents):

    requests.put('http://localhost:9200/dig-sandpaper-test', data="{}")
    time.sleep(5)

    for i, document in enumerate(documents):
        url = 'http://localhost:9200/dig-sandpaper-test/ads/{}'.format(i)
        requests.put(url,
                     data=json.dumps(document))
        time.sleep(5)


def reset_elasticsearch():
    requests.delete('http://localhost:9200/dig-sandpaper-test')
    time.sleep(5)
