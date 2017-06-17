import json
import codecs
import copy
import uuid
from jsonpath_rw_ext import parse

__name__ = "ConstraintExpansion"
name = __name__

def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


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

    def preprocess_clauses(self, where):
        where_clauses = where["clauses"]
        
        new_where_clauses = list()
        
        for clause in where_clauses:
            if "constraint" not in clause:
                if "clauses" in clause:
                    self.preprocess_clauses(clause)
                continue
            expanded_values = self.expand(clause)
            for expanded_value in expanded_values:
                new_clause = copy.copy(clause)
                new_clause["constraint"] = expanded_value
                new_clause["isOptional"] = True
                new_clause["_id"] = uuid.uuid4().hex
                new_where_clauses.append(new_clause)
        where_clauses.extend(new_where_clauses)

    def preprocess(self, query):
        where = query["SPARQL"]["where"]

        if "clauses" in where:
            self.preprocess_clauses(where)
        
        if "filters" in where:
            filters = where["filters"]
            where["filters"] = [self.preprocess_filter(f) for f in filters]

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

    def height_conversion(self, clause):
        if "height" in clause["type"].lower():
            if isinstance(clause["constraint"], int):
                height = clause["constraint"]
                if height < 100:
                    return [int(height * 2.54), "{}'{}\"".format(height//12, height%12)]
                else:
                    height_in_cm = height
                    height_in_inches = height // 2.54
                    return [height_in_inches, "{}'{}\"".format(height_in_inches//12, height_in_inches%12)]
            if isinstance(clause["constraint"], basestring):
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
