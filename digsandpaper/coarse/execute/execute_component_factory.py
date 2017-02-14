import execute_query_component


def get_component(component_config):
    component_type = component_config["type"]
    if component_type == execute_query_component.name:
        return execute_query_component.get_component(component_config)
    raise ValueError(
        "Unsupported component type: {}".format(component_type))


def get_components(component_configs):
    components = [get_component(component_config) for
                  component_config in component_configs]
    return components
