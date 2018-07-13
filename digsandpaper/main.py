#!/usr/bin/env python
import json
import codecs

from optparse import OptionParser
from .engine import Engine
from . import search_server
from .search_server import update_endpoint


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
    parser.add_option("-u", "--mydigurl", action="store",
                      type="string", dest="mydigurl")
    parser.add_option("-j", "--project", action="store",
                      type="string", dest="project")
    parser.add_option("-e", "--endpoint", action="store",
                      type="string", dest="endpoint")
    parser.add_option("-i", "--index", action="store",
                      type="string", dest="index")
    parser.add_option("-m", "--sample", action="store_true",
                      dest="sample", default=False)
    (c_options, args) = parser.parse_args()

    query_file = c_options.query
    config_file = c_options.config
    server = c_options.server
    host = c_options.host
    port = c_options.port
    mydigurl = c_options.mydigurl
    project = c_options.project
    endpoint = c_options.endpoint
    index = c_options.index
    sample = c_options.sample

    if not config_file:
        parser.error('Config file not specified.  Use -c or --config')

    config = load_json_file(config_file)
    if endpoint:
        update_endpoint(config, endpoint)
    engine = Engine(config)
    if server:
        search_server.set_engine(engine)
        if mydigurl and project:
            search_server.apply_config_from_project(mydigurl, project,
                                                    endpoint, index,
                                                    sample=sample)
        if not host and not port:
            search_server.app.run()
        else:
            search_server.app.run(host, port, threaded=True)
    else:
        query = load_json_file(query_file)
        result = engine.execute(query)
        print(result)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
