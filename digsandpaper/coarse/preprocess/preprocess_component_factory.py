import constraint_consistency_factory
import constraint_expansion_factory
import constraint_type_mapper_factory
from constraint_type_mapper_factory import TopConstraintTypeMapper

component_order = {constraint_type_mapper_factory.name: 1,
                   constraint_consistency_factory.name: 2,
                   constraint_expansion_factory.name: 3}


def get_component(component_config):
    component_type = component_config["type"]
    if component_type == constraint_type_mapper_factory.name:
        return constraint_type_mapper_factory.get_component(component_config)
    elif component_type == constraint_consistency_factory.name:
        return constraint_consistency_factory.get_component(component_config)
    elif component_type == constraint_expansion_factory.name:
        return constraint_expansion_factory.get_component(component_config)
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
    if not is_component_type_found(component_configs, "ConstraintTypeMapper"):
        components.insert(0, TopConstraintTypeMapper())
    return components
