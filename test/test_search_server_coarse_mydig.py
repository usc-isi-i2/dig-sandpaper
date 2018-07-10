from digsandpaper import search_server
import unittest
import json
import time
from test import test_utils
from digsandpaper.engine import Engine


class SearchServerTestCase(unittest.TestCase):

    def setUp(self):
        search_server.app.config['TESTING'] = True
        self.app = search_server.app.test_client()
        engine_config = test_utils.load_engine_configuration(1)
        self.engine = Engine(engine_config)
        search_server.set_engine(self.engine)

    def tearDown(self):
        test_utils.reset_elasticsearch()
        search_server.get_engine().teardown()
        self.engine.teardown()

    def initialize_elasticsearch_doc_types(self, project, documents_by_type):
        for (t, docs) in documents_by_type.items():
            self.initialize_elasticsearch_docs(project, docs, t)

    def initialize_elasticsearch_docs(self, project, documents, t="ads"):
        params = {'project': project, 'type': 'ads',
                  'index': 'dig-sandpaper-test'}
        headers = {'Content-Type': 'application/json'}
        for document in documents:
            response = self.app.post('/indexing',
                                     query_string=params,
                                     data=json.dumps(document),
                                     headers=headers)
            self.assertEqual(200, response.status_code)
        time.sleep(5)

    def helper_setup(self, i, docs_by_type):
        project = 'project{}'.format(i)
        # load mydig config
        mydig_config = test_utils.load_mydig_configuration(i, '_config.json')
        headers = {'Content-Type': 'application/json'}

        # apply mydig config
        params = {'project': project, 'index': 'dig-sandpaper-test'}
        response = self.app.post('/config',
                                 data=json.dumps(mydig_config),
                                 query_string=params,
                                 headers=headers)
        self.assertEqual(200, response.status_code)

        # generate mapping in elasticsearch
        response = self.app.post('/mapping',
                                 data=json.dumps(mydig_config),
                                 query_string=params,
                                 headers=headers)
        self.assertEqual(200, response.status_code)

        # index documents by type
        self.initialize_elasticsearch_doc_types(project, docs_by_type)

    def helper_test(self, i, docs_by_type):
        project = 'project{}'.format(i)
        query = test_utils.load_mydig_configuration(i, "_query.json")
        self.helper_setup(i, docs_by_type)
        params = {'project': project}
        headers = {'Content-Type': 'application/json'}

        response = self.app.post('/search/coarse', data=json.dumps(query),
                                 query_string=params,
                                 headers=headers)
        self.assertEqual(200, response.status_code)
        results = json.loads(response.data)
        return results

    def test_search_1(self):
        document = test_utils.load_mydig_configuration(1, "_document.json")
        results_1 = self.helper_test(1, {"ads": [document]})
        self.assertEqual(len(results_1), 1)
        self.assertEqual(len(results_1[0]["result"]["hits"]["hits"]), 1)

    def test_search_2(self):
        document = test_utils.load_mydig_configuration(2, "_document.json")
        results_2 = self.helper_test(2, {"ads": [document]})
        self.assertEqual(len(results_2), 1)
        self.assertEqual(len(results_2[0]["result"]["hits"]["hits"]), 1)


if __name__ == '__main__':
    unittest.main()
