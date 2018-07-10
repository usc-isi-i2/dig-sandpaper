from digsandpaper import sandpaper_utils
import unittest
import json


class SearchServerTestCase(unittest.TestCase):

    def setUp(self):
        self.doc1 = json.load(open('mydig/kg_jsonld.json'))
        self.doc2 = json.load(open('mydig/kg2_jsonld.json'))

    def test_cdr_1(self):
        converted_docs = sandpaper_utils.convert_jsonld_cdr(self.doc1)
        self.assertTrue(len(converted_docs) == 2)
        self.assertTrue('@context' in converted_docs[0])
        self.assertTrue('doc_id' in converted_docs[0])
        self.assertTrue('knowledge_graph' in converted_docs[0])
        c_doc1_id = converted_docs[0]['doc_id']
        self.assertEqual(c_doc1_id, 'http://www.isi.edu/dig/entities/dc81cfec-0606-43d2-829f-bb1b02046172')

        self.assertTrue('@context' in converted_docs[1])
        self.assertTrue('doc_id' in converted_docs[1])
        self.assertTrue('knowledge_graph' in converted_docs[1])
        self.assertTrue(c_doc1_id in [x['key'] for x in converted_docs[1]['knowledge_graph']['conflict_attack_place']])

    def test_cdr_2(self):
        converted_docs = sandpaper_utils.convert_jsonld_cdr(self.doc2)
        self.assertTrue(len(converted_docs) == 1)
        self.assertTrue('type' in converted_docs[0]['knowledge_graph'])
        self.assertTrue('conflict_attack_place' in converted_docs[0]['knowledge_graph'])
        self.assertTrue('prefLabel' in converted_docs[0]['knowledge_graph'])
        self.assertEqual(converted_docs[0]['knowledge_graph']['prefLabel'][0]['value'], 'shot')


if __name__ == '__main__':
    unittest.main()
