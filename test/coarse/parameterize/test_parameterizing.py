import unittest
import json
import codecs
from digsandpaper.coarse.parameterize.parameterizer import Parameterizer
import os


_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    rules = json.load(codecs.open(os.path.join(_location__, file_name),
                                  'r', 'utf-8'))
    return rules


class TestCoarseParameterizing(unittest.TestCase):

    def test_basic_coarse_parameterizing(self):
        config = load_json_file("1_config.json")
        query = load_json_file("1_query.json")
        parameterizer = Parameterizer(config)

        results = parameterizer.parameterize(query)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["zone"], [1])
        self.assertEqual(results[1]["zone"], [1, 2])
        self.assertEqual(results[0]["field_count"], 1)
        self.assertEqual(results[1]["field_count"], 1)

        #print "parameterized result"
        #print json.dumps(results, sort_keys=True, indent=4)


if __name__ == '__main__':
    unittest.main()
