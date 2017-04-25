from digsandpaper import search_server
import unittest
import json
from digsandpaper.engine import Engine
import test_utils


class SearchServerTestCaseCoarse(unittest.TestCase):

    def setUp(self):
        search_server.app.config['TESTING'] = True
        self.app = search_server.app.test_client()

    def helper_setup(self, i):
        config = test_utils.load_engine_configuration(i)
        engine = Engine(config)
        query = test_utils.load_sub_configuration("coarse", "preprocess",
                                       i, "_query.json")
        document = test_utils.load_sub_configuration("coarse", "execute",
                                          i, "_document.json")
        es_config = config["coarse"]["execute"]["components"][0]
        test_utils.initialize_elasticsearch([document], es_config)
        search_server.set_engine(engine)
        return (query, es_config)

    def helper_test_coarse(self, i):
        (query, es_config) = self.helper_setup(i)
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
        self.assertEquals(len(results_6[0]["result"]["hits"]["hits"]), 1)
        self.assertEquals(results_6[0]["result"]["aggregations"]["?ethnicity"]["buckets"][0]["doc_count"], 1)

if __name__ == '__main__':
    unittest.main()
