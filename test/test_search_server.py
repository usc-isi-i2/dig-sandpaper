from digsandpaper import search_server
import unittest
import os
import json
import codecs
from digsandpaper.engine import Engine
import test_utils

_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    rules = json.load(codecs.open(os.path.join(_location__,
                                               file_name),
                                  'r', 'utf-8'))
    return rules


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


class SearchServerTestCase(unittest.TestCase):

    def setUp(self):
        search_server.app.config['TESTING'] = True
        self.app = search_server.app.test_client()

    def test_hello(self):
        response = self.app.get('/')
        self.assertEquals(200, response.status_code)

    def helper_test_coarse(self, i):
        config = load_engine_configuration(i)
        engine = Engine(config)
        query = load_sub_configuration("coarse", "preprocess",
                                       i, "_query.json")
        document = load_sub_configuration("coarse", "execute",
                                          i, "_document.json")
        es_config = config["coarse"]["execute"]["components"][0]
        test_utils.initialize_elasticsearch([document], es_config)
        search_server.set_engine(engine)
        response = self.app.post('/search/coarse', data=json.dumps(query))
        self.assertEquals(200, response.status_code)
        results = json.loads(response.data)
        test_utils.reset_elasticsearch(es_config)
        return results
        self.assertEquals(len(results), 2)

    def test_coarse_1(self):
        results_1 = self.helper_test_coarse(1)
        self.assertEquals(len(results_1), 2)
        self.assertEquals(len(results_1[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_2(self):
        results_2 = self.helper_test_coarse(2)
        self.assertEquals(len(results_2), 1)
        self.assertEquals(len(results_2[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_3(self):
        results_3 = self.helper_test_coarse(3)
        self.assertEquals(len(results_3), 1)
        self.assertEquals(len(results_3[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_4(self):
        results_4 = self.helper_test_coarse(4)
        self.assertEquals(len(results_4), 1)
        self.assertEquals(len(results_4[0]["result"]["hits"]["hits"]), 1)


if __name__ == '__main__':
    unittest.main()
