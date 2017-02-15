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

    def test_coarse(self):
        config = load_engine_configuration(1)
        engine = Engine(config, "localhost", 9200)
        query = load_sub_configuration("coarse", "preprocess",
                                       1, "_query.json")
        document = load_sub_configuration("coarse", "execute",
                                          1, "_document.json")
        test_utils.initialize_elasticsearch([document])
        search_server.set_engine(engine)
        response = self.app.post('/search/coarse', data=json.dumps(query))
        self.assertEquals(200, response.status_code)
        results = json.loads(response.data)
        self.assertEquals(len(results), 2)
        test_utils.reset_elasticsearch()


if __name__ == '__main__':
    unittest.main()
