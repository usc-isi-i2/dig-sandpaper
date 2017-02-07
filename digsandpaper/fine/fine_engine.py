class FineEngine(object):

    def __init__(self, config):
        self.config = config
        self._initialize()

    def _initialize(self):
        self.name = ""

    def execute(self, expanded_queries, coarse_results):
        return {}
