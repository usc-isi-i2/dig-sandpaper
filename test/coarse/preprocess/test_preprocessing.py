import unittest
import json
import codecs
from digsandpaper.coarse.preprocess.preprocessor import Preprocessor
from digsandpaper.coarse.preprocess.constraint_expansion_factory import DictConstraintExpander
import os


_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    with codecs.open(os.path.join(_location__,
                                  file_name),
                     'r', 'utf-8') as json_file:
        rules = json.load(json_file)
        return rules


class TestCoarsePreprocessing(unittest.TestCase):

    def test_basic_coarse_preprocessing(self):
        config = load_json_file("1_config.json")
        query = load_json_file("1_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        self.assertEqual(result["SPARQL"]["where"]["clauses"][1]["constraint"],
                         "toronto, ontario")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][1]["isOptional"],
                         True)
        self.assertEqual(result["SPARQL"]["where"]["clauses"][1]["type"],
                         "Location")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][3]["type"],
                         "Title")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][4]["type"],
                         "HairColor")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][4]["constraint"],
                         "blonde")
        self.assertEqual(result["SPARQL"]["where"]["clauses"][5]["constraint"],
                         "straw")
        self.assertEqual(result["SPARQL"]["where"]["filters"][0]["type"],
                         "Title")
        self.assertNotIn("the", result["SPARQL"]["where"]["filters"][0]["constraint"].split(" ") )
        self.assertIn("mistress", result["SPARQL"]["where"]["filters"][0]["constraint"].split(" ") )

    def test_basic_coarse_preprocessing_with_compound_filter(self):
        config = load_json_file("2_config.json")
        query = load_json_file("2_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        f = result["SPARQL"]["where"]["filters"][0]
        self.assertEqual(f["clauses"][0]["type"],
                         "Title")
        self.assertEqual(f["clauses"][1]["type"],
                         "owl:Thing")

    def test_basic_coarse_preprocessing_with_no_type_mappings(self):
        config = load_json_file("3_config.json")
        query = load_json_file("3_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        f = result["SPARQL"]["where"]["filters"][0]
        self.assertEqual(f["clauses"][0]["type"],
                         "owl:Thing")

    def test_basic_coarse_preprocessing_with_date_filter(self):
        config = load_json_file("4_config.json")
        query = load_json_file("4_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        f = result["SPARQL"]["where"]["filters"][0]
        self.assertEqual(f["clauses"][0]["type"],
                         "PostingDate")

    def test_nested_filter_constraint_expansion(self):
        config = json.loads('''{
            "type": "ConstraintExpansion",
            "name": "DictConstraintExpander",
            "dict_constraint_mappings": "test/coarse/preprocess/1_dict_constraint_mappings.json"
        }''')
        expander = DictConstraintExpander(config)
        query = {"SPARQL": {"where": {"clauses": [],
                                      "filters":[
                                                 {"operator": "or", "clauses": [
                                                                                {"operator":"=", "constraint":"blonde", "variable":"?hair-color", "type": "HairColor"},
                                                                                {"operator":"=", "constraint":"brown", "variable":"?hair-color", "type": "HairColor"}]}]}}}
        result = expander.preprocess(query)
        f = result["SPARQL"]["where"]["filters"][0]
        self.assertEqual(f["clauses"][0]["operator"], "or")

    def test_sparql_unnesting(self):
        config = load_json_file("5_config.json")
        query = load_json_file("5_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        w = result["SPARQL"]["where"]
        self.assertEqual(w["type"], "Ad")
        self.assertEqual(w["clauses"][0]["type"], "Cluster")

    def test_group_by_typing(self):
        config = load_json_file("6_config.json")
        query = load_json_file("6_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        g = result["SPARQL"]["group-by"]
        self.assertEqual(g["variables"][0]["type"], "Ethnicity")

    def test_union_and_not_exists(self):
        config = load_json_file("7_config.json")
        query = load_json_file("7_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        c = result["SPARQL"]["where"]["clauses"]
        self.assertEqual(c[0]["clauses"][0]["type"], "Location")
        self.assertEqual(c[0]["clauses"][1]["type"], "Location")
        fs = result["SPARQL"]["where"]["filters"]
        self.assertEqual(fs[0]["clauses"][0]["type"], "PostingDate")
        self.assertEqual(fs[0]["clauses"][1]["clauses"][0]["type"], "Title")

    def test_network_expansion(self):
        config = load_json_file("8_config.json")
        query = load_json_file("8_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        w = result["SPARQL"]["where"]
        self.assertEqual(w["clauses"][0]["filters"][0]["type"], "City")

    def test_order_by(self):
        config = load_json_file("9_config.json")
        query = load_json_file("9_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        o = result["SPARQL"]["order-by"]
        self.assertEqual(o["values"][0]["type"], "PostingDate")


    def test_rank_scoring_coefficient(self):
        config = load_json_file("10_config.json")
        query = load_json_file("10_query.json")
        preprocessor = Preprocessor(config)

        result = preprocessor.preprocess(query)
        c = result["SPARQL"]["where"]["clauses"]
        self.assertEqual(c[0]["type"], "City")


if __name__ == '__main__':
    unittest.main()
