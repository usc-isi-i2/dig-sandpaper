from . import execute_component_factory


class Executor(object):

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        component_configs = self.config.get("components", [])
        self.components = execute_component_factory.\
            get_components(component_configs)

    def execute(self, query):
        for component in self.components:
            results = component.execute(query)
        return results

    def teardown(self):
        for component in self.components:
            component.teardown()
