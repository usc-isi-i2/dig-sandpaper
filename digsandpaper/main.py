#!/usr/bin/env python
import json
import codecs

from optparse import OptionParser
from engine import Engine


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-h", "--host", action="store",
                      type="string", dest="host", default="localhost")
    parser.add_option("-p", "--port", action="store",
                      type="int", dest="port", default=9200)
    parser.add_option("-c", "--config", action="store",
                      type="string", dest="config")
    parser.add_option("-q", "--query", action="store",
                      type="string", dest="query")
    (c_options, args) = parser.parse_args()

    query_file = c_options.query
    config_file = c_options.config
    host = c_options.host
    port = c_options.port

    config = load_json_file(config_file)
    query = load_json_file(query_file)
    engine = Engine(config, host, port)
    result = engine.execute(query)
    print result
