from . import similarity_score_rerank_component


def get_component(component_config):
    component_type = component_config["type"]
    if component_type == similarity_score_rerank_component.name:
        return similarity_score_rerank_component.get_component(component_config)
    else:
        raise ValueError(
            "Unsupported component type: {}".format(component_type))


def is_component_type_found(component_configs, component_type):
    return len([component_config for component_config
                in component_configs
                if component_config["type"] == component_type]) > 1


def get_components(component_configs):
    components = [get_component(component_config) for
                  component_config in component_configs]
    return components
