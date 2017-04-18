import json
import os
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
    (c_options, args) = parser.parse_args()

    query_file = c_options.query
    host = c_options.host
    port = c_options.port
    endpoint = c_options.endpoint

    if not query_file:
        parser.error('Query file not specified.  Use -q or --query')

    if not endpoint:
        endpoint = "http://{}:{}/search".format(host, port)
    if not endpoint.endswith("/search"):
        endpoint = "{}/search".format(endpoint)

    query_file_json = load_json_file(query_file)
    if isinstance(query_file_json, list):
        for query in query_file_json:
            r =requests.post(endpoint, json.dumps(query))
            print(r.status_code)
            print(r.text)
    else:
        r = requests.post(endpoint, json.dumps(query))
        print(r.status_code)
        print(r.text)

if __name__ == "__main__":
    main(sys.argv[1:])