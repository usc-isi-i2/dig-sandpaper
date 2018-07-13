from digsandpaper import search_server
import unittest
import json
from digsandpaper.engine import Engine
from test import test_utils


class SearchServerTestCase(unittest.TestCase):

    def setUp(self):
        search_server.app.config['TESTING'] = True
        self.app = search_server.app.test_client()

    def tearDown(self):
        test_utils.reset_elasticsearch()
        search_server.get_engine().teardown()

    def helper_setup(self, i, docs_by_type):
        config = test_utils.load_engine_configuration(i)
        engine = Engine(config)
        es_config = config["coarse"]["execute"]["components"][0]
        test_utils.initialize_elasticsearch_doc_types(docs_by_type, es_config)
        search_server.set_engine(engine)
        return es_config

    def helper_test(self, i, docs_by_type):
        query = test_utils.load_sub_configuration("coarse", "preprocess",
                                                  i, "_query.json")
        es_config = self.helper_setup(i, docs_by_type)
        headers = {'Content-Type': 'application/json'}
        response = self.app.post('/search', data=json.dumps(query),
                                 headers=headers)
        self.assertEqual(200, response.status_code)
        results = json.loads(response.data)
        test_utils.reset_elasticsearch(es_config)
        return results

    def test_search_1(self):
        document = test_utils.load_sub_configuration("coarse", "execute",
                                                     1, "_document.json")
        results_1 = self.helper_test(1, {"ads": [document]})
        self.assertEqual(2, len(results_1))
        self.assertEqual(1, len(results_1[0]["answers"]))
        self.assertEqual(1, len(results_1[1]["answers"]))
        self.assertEqual("caucasian", results_1[0]["answers"][0][1])

    def test_search_5(self):
        ad_document = test_utils.load_sub_configuration("coarse", "execute",
                                                        5, "_document_ad.json")
        cluster_document = test_utils.load_sub_configuration("coarse", "execute",
                                                             5, "_document_cluster.json")
        results_5 = self.helper_test(5, {"ads": [ad_document],
                                         "clusters": [cluster_document]})
        self.assertEqual(1, len(results_5))
        self.assertEqual(1, len(results_5[0]["answers"]))
        self.assertEqual("jane", results_5[0]["answers"][0][0])
        self.assertEqual("jane", results_5[0]["agg"])


if __name__ == '__main__':
    unittest.main()
