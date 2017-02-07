import unittest
import json
import codecs
from digsandpaper.coarse.preprocess.preprocessor import Preprocessor
import os


_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    rules = json.load(codecs.open(os.path.join(_location__, file_name),
                                  'r', 'utf-8'))
    return rules


class TestCoarsePreprocessing(unittest.TestCase):

    def test_basic_coarse_preprocessing(self):
        config = load_json_file("1_config.json")
        query = load_json_file("1_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        self.assertEqual(result["SPARQL"]["where"]["clauses"][1]["constraint"],
                         "toronto, ontario")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][1]["type"],
                         "Location")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][4]["type"],
                         "HairColor")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][4]["constraint"],
                         "blonde")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][5]["constraint"],
                         "straw")


if __name__ == '__main__':
    unittest.main()
