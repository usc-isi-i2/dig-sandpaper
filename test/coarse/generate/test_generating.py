import unittest
import json
import codecs
from digsandpaper.coarse.generate.generator import Generator
import os


_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    rules = json.load(codecs.open(os.path.join(_location__, file_name),
                                  'r', 'utf-8'))
    return rules


class TestCoarseGenerating(unittest.TestCase):

    def test_basic_coarse_generating(self):
        config = load_json_file("1_config.json")
        parameterized_queries = load_json_file("1_query.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        where0 = generated_queries[0]["SPARQL"]["where"]
        where1 = generated_queries[1]["SPARQL"]["where"]
        self.assertEqual(len(generated_queries), 2)
        self.assertEqual(where0["clauses"][1]["fields"][0]["name"],
                         "extractors.content_strict.data_extractors.city.result.value")
        self.assertEqual(where0["clauses"][1]["fields"][0]["weight"],
                         4)
        self.assertEqual(where1["clauses"][1]["fields"][1]["name"],
                         "extractors.content_relaxed.data_extractors.city.result.value")
        self.assertEquals(where1["clauses"][1]["fields"][1]["weight"], 0.5)
        self.assertNotIn("weight", where0["clauses"][0]["fields"][1])
        self.assertEqual(where0["clauses"][3]["query_type"], "match_phrase")
        self.assertEqual(where0["filters"][0]["query_type"], "match_phrase")

    def test_basic_coarse_generating_elasticsearch_compiler(self):
        config = load_json_file("1_config_step_two.json")
        parameterized_queries = load_json_file("1_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 2)
        self.assertIn("ELASTICSEARCH", generated_queries[0])
        self.assertIn("search", generated_queries[0]["ELASTICSEARCH"])
        self.assertIn("query", generated_queries[0]["ELASTICSEARCH"]["search"])
        self.assertEqual(generated_queries[0]["ELASTICSEARCH"]["search"]["size"], 500)
        self.assertEqual(generated_queries[0]["ELASTICSEARCH"]["search"]["from"], 0)
        self.assertIn("highlight", generated_queries[0]["ELASTICSEARCH"]["search"])
        self.assertIn("extractors.content_strict.data_extractors.phone.result.value", generated_queries[0]["ELASTICSEARCH"]["search"]["highlight"]["fields"])

    def test_basic_coarse_generating_compound_filter(self):
        config = load_json_file("2_config.json")
        parameterized_queries = load_json_file("2_query.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_generating_elasticsearch_compiler_compound_filter(self):
        config = load_json_file("2_config_step_two.json")
        parameterized_queries = load_json_file("2_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_generating_no_type_mapping(self):
        config = load_json_file("3_config.json")
        parameterized_queries = load_json_file("3_query.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_generating_elasticsearch_compiler_no_type_mapping(self):
        config = load_json_file("3_config_step_two.json")
        parameterized_queries = load_json_file("3_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)
        gq = generated_queries[0]
        self.assertIn("url",
                      gq["ELASTICSEARCH"]["search"]["_source"]["includes"])

    def test_basic_coarse_generating_date_filters(self):
        config = load_json_file("4_config.json")
        parameterized_queries = load_json_file("4_query.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_generating_elasticsearch_compiler_date_filters(self):
        config = load_json_file("4_config_step_two.json")
        parameterized_queries = load_json_file("4_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_sparql_root_unnesting(self):
        config = load_json_file("5_config.json")
        parameterized_queries = load_json_file("5_query.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_sparql_root_unnesting_compiler(self):
        config = load_json_file("5_config_step_two.json")
        parameterized_queries = load_json_file("5_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)


    def test_basic_aggregation(self):
        config = load_json_file("6_config.json")
        parameterized_queries = load_json_file("6_query.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)

    def test_basic_coarse_aggregation_step_two(self):
        config = load_json_file("6_config_step_two.json")
        parameterized_queries = load_json_file("6_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 1)
        self.assertIn("aggs", generated_queries[0]["ELASTICSEARCH"]["search"])
        self.assertIn("?ethnicity", generated_queries[0]["ELASTICSEARCH"]["search"]["aggs"])

if __name__ == '__main__':
    unittest.main()
