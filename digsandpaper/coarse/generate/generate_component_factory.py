import field_weight_component
import type_field_mapping_component
import type_query_mapping_component
import zone_field_mapping_component

component_order = {type_field_mapping_component.name: 1,
                   zone_field_mapping_component.name: 2,
                   field_weight_component.name: 3,
                   type_query_mapping_component: 4}


def get_component(component_config):
    component_type = component_config["type"]
    if component_type == field_weight_component.name:
        return field_weight_component.get_component(component_config)
    elif component_type == type_field_mapping_component.name:
        return type_field_mapping_component.get_component(component_config)
    elif component_type == type_query_mapping_component.name:
        return type_query_mapping_component.get_component(component_config)
    elif component_type == zone_field_mapping_component.name:
        return zone_field_mapping_component.get_component(component_config)
    else:
        raise ValueError(
            "Unsupported component type: {}".format(component_type))


def is_component_type_found(component_configs, component_type):
    return len([component_config for component_config
                in component_configs
                if component_config["type"] == component_type]) > 1


def get_component_type_order(component):
    return component_order[component.component_type]


def get_components(component_configs):
    components = [get_component(component_config) for
                  component_config in component_configs]
    components = sorted(components, key=get_component_type_order)
    return components
