from . import generate_component_factory


class Generator(object):

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        component_configs = self.config.get("components", [])
        self.components = generate_component_factory.\
            get_components(component_configs)

    def generate(self, query):
        for component in self.components:
            query = component.generate(query)
        return query
