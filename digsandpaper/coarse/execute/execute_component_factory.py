def get_component(component_config):
    component_type = component_config["type"]
    raise ValueError(
        "Unsupported component type: {}".format(component_type))


def get_components(component_configs):
    components = [get_component(component_config) for
                  component_config in component_configs]
    return components
