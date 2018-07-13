import time
import json
import codecs
from optparse import OptionParser
import requests
import sys


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


def main(args):
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-h", "--host", action="store",
                      type="string", dest="host", default="localhost")
    parser.add_option("-p", "--port", action="store",
                      type="int", dest="port", default=9876)
    parser.add_option("-e", "--endpoint", action="store",
    	              type="string", dest="endpoint", default=None)
    parser.add_option("-q", "--query", action="store",
                      type="string", dest="query")
    parser.add_option("-g", "--generate", action="store_true",
                      dest="is_generate", default=False)
    parser.add_option("-j", "--project", action="store",
                      type="string", dest="project")
    parser.add_option("-c", action="store_true", dest="is_coarse", default=False)
    (c_options, args) = parser.parse_args()

    query_file = c_options.query
    host = c_options.host
    port = c_options.port
    endpoint = c_options.endpoint
    is_coarse = c_options.is_coarse
    is_generate = c_options.is_generate
    project = c_options.project

    if not query_file:
        parser.error('Query file not specified.  Use -q or --query')

    if not endpoint:
        endpoint = "http://{}:{}/search".format(host, port)
    if not endpoint.endswith("/search"):
        endpoint = "{}/search".format(endpoint)
    if is_coarse:
        endpoint = "{}/coarse".format(endpoint)
        if is_generate:
            endpoint = "{}/generate".format(endpoint)
    if project:
        endpoint = "{}?project={}".format(endpoint, project)

    query_file_json = load_json_file(query_file)
    if isinstance(query_file_json, list):
        print("[")
        query_count = len(query_file_json)
        i = 0
        separator = ","
        for query in query_file_json:
            i = i + 1
            start = time.time()
            r = requests.post(endpoint, json=query)
            if r.status_code == 200:
                if query_count == i:
                    separator = ""

                if r.text[0] == '[':
                    print("{}{}".format(r.text[1:-1], separator))
                else:
                    print("{}{}".format(r.text, separator))
                end = time.time()
                sys.stderr.write("{},{}\n".format(query.get("id", "unknown"), end - start))
            else:
                sys.stderr.write("{} query failed error code: {}\n".format(query.get("id",
                                                                                     "unknown"),
                                                                           r.status_code))
        print("]")
    else:
        query = query_file_json
        r = requests.post(endpoint, json=query)
        print(r.text)


if __name__ == "__main__":
    main(sys.argv[1:])
