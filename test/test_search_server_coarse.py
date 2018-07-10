from digsandpaper import search_server
import unittest
import json
from digsandpaper.engine import Engine
from test import test_utils


class SearchServerTestCaseCoarse(unittest.TestCase):

    def setUp(self):
        search_server.app.config['TESTING'] = True
        self.app = search_server.app.test_client()

    def tearDown(self):
        test_utils.reset_elasticsearch()
        search_server.get_engine().teardown()

    def helper_setup(self, i, additional_documents_suffixes=[],
                     has_mapping=False):
        config = test_utils.load_engine_configuration(i)
        engine = Engine(config)
        query = test_utils.load_sub_configuration("coarse", "preprocess",
                                                  i, "_query.json")
        documents = []
        document = test_utils.load_sub_configuration("coarse", "execute",
                                                     i, "_document.json")
        documents.append(document)
        if additional_documents_suffixes:
            for a in additional_documents_suffixes:
                documents.append(test_utils.load_sub_configuration("coarse",
                                                                   "execute",
                                                                   i,
                                                                   "_document_{}.json".format(a)))

        if has_mapping:
            mapping = test_utils.load_sub_configuration("coarse", "execute",
                                                        i, "_mapping.json")
        else:
            mapping = {}
        es_config = config["coarse"]["execute"]["components"][0]
        test_utils.initialize_elasticsearch(documents, es_config, mapping)
        search_server.set_engine(engine)
        return (query, es_config)

    def helper_test_coarse(self, i, additional_documents_suffixes=[],
                           has_mapping=False):
        (query, es_config) = self.helper_setup(i,
                                               additional_documents_suffixes,
                                               has_mapping)

        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search/coarse', data=json.dumps(query),
                                 headers=headers)
        self.assertEqual(200, response.status_code)
        results = json.loads(response.data)
        test_utils.reset_elasticsearch(es_config)
        return results

    def test_coarse_1(self):
        results_1 = self.helper_test_coarse(1)
        self.assertEqual(len(results_1), 2)
        self.assertEqual(len(results_1[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_2(self):
        results_2 = self.helper_test_coarse(2)
        self.assertEqual(len(results_2), 1)
        self.assertEqual(len(results_2[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_3(self):
        results_3 = self.helper_test_coarse(3)
        self.assertEqual(len(results_3), 1)
        self.assertEqual(len(results_3[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_4(self):
        results_4 = self.helper_test_coarse(4)
        self.assertEqual(len(results_4), 1)
        self.assertEqual(len(results_4[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_6(self):
        results_6 = self.helper_test_coarse(6, has_mapping=True)
        self.assertEqual(len(results_6), 1)
        self.assertEqual(results_6[0]["result"]["aggregations"]
                                     ["?ethnicity"]["buckets"]
                                     [0]["doc_count"], 1)

    def test_coarse_7(self):
        results_7 = self.helper_test_coarse(7, ["2", "3"])
        self.assertEqual(len(results_7), 1)
        self.assertEqual(len(results_7[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_8(self):
        results_8 = self.helper_test_coarse(8, ["2", "3", "4", "5", "6"], True)
        self.assertEqual(len(results_8), 1)
        self.assertEqual(len(results_8[0]["result"][0]["hits"]["hits"]), 4)
        self.assertEqual(len(results_8[0]["result"][1]["hits"]["hits"]), 5)

    def test_coarse_9(self):
        results_9 = self.helper_test_coarse(9, ["2", "3", "4", "5", "6"], True)
        self.assertEqual(len(results_9), 1)
        self.assertEqual(len(results_9[0]["result"]["hits"]["hits"]), 4)
        hits = results_9[0]["result"]["hits"]["hits"]
        self.assertEqual("PQABCDEFGHIJKLMNO", hits[0]["_source"]["doc_id"])
        self.assertEqual("DEFGHIJKLMNOPQABCD", hits[1]["_source"]["doc_id"])
        self.assertEqual("GHIJKLMNOPQABCDEF", hits[2]["_source"]["doc_id"])
        self.assertEqual("ABCDEFGHIJKLMNOPQ", hits[3]["_source"]["doc_id"])

    def test_coarse_10(self):
        results_10 = self.helper_test_coarse(10, ["2", "3", "4"], False)
        self.assertEqual(len(results_10), 1)
        self.assertEqual(len(results_10[0]["result"]["hits"]["hits"]), 4)
        hits = results_10[0]["result"]["hits"]["hits"]
        self.assertEqual("ABCDEFGHIJKLMNOPQ", hits[0]["_source"]["doc_id"])
        self.assertEqual("DEFGHIJKLMNOPQABCD", hits[1]["_source"]["doc_id"])
        self.assertEqual("GHIJKLMNOPQABCDEF", hits[2]["_source"]["doc_id"])
        self.assertEqual("JKLMNOPQABCDEFGHI", hits[3]["_source"]["doc_id"])


if __name__ == '__main__':
    unittest.main()
