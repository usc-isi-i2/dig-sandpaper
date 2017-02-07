import parameterize_component_factory


class Parameterizer(object):

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        component_configs = self.config.get("components", [])
        self.components = parameterize_component_factory.\
            get_components(component_configs)

    def parameterize(self, query):
        queries = [query]
        for component in self.components:
            parameterized_queries = []
            for query in queries:
                parameterized_queries.extend(component.parameterize(query))
            queries = parameterized_queries
        return queries
