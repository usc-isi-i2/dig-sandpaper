import copy


__name__ = "ZoneHierarchy"
name = __name__


class SingleZoneHierarchy(object):

    name = "SingleZoneHierarchy"
    component_type = __name__

    def parameterize(self, query):
        query["zone"] = 1
        return [query]


class MultipleZoneHierarchy(object):

    name = "MultipleZoneHierarchy"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        self.zone_count = self.config["zone_count"]

    def parameterize(self, query):
        queries = list()
        for x in range(1, self.zone_count + 1):
            parameterized_query = copy.deepcopy(query)
            parameterized_query["zone"] = range(1, x+1)
            queries.append(parameterized_query)
        return queries


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == SingleZoneHierarchy.name:
        return SingleZoneHierarchy()
    elif component_name == MultipleZoneHierarchy.name:
        return MultipleZoneHierarchy(component_config)
    else:
        raise ValueError("Unsupported zone hierarchy component {}".
                         format(component_name))
