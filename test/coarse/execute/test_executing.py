import unittest
import json
import codecs
import requests
from digsandpaper.coarse.execute.executor import Executor
import os


_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    rules = json.load(codecs.open(os.path.join(_location__, file_name),
                                  'r', 'utf-8'))
    return rules


class TestCoarseExecuting(unittest.TestCase):

    def test_basic_coarse_executing(self):
        config = load_json_file("1_config.json")
        queries = load_json_file("1_query.json")
        document = load_json_file("1_document.json")

        r = requests.put('http://localhost:9200/dig-sandpaper-test', data="{}")


        r = requests.put('http://localhost:9200/dig-sandpaper-test/ads/1',
                         data=json.dumps(document))

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)

        r = requests.delete('http://localhost:9200/dig-sandpaper-test')



if __name__ == '__main__':
    unittest.main()
