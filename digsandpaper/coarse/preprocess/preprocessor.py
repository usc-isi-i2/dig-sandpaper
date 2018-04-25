from . import preprocess_component_factory


class Preprocessor(object):

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        component_configs = self.config.get("components", [])
        self.components = preprocess_component_factory.\
            get_components(component_configs)

    def preprocess(self, query):
        for component in self.components:
            query = component.preprocess(query)
        return query
