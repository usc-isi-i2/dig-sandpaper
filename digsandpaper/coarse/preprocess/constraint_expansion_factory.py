from __future__ import unicode_literals
from digsandpaper.sandpaper_utils import load_json_file
import copy
import uuid

__name__ = "ConstraintExpansion"
name = __name__


class LambdaConstraintExpander(object):

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        self.expand = None

    def preprocess_filter(self, f):
        if "clauses" in f:
            if isinstance(f["clauses"], list):
                f["clauses"] = [self.preprocess_filter(c) for c in f["clauses"]]
                return f
            elif isinstance(f["clauses"], dict):
                f["clauses"] = self.preprocess_filter(f["clauses"])
                return f
        else:
            if "constraint" not in f or "type" not in f:
                return f
            new_filters = []
            expanded_values = self.expand(f)
            for expanded_value in expanded_values:
                new_filter = copy.copy(f)
                new_filter["constraint"] = expanded_value
                new_filter["isOptional"] = True
                new_filter["_id"] = uuid.uuid4().hex
                new_filters.append(new_filter)
            if len(new_filters) > 0:
                new_filters.append(f)
                return {"operator": "or", "clauses": new_filters}
            else:
                return f

    def preprocess_clauses(self, clause):
        new_clauses = list()

        # this should become a union
        if "clauses" in clause:
            for sub_clause in clause["clauses"]:
                if "constraint" not in sub_clause:
                    if "clauses" in sub_clause:
                        self.preprocess_clauses(sub_clause)
                    continue
                expanded_values = self.expand(sub_clause)
                for expanded_value in expanded_values:
                    new_clause = copy.copy(sub_clause)
                    new_clause["constraint"] = expanded_value
                    new_clause["isOptional"] = True
                    new_clause["_id"] = uuid.uuid4().hex
                    new_clauses.append(new_clause)
            clause["clauses"].extend(new_clauses)
        if "filters" in clause:
            filters = clause["filters"]
            clause["filters"] = [self.preprocess_filter(f) for f in filters]

    def preprocess(self, query):
        where = query["SPARQL"]["where"]

        if "clauses" in where:
            self.preprocess_clauses(where)

        return query


class IdentityConstraintExpander(LambdaConstraintExpander):

    name = "IdentityConstraintExpander"
    component_type = __name__

    def __init__(self):
        LambdaConstraintExpander.__init__(self, {})
        self._configure()

    def _configure(self):
        self.expand = lambda x: list()


class DictConstraintExpander(LambdaConstraintExpander):

    name = "DictConstraintExpander"
    component_type = __name__

    def __init__(self, config):
        LambdaConstraintExpander.__init__(self, config)
        self._configure()

    def _configure(self):
        file = self.config["dict_constraint_mappings"]
        if isinstance(file, dict):
            self.dict_constraint_mappings = file
        else:
            self.dict_constraint_mappings = load_json_file(file)
        self.expand = lambda clause: self.dict_constraint_mappings.get(
                clause["type"], {}).get(clause["constraint"], [])


class PhoneConstraintExpander(LambdaConstraintExpander):

    name = "PhoneConstraintExpander"
    component_type = __name__

    def __init__(self, config):
        LambdaConstraintExpander.__init__(self, config)
        self._configure()

    def drop_country_code(self, clause):
        if "phone" in clause["type"].lower():
            expanded_values = []
            if len(clause["constraint"]) > 10:
                expanded_values.append(clause["constraint"][-10:])
            if len(clause["constraint"]) > 10 and \
               not clause["constraint"][0] == "+":
                expanded_values.append("+{}".format(clause["constraint"]))
            return expanded_values
        return []

    def _configure(self):
        self.expand = self.drop_country_code


class HeightConstraintExpander(LambdaConstraintExpander):

    name = "HeightConstraintExpander"
    component_type = __name__

    def __init__(self, config):
        LambdaConstraintExpander.__init__(self, config)
        self._configure()

    def safe_parse_int(self, height):
        try:
            return int(height)
        except ValueError:
            return None

    def height_conversion(self, clause):
        if "height" in clause["type"].lower():
            if isinstance(clause["constraint"], int) or self.safe_parse_int(clause["constraint"]):
                height = int(clause["constraint"])
                if height < 100:
                    return [int(round(height * 2.54)), "{}'{}\"".format(height//12, height%12)]
                else:
                    height_in_cm = height
                    height_in_inches = height // 2.54
                    return [height_in_inches, "{}'{}\"".format(height_in_inches//12, height_in_inches%12)]
            if isinstance(clause["constraint"], str):
                height = clause["constraint"]
                try:
                    if "cm" in height:
                        height_just_value = height.replace("cm", "")
                        height_in_cm = int(height_just_value)
                        height_in_inches = int(height_just_value) // 2.54
                        return [height_in_inches, "{}'{}\"".format(height_in_inches//12, height_in_inches%12)]
                    if "inches" in height:
                        height_just_value = height.replace("inches", "")
                        height_in_inches = int(height_just_value)
                        height_in_cm = int(height_just_value * 2.54)
                        return [height_in_cm, "{}'{}\"".format(height//12, height%12)]
                    if "in" in height:
                        height_just_value = height.replace("in", "")
                        height_in_inches = int(height_just_value)
                        height_in_cm = int(height_just_value  // 2.54)
                        return [height_in_cm, "{}'{}\"".format(height//12, height%12)]
                    if "'" in height and "\"" in height:
                        height_components = height.split("'")
                        inches_component = height_components[1].split("\"")[0]
                        height_in_inches = int(height_components[0]) * 12 + inches_component
                        height_in_cm = int(height_in_inches * 2.54)
                        return [height_in_inches, height_in_cm]
                except:
                    return []
        return []

    def _configure(self):
        self.expand = self.height_conversion


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == IdentityConstraintExpander.name:
        return IdentityConstraintExpander()
    elif component_name == DictConstraintExpander.name:
        return DictConstraintExpander(component_config)
    elif component_name == HeightConstraintExpander.name:
        return HeightConstraintExpander(component_config)
    elif component_name == PhoneConstraintExpander.name:
        return PhoneConstraintExpander(component_config)
    else:
        raise ValueError("Unsupported constraint expansion {}".
                         format(component_name))
