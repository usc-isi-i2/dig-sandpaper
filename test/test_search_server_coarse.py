from digsandpaper import search_server
import unittest
import json
from digsandpaper.engine import Engine
import test_utils


class SearchServerTestCaseCoarse(unittest.TestCase):

    def setUp(self):
        search_server.app.config['TESTING'] = True
        self.app = search_server.app.test_client()

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
        response = self.app.post('/search/coarse', data=json.dumps(query))
        self.assertEquals(200, response.status_code)
        results = json.loads(response.data)
        test_utils.reset_elasticsearch(es_config)
        return results

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

    def test_coarse_6(self):
        results_6 = self.helper_test_coarse(6)
        self.assertEquals(len(results_6), 1)
        self.assertEquals(results_6[0]["result"]["aggregations"]
                                      ["?ethnicity"]["buckets"]
                                      [0]["doc_count"], 1)

    def test_coarse_7(self):
        results_7 = self.helper_test_coarse(7, ["2", "3"])
        self.assertEquals(len(results_7), 1)
        self.assertEquals(len(results_7[0]["result"]["hits"]["hits"]), 1)

    def test_coarse_8(self):
        results_8 = self.helper_test_coarse(8, ["2", "3", "4", "5", "6"], True)
        self.assertEquals(len(results_8), 1)
        self.assertEquals(len(results_8[0]["result"][0]["hits"]["hits"]), 4)
        self.assertEquals(len(results_8[0]["result"][1]["hits"]["hits"]), 5)

    def test_coarse_9(self):
        results_9 = self.helper_test_coarse(9, ["2", "3", "4", "5", "6"], True)
        self.assertEquals(len(results_9), 1)
        self.assertEquals(len(results_9[0]["result"]["hits"]["hits"]), 4)
        hits = results_9[0]["result"]["hits"]["hits"]
        self.assertEquals("PQABCDEFGHIJKLMNO", hits[0]["_source"]["doc_id"])
        self.assertEquals("DEFGHIJKLMNOPQABCD", hits[1]["_source"]["doc_id"])
        self.assertEquals("GHIJKLMNOPQABCDEF", hits[2]["_source"]["doc_id"])
        self.assertEquals("ABCDEFGHIJKLMNOPQ", hits[3]["_source"]["doc_id"])


if __name__ == '__main__':
    unittest.main()
