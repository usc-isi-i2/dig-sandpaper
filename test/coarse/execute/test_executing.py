import unittest
import json
import codecs
from digsandpaper.coarse.execute.executor import Executor
import os
import test.test_utils

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

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEquals(len(result.hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])

    def test_basic_coarse_executing_compound_filters(self):
        config = load_json_file("2_config.json")
        queries = load_json_file("2_query.json")
        document = load_json_file("2_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEquals(len(result.hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])

    def test_basic_coarse_executing_compound_filters_no_type_mapping(self):
        config = load_json_file("3_config.json")
        queries = load_json_file("3_query.json")
        document = load_json_file("3_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEquals(len(result.hits), 1)
            self.assertIn("fields", result.hits[0])
            self.assertIn("posting-date", result.hits[0]["fields"])
            self.assertEquals("2015-03-01T14:02:00",
                              result.hits[0]["fields"]["posting-date"]["strict"]["name"])

        test.test_utils.reset_elasticsearch(config["components"][0])

    def test_basic_coarse_executing_date_filters(self):
        config = load_json_file("4_config.json")
        queries = load_json_file("4_query.json")
        document = load_json_file("4_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEquals(len(result.hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])


if __name__ == '__main__':
    unittest.main()
