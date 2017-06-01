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
    parser.add_option("-c", action="store_true", dest="is_coarse", default=False)
    (c_options, args) = parser.parse_args()

    query_file = c_options.query
    host = c_options.host
    port = c_options.port
    endpoint = c_options.endpoint
    is_coarse = c_options.is_coarse

    if not query_file:
        parser.error('Query file not specified.  Use -q or --query')

    if not endpoint:
        endpoint = "http://{}:{}/search".format(host, port)
    if not endpoint.endswith("/search"):
        endpoint = "{}/search".format(endpoint)
    if is_coarse:
        endpoint = "{}/coarse".format(endpoint)

    query_file_json = load_json_file(query_file)
    if isinstance(query_file_json, list):
        print "["
        for query in query_file_json:
            r =requests.post(endpoint, json.dumps(query))
            if r.status_code == 200:
                if r.text[0] == '[':
                    print "{},".format(r.text[1:-1])
                else:
                    print "{},".format(r.text)
            else: 
                sys.stderr.write("{} query failed error code: {}\n".format(query.get("id", "unknown"), r.status_code))
        print "]"
    else:
        r = requests.post(endpoint, json.dumps(query))
        print(r.text)

if __name__ == "__main__":
    main(sys.argv[1:])