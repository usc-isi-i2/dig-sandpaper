__name__ = "FieldCombination"
name = __name__


class AtLeastOneFieldCombination(object):

    name = "AtLeastOneFieldCombination"
    component_type = __name__

    def parameterize(self, query):
        query["field_count"] = 1
        return [query]


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == AtLeastOneFieldCombination.name:
        return AtLeastOneFieldCombination()
    else:
        raise ValueError("Unsupported field combination component {}".
                         format(component_name))
