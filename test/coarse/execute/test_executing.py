import unittest
import json
import codecs
from digsandpaper.coarse.execute.executor import Executor
import os
import test.test_utils

_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_json_file(file_name):
    with codecs.open(os.path.join(_location__,
                                  file_name),
                     'r', 'utf-8') as json_file:
        rules = json.load(json_file)
        return rules


class TestCoarseExecuting(unittest.TestCase):

    def test_basic_coarse_executing(self):
        config = load_json_file("1_config.json")
        queries = load_json_file("1_query.json")
        document = load_json_file("1_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEqual(len(result.hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_compound_filters(self):
        config = load_json_file("2_config.json")
        queries = load_json_file("2_query.json")
        document = load_json_file("2_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEqual(len(result.hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_compound_filters_no_type_mapping(self):
        config = load_json_file("3_config.json")
        queries = load_json_file("3_query.json")
        document = load_json_file("3_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEqual(len(result.hits), 1)
            self.assertIn("fields", result.hits[0])
            self.assertIn("posting-date", result.hits[0]["fields"])
            self.assertEqual("2015-03-01T14:02:00",
                             result.hits[0]["fields"]["posting-date"]["strict"]["name"])

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_date_filters(self):
        config = load_json_file("4_config.json")
        queries = load_json_file("4_query.json")
        document = load_json_file("4_document.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEqual(len(result.hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_sparql_unnesting(self):
        config = load_json_file("5_config.json")
        queries = load_json_file("5_query.json")
        ad_document = load_json_file("5_document_ad.json")
        cluster_document = load_json_file("5_document_cluster.json")
        docs_by_type = {"ads": [ad_document],
                        "clusters": [cluster_document]}

        test.test_utils.initialize_elasticsearch_doc_types(docs_by_type,
                                                           config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            self.assertEqual(len(result), 2)
            self.assertEqual(len(result[1].hits), 1)

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_aggregation(self):
        config = load_json_file("6_config.json")
        queries = load_json_file("6_query.json")
        document = load_json_file("6_document.json")
        mapping = load_json_file("6_mapping.json")

        test.test_utils.initialize_elasticsearch([document],
                                                 config["components"][0],
                                                 mapping)

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            result_dict = result.to_dict()
            # aggregation queries should not return any documents
            self.assertEqual(len(result.hits), 0)
            self.assertIn("aggregations", result_dict)
            self.assertIn("?ethnicity", result_dict["aggregations"])
            self.assertEqual(1, len(result_dict["aggregations"]["?ethnicity"]["buckets"]))
            self.assertEqual(1,
                             result_dict["aggregations"]["?ethnicity"]["buckets"][0]["doc_count"])

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_union_and_not_exists(self):
        config = load_json_file("7_config.json")
        queries = load_json_file("7_query.json")
        document = load_json_file("7_document.json")
        document2 = load_json_file("7_document_2.json")
        document3 = load_json_file("7_document_3.json")

        test.test_utils.initialize_elasticsearch([document, document2, document3],
                                                 config["components"][0])

        executor = Executor(config)

        for query in queries:
            result = executor.execute(query)
            result_dict = result.to_dict()
            self.assertEqual(len(result.hits), 1)
            self.assertEqual("QPONMLKJIHGFEDCBA",
                             result_dict["hits"]["hits"][0]["_source"]["doc_id"])

        test.test_utils.reset_elasticsearch(config["components"][0])
        executor.teardown()

    def test_basic_coarse_executing_network_expansion(self):
        config = load_json_file("8_config.json")
        queries = load_json_file("8_query.json")
        document = load_json_file("8_document.json")
        document2 = load_json_file("8_document_2.json")
        document3 = load_json_file("8_document_3.json")
        document4 = load_json_file("8_document_4.json")
        document5 = load_json_file("8_document_5.json")
        document6 = load_json_file("8_document_6.json")
        mapping = load_json_file("8_mapping.json")

        test.test_utils.initialize_elasticsearch([document, document2, document3,
                                                  document4, document5, document6],
                                                 config["components"][0], mapping)

        executor = Executor(config)

        try:
            for query in queries:
                results = executor.execute(query)
                result1 = results[0]
                self.assertEqual(len(result1.hits), 4)
                result2 = results[1]
                result2_dict = result2.to_dict()
                self.assertEqual(len(result2.hits), 5)
                self.assertEqual("JKLMNOPQABCDEFGHI",
                                 result2_dict["hits"]["hits"][4]["_source"]["doc_id"])
        finally:
            test.test_utils.reset_elasticsearch(config["components"][0])
            executor.teardown()

    def test_basic_coarse_order_by(self):
        config = load_json_file("9_config.json")
        queries = load_json_file("9_query.json")
        document = load_json_file("9_document.json")
        document2 = load_json_file("9_document_2.json")
        document3 = load_json_file("9_document_3.json")
        document4 = load_json_file("9_document_4.json")
        document5 = load_json_file("9_document_5.json")
        document6 = load_json_file("9_document_6.json")
        mapping = load_json_file("9_mapping.json")

        test.test_utils.initialize_elasticsearch([document, document2, document3,
                                                  document4, document5, document6],
                                                 config["components"][0], mapping)

        executor = Executor(config)

        try:
            for query in queries:
                result = executor.execute(query)
                result_dict = result.to_dict()
                self.assertEqual(len(result.hits), 4)
                self.assertEqual("PQABCDEFGHIJKLMNO",
                                 result_dict["hits"]["hits"][0]["_source"]["doc_id"])
                self.assertEqual("DEFGHIJKLMNOPQABCD",
                                 result_dict["hits"]["hits"][1]["_source"]["doc_id"])
                self.assertEqual("GHIJKLMNOPQABCDEF",
                                 result_dict["hits"]["hits"][2]["_source"]["doc_id"])
                self.assertEqual("ABCDEFGHIJKLMNOPQ",
                                 result_dict["hits"]["hits"][3]["_source"]["doc_id"])
        finally:
            test.test_utils.reset_elasticsearch(config["components"][0])
            executor.teardown()

    def test_basic_coarse_rank_scoring_coefficient(self):
        config = load_json_file("10_config.json")
        queries = load_json_file("10_query.json")
        document = load_json_file("10_document.json")
        document2 = load_json_file("10_document_2.json")
        document3 = load_json_file("10_document_3.json")
        document4 = load_json_file("10_document_4.json")

        test.test_utils.initialize_elasticsearch([document, document2, document3, document4],
                                                 config["components"][0])

        executor = Executor(config)

        try:
            for query in queries:
                result = executor.execute(query)
                result_dict = result.to_dict()
                self.assertEqual(len(result.hits), 4)
                self.assertEqual("ABCDEFGHIJKLMNOPQ",
                                 result_dict["hits"]["hits"][0]["_source"]["doc_id"])
                self.assertEqual("DEFGHIJKLMNOPQABCD",
                                 result_dict["hits"]["hits"][1]["_source"]["doc_id"])
                self.assertEqual("GHIJKLMNOPQABCDEF",
                                 result_dict["hits"]["hits"][2]["_source"]["doc_id"])
                self.assertEqual("JKLMNOPQABCDEFGHI",
                                 result_dict["hits"]["hits"][3]["_source"]["doc_id"])
        finally:
            test.test_utils.reset_elasticsearch(config["components"][0])
            executor.teardown()


if __name__ == '__main__':
    unittest.main()
