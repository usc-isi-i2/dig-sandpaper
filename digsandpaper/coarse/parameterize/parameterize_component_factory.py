import zone_hierarchy_component
import field_combination_component
import extractor_hierarchy_component
import clause_combination_component


def get_component(component_config):
    component_type = component_config["type"]
    if component_type == zone_hierarchy_component.name:
        return zone_hierarchy_component.get_component(component_config)
    elif component_type == field_combination_component.name:
        return field_combination_component.get_component(component_config)
    elif component_type == extractor_hierarchy_component.name:
        return extractor_hierarchy_component.get_component(component_config)
    elif component_type == clause_combination_component.name:
        return clause_combination_component.get_component(component_config)
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
