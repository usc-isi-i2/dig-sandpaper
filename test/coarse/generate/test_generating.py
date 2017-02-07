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
        self.assertEqual(len(generated_queries), 2)
        self.assertEqual(generated_queries[0]["SPARQL"]["where"]["clauses"][1]["fields"][0]["name"],
                         "extractors.content_strict.data_extractors.city.result.value")
        self.assertEqual(generated_queries[0]["SPARQL"]["where"]["clauses"][1]["fields"][0]["weight"],
                         4)
        self.assertEqual(generated_queries[1]["SPARQL"]["where"]["clauses"][1]["fields"][1]["name"],
                         "extractors.content_relaxed.data_extractors.city.result.value")
        self.assertNotIn("weight", generated_queries[1]["SPARQL"]["where"]["clauses"][1]["fields"][1])


if __name__ == '__main__':
    unittest.main()
