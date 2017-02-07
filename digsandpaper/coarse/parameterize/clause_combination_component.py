__name__ = "ClauseCombination"
name = __name__


class NoClauseCombination(object):

    name = "NoClauseCombination"
    component_type = __name__

    def parameterize(self, query):
        return [query]


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == NoClauseCombination.name:
        return NoClauseCombination()
    else:
        raise ValueError("Unsupported field combination component {}".
                         format(component_name))
