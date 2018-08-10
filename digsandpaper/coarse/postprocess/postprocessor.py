from . import postprocess_component_factory


class PostProcessor(object):
    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        component_configs = self.config.get("components", [])
        self.components = postprocess_component_factory. \
            get_components(component_configs)

    def postprocess(self, query, result):
        for component in self.components:
            result = component.postprocess(query, result)

        return result
