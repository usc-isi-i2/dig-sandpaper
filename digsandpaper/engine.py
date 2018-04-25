
from .coarse.coarse_engine import CoarseEngine
from .fine.fine_engine import FineEngine


class Engine(object):

    def __init__(self, config):
        self.config = config
        self.coarse = CoarseEngine(config.get("coarse", {}))
        self.fine = FineEngine(config.get("fine", {}))

    def execute(self, query):
        (expanded_queries, coarse_results) = self.execute_coarse(query)
        fine_results = self.execute_fine(expanded_queries, coarse_results)
        return fine_results

    def execute_coarse(self, query):
        return self.coarse.execute(query)

    def generate_coarse(self, query):
        return self.coarse.generate(query)

    def execute_fine(self, expanded_queries, coarse_results):
        return self.fine.execute(expanded_queries, coarse_results)

    def teardown(self):
        self.coarse.teardown()
