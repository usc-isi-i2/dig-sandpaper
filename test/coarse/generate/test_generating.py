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
        self.assertNotIn("weight", where1["clauses"][1]["fields"][1])
        #print json.dumps(generated_queries, sort_keys=True, indent=4)

    def test_basic_coarse_generating_elasticsearch_compiler(self):
        config = load_json_file("1_config_step_two.json")
        parameterized_queries = load_json_file("1_query_step_two.json")
        generator = Generator(config)

        generated_queries = [generator.generate(
            q) for q in parameterized_queries]
        self.assertEqual(len(generated_queries), 2)
        #print json.dumps(generated_queries, sort_keys=True, indent=4)


if __name__ == '__main__':
    unittest.main()
