
from coarse.coarse_engine import CoarseEngine
from fine.fine_engine import FineEngine


class Engine(object):

    def __init__(self, config, host, port):
        self.config = config
        self.host = host
        self.port = port
        self.coarse = CoarseEngine(config.get("coarse", {}), host, port)
        self.fine = FineEngine(config.get("fine", {}))

    def execute(self, query):
        (expanded_queries, coarse_results) = self.coarse.execute(query)
        fine_results = self.fine.execute(expanded_queries, coarse_results)
        return fine_results
