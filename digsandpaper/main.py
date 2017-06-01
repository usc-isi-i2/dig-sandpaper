#!/usr/bin/env python
import json
import codecs

from optparse import OptionParser
from engine import Engine
import search_server


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


def main(args):
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-h", "--host", action="store",
                      type="string", dest="host", default="localhost")
    parser.add_option("-p", "--port", action="store",
                      type="int", dest="port", default=9876)
    parser.add_option("-c", "--config", action="store",
                      type="string", dest="config")
    parser.add_option("-q", "--query", action="store",
                      type="string", dest="query")
    parser.add_option("-s", "--server", action="store_true",
                      dest="server", default=False)
    (c_options, args) = parser.parse_args()

    query_file = c_options.query
    config_file = c_options.config
    server = c_options.server
    host = c_options.host
    port = c_options.port

    if not config_file:
        parser.error('Config file not specified.  Use -c or --config')

    config = load_json_file(config_file)
    engine = Engine(config)
    if server:
        search_server.set_engine(engine)
        search_server.app.run(host, port, threaded=True)
    else:
        query = load_json_file(query_file)
        result = engine.execute(query)
        print result


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
