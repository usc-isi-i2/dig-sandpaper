from __future__ import unicode_literals
from digsandpaper.sandpaper_utils import load_json_file
import copy
import re
from elasticsearch_dsl import Search, A
from elasticsearch_dsl.query import Match, MatchPhrase, DisMax,\
    Bool, Exists, ConstantScore, Range, FunctionScore, SF

__name__ = "QueryCompiler"
name = __name__


class ElasticsearchQueryCompiler(object):

    name = "ElasticsearchQueryCompiler"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["elasticsearch_compiler_options"]
        if isinstance(file, dict):
            self.elasticsearch_compiler_options = file
        else:
            self.elasticsearch_compiler_options = load_json_file(file)

    def compute_minimum_should_match(self, constraint):
        terms = len(constraint.split(" "))
        terms_msm = self.elasticsearch_compiler_options.get("terms_minimum_should_match", 1)
        if terms > 5:
            msm = terms // 2 + 1
        elif terms > 1:
            msm = max(min(terms, terms_msm), terms // 2)
        else:
            msm = 1
        return msm

    def translate_filter(self, f, field):
        range_operators = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}
        op = f["operator"]
        if isinstance(op, str) and op in range_operators:
            range_params = {}
            range_field_params = {}
            range_field_params[range_operators[op]] = f["constraint"]
            range_params[field["name"]] = range_field_params
            range_field_params["_name"] = "{}:{}:{}".format(f.get("_id"),
                                                            field.get("name"),
                                                            f.get("constraint"))
            return Range(**range_params)
        if not isinstance(op, str) and isinstance(op, list):
            range_params = {}
            range_field_params = {}
            for (o, c) in zip(op, f["constraint"]):
                range_field_params[range_operators[o]] = c
            range_params[field["name"]] = range_field_params
            _name = ""
            for (i, c) in zip(f.get("_id"), f.get("constraint")):
                _name = "{}:{}:{}:{}".format(_name, i,
                                             field.get("name"), c)
            _name = _name[1:]
            range_field_params["_name"] = _name
            return Range(**range_params)
        else:
            match_params = {}
            match_field_params = {}
            if self.elasticsearch_compiler_options.get("boost_text", True):
                match_field_params["boost"] = field.get("weight", 1.0) * 5
            match_field_params["query"] = f["constraint"]
            match_field_params["_name"] = "{}:{}:{}".format(f.get("_id"),
                                                            field.get("name"),
                                                            f.get("constraint"))
            match_params[field["name"]] = match_field_params
            query_type = f.get("query_type", "match")
            if query_type == "match_phrase" and op.lower() != "not in":
                match_params_mp = {}
                match_field_params_mp = copy.copy(match_field_params)
                if self.elasticsearch_compiler_options.get("boost_text", True):
                    match_field_params_mp["boost"] = match_field_params_mp["boost"] * 10
                match_field_params_mp["_name"] = match_field_params_mp["_name"] + ":match_phrase"
                match_params_mp[field["name"]] = match_field_params_mp
                match_field_params_mp["slop"] = 10
                constraint = f.get("constraint")
                if self.elasticsearch_compiler_options.get("boost_text", True):
                    msm = self.compute_minimum_should_match(constraint)
                    match_field_params["minimum_should_match"] = msm
                mp = MatchPhrase(**match_params_mp)
                if self.elasticsearch_compiler_options.get("boost_text", True):
                    if f.get("type", "owl:Thing") == "owl:Thing":
                        match_field_params["boost"] = field.get("weight", 1.0) * 2
                m = Match(**match_params)
                return Bool(must=[m], should=[mp])
            else:
                if op.lower() == "not in":
                    must_nots = []
                    terms = f.get("constraint")
                    for term in terms:
                        match_params_mn = {}
                        match_field_params_mn = copy.copy(match_field_params)
                        match_field_params_mn["query"] = term
                        match_field_params_mn["_name"] = "{}:{}:{}".format(f.get("_id"),
                                                                           field.get("name"),
                                                                           term)
                        match_params_mn[field["name"]] = match_field_params_mn
                        if self.elasticsearch_compiler_options.get("boost_text", True):
                            msm = self.compute_minimum_should_match(term)
                            match_field_params_mn["minimum_should_match"] = msm
                        must_not = Match(**match_params_mn)
                        must_nots.append(must_not)
                    return Bool(must_not=must_nots)
                else:
                    constraint = f.get("constraint")
                    if self.elasticsearch_compiler_options.get("boost_text", True):
                        msm = self.compute_minimum_should_match(constraint)
                        match_field_params["minimum_should_match"] = msm
                        if f.get("type", "owl:Thing") == "owl:Thing":
                            match_field_params["boost"] = field.get("weight", 1.0) * 2
                    return Match(**match_params)

    def translate_clause(self, clause, field):
        if("constraint" in clause):
            match_params = {}
            query_type = clause.get("query_type", "match")
            match_field_params = {}
            match_field_params["query"] = clause["constraint"]
            # match_field_params["type"] = query_type
            match_field_params["boost"] = field.get("weight", 1.0)
            match_field_params["_name"] = "{}:{}:{}".format(clause.get("_id"),
                                                            field.get("name"),
                                                            clause.get("constraint"))
            match_params[field["name"]] = match_field_params
            if query_type == "match_phrase":
                match_params_mp = {}
                match_field_params_mp = copy.copy(match_field_params)
                if self.elasticsearch_compiler_options.get("boost_text", True):
                    match_field_params_mp["boost"] = match_field_params_mp["boost"] *\
                        len(clause.get("constraint").split(" "))
                match_field_params_mp["_name"] = match_field_params_mp["_name"] + ":match_phrase"
                match_params_mp[field["name"]] = match_field_params_mp
                match_field_params_mp["slop"] = 10
                mp = MatchPhrase(**match_params_mp)
                m = Match(**match_params)
                return Bool(must=[m], should=[mp])
            else:
                if "date" in clause.get("type", "owl:Thing").lower():
                    match_field_params.pop("query", None)
                    if re.match("\d\d\d\d-\d\d-\d\d", clause["constraint"]):
                        match_field_params["gte"] = clause["constraint"]
                    else:
                        match_field_params["gte"] = "{}||/d".format(clause["constraint"])
                    match_field_params["lt"] = "{}||+1d/d".format(clause["constraint"])
                    return Range(**match_params)

                if self.elasticsearch_compiler_options.get("boost_text", True):
                    if clause.get("type", "owl:Thing") == "owl:Thing":
                        match_field_params["boost"] = field.get("weight", 1.0) * 2
                # terms = len(clause.get("constraint").split(" "))
                constraint = clause.get("constraint")
                if self.elasticsearch_compiler_options.get("boost_text", True):
                    msm = self.compute_minimum_should_match(constraint)
                    match_field_params["minimum_should_match"] = msm
                return Match(**match_params)
        else:
            return Exists(field=field["name"])

    def clean_dismax(self, query):
        if isinstance(query, dict):
            if "dis_max" in query:
                for i in range(0, len(query["dis_max"]['queries'])):
                    if not isinstance(query["dis_max"]['queries'][i], dict):
                        query["dis_max"]['queries'][i] = query["dis_max"]['queries'][i].to_dict()
            else:
                for key in query:
                    self.clean_dismax(query[key])
        elif isinstance(query, list):
            # need to update in place
            for i in range(len(query)):
                e = query[i]
                self.clean_dismax(e)
                if isinstance(e, DisMax):
                    query[i] = e.to_dict()
        return query

    # have to return source_fields because set union operation produces a new set
    def generate_filter(self, f, filters, must_nots, source_fields):
        if "operator" not in f:
            return source_fields

        operator = f["operator"]
        if isinstance(operator, list) and len(operator) == 1:
            operator = operator[0]
        compound_filter = operator == "and" or operator == "or"
        exists_filter = operator and "exists" in operator
        if "fields" not in f and not compound_filter and not exists_filter:
            return source_fields
        if compound_filter:
            clauses = f["clauses"]
            sub_filters = []
            sub_must_nots = []

            if operator == "and" and len(clauses) > 1:
                clauses_by_variable = {}
                compound_clauses = []
                for clause in clauses:
                    if "variable" in clause:
                        cs = clauses_by_variable.get(clause["variable"], [])
                        cs.append(clause)
                        clauses_by_variable[clause["variable"]] = cs
                    else:
                        compound_clauses.append(clause)

                for (variable, clauses) in clauses_by_variable.items():
                    if len(clauses) == 1:
                        source_fields = self.generate_filter(clauses[0],
                                                             sub_filters,
                                                             sub_must_nots,
                                                             source_fields)
                    else:
                        ops = []
                        constraints = []
                        ids = []
                        for clause in clauses:
                            ops.append(clause["operator"])
                            constraints.append(clause["constraint"])
                            ids.append(clause["_id"])
                        new_clause = {}
                        new_clause["operator"] = ops
                        new_clause["constraint"] = constraints
                        new_clause["_id"] = ids
                        new_clause["type"] = clauses[0]["type"]
                        new_clause["fields"] = clauses[0]["fields"]
                        source_fields = self.generate_filter(new_clause,
                                                             sub_filters,
                                                             sub_must_nots,
                                                             source_fields)
                for clause in compound_clauses:
                    source_fields = self.generate_filter(clause,
                                                         sub_filters,
                                                         sub_must_nots,
                                                         source_fields)
                q = Bool(filter=sub_filters,
                         must_not=sub_must_nots)
            else:
                for clause in clauses:
                    source_fields = self.generate_filter(clause,
                                                         sub_filters,
                                                         sub_must_nots,
                                                         source_fields)
                if operator == "or":
                    q = Bool(should=[ConstantScore(filter=sf)
                                     for sf in sub_filters],
                             must_not=sub_must_nots)
                else:
                    q = sub_filters[0]
            filters.append(q)
        elif exists_filter:
            if "not" not in operator:
                return source_fields
            sub_filters = []
            for clause in f["clauses"]:
                fields = clause["fields"]
                source_fields |= set([field["name"] for field in fields])
                es_clause = self.translate_clause_helper(clause, fields, True)
                must_nots.append(es_clause)
        else:
            source_fields |= set([field["name"] for field in f["fields"]])
            if len(f["fields"]) == 1:
                q = self.translate_filter(f, f["fields"][0])
            else:
                sub_filters = []
                for field in f["fields"]:
                    sub_filters.append(self.translate_filter(f, field))
                if isinstance(f["operator"], list) and len(f["operator"]) > 0:
                    q = Bool(should=sub_filters)
                else:
                    q = DisMax(queries=sub_filters)
            filters.append(q)
        return source_fields

    def generate_source_fields(self, s, source_fields):
        if "default_source_fields" in self.elasticsearch_compiler_options:
            default_source_fields = self.elasticsearch_compiler_options["default_source_fields"]
            if isinstance(default_source_fields, str):
                default_source_fields = [default_source_fields]
            source_fields |= set(default_source_fields)

        if "excluded_source_fields" in self.elasticsearch_compiler_options:
            excluded_source_fields = self.elasticsearch_compiler_options["excluded_source_fields"]
            source_fields = source_fields.difference(excluded_source_fields)
            s = s.source(includes=list(source_fields),
                         excludes=excluded_source_fields)
        else:
            s = s.source(includes=list(source_fields))
        return s

    def generate_query_boilerplate(self, query, s, source_fields):

        select_variables = query["SPARQL"]["select"]["variables"]
        for sv in select_variables:
            if "fields" not in sv:
                continue
            source_fields |= set([field["name"] for field in sv["fields"]])

        s = self.generate_source_fields(s, source_fields)

        if query["type"].lower() == "point fact" and\
           'predicate_scoring_coefficients' in\
           self.elasticsearch_compiler_options:
                psc = self.elasticsearch_compiler_options['predicate_scoring_coefficients']
                functions = []
                for key, value in psc.items():
                    field = "doc['knowledge_graph.{}.key'].value".format(key)
                    sf = SF('script_score', script="_score*{}*{}".format(value, field))
                    functions.append(sf)
                fs = FunctionScore(query=s.query, functions=functions)
                s.query = fs

        limit = 20
        offset = 0

        if "group-by" in query["SPARQL"]:
            if "limit" in query["SPARQL"]["group-by"]:
                limit = int(query["SPARQL"]["group-by"]["limit"])
            if "offset" in query["SPARQL"]["group-by"]:
                offset = int(query["SPARQL"]["group-by"]["offset"])

        if query.get("type", "Point Fact") == "Aggregation":
            s = s.extra(size=0)
        else:
            s = s.extra(size=limit)
            s = s.extra(from_=offset)

        highlight_fields = dict((source_field, {}) for source_field in
                                list(source_fields) if source_field != "raw_content")

        if "highlight" in self.elasticsearch_compiler_options:
            highlight = self.elasticsearch_compiler_options["highlight"]
            for key in highlight["fields"]:
                highlight_fields[key] = highlight["fields"][key]
        for key in highlight_fields:
            s = s.highlight(key, **highlight_fields[key])

        order_by_values = None
        if "order-by" in query["SPARQL"]:
            order_by = query["SPARQL"]["order-by"]
            order_by_values = order_by["values"]

        if query["type"].lower() == "aggregation":
            for sv in select_variables:
                if "function" in sv:
                    asc_or_desc = "desc"
                    order_function = "_count"
                    if order_by_values:
                        order_by_value = order_by_values[0]
                        asc_or_desc = order_by_value.get("order", "asc")
                        if "function" not in order_by_value:
                            order_function = "_term"
                        else:
                            order_function = "_{}".format(order_by_value["function"].lower())
                    order = {order_function: asc_or_desc}

                    a = A('terms', field=sv["fields"][0]["name"],
                          size=limit, order=order)
                    s.aggs.bucket(sv["variable"], a)
        elif query["type"].lower() == "point fact":
            if "order-by" in query["SPARQL"] and \
               "values" in query["SPARQL"]["order-by"]:
                order_by_clauses = []
                for order_by_value in query["SPARQL"]["order-by"]["values"]:
                    asc_or_desc = order_by_value.get("order", "asc")
                    field = order_by_value["fields"][0]["name"]
                    # our fields can be multi valued.
                    # the mode argument allows us to pick one of the values.
                    if asc_or_desc and asc_or_desc == "desc":
                        order_by_clause = {field: {"order": "desc",
                                                   "mode": "max"}}
                    else:
                        order_by_clause = {field: {"order": "asc",
                                                   "mode": "min"}}
                    order_by_clauses.append(order_by_clause)
                s = s.sort(*order_by_clauses)
        return s

    def generate(self, query):
        where = query["SPARQL"]["where"]
        generated = self.generate_where(query, where, True)
        query["ELASTICSEARCH"] = generated
        return query

    def translate_clause_helper(self, clause, fields, use_dist_max):
        if len(fields) == 1:
            es_clause = self.translate_clause(clause, fields[0])
        else:
            sub_queries = []
            for field in clause["fields"]:
                sub_queries.append(self.translate_clause(clause,
                                                         field))
            if use_dist_max:
                es_clause = DisMax(queries=sub_queries)
            else:
                es_clause = Bool(should=sub_queries)

        return es_clause

    def boosting_musts_and_shoulds_enabled(self, musts):
        return self.elasticsearch_compiler_options.get("boost_shoulds", False) or\
            ("boost_musts" in self.elasticsearch_compiler_options and
                len(musts) > 0)

    def should_contains_filter(self, should):
        if isinstance(should, Bool) and len(should.should) > 0:
            filter_count = len([clause for clause in should.should if isinstance(clause, Exists)])
            return filter_count > 0
        return False

    def boost_musts_and_shoulds(self, q, musts, shoulds, filters, must_nots):
        if "boost_musts" in self.elasticsearch_compiler_options\
                and len(musts) == 1:
            shoulds.extend(musts)
            q = Bool(should=shoulds,
                     filter=filters,
                     must_not=must_nots)
        else:
            boost = 10.0
            weighted_by_musts = []
            musts_temp = musts
            if "boost_musts" in self.elasticsearch_compiler_options:
                shoulds.extend(musts)
                musts_temp = []

            filter_count = len([should for should in shoulds if
                                self.should_contains_filter(should)])
            if len(shoulds) == 1 and len(musts) == 0:
                return q

            if len(shoulds) > 0 and len(shoulds) != filter_count:
                extra_minimum_should_match = filter_count

                if len(shoulds) >= 2 and "boost_shoulds"\
                        in self.elasticsearch_compiler_options:
                    extra_minimum_should_match = extra_minimum_should_match +\
                        self.elasticsearch_compiler_options\
                            .get("extra_minimum_should_match", 1)
                for x in range(0,
                               max(1,
                                   len(shoulds) - extra_minimum_should_match)):
                    weighted_q = Bool(
                        should=shoulds,
                        boost=boost,
                        minimum_should_match=len(shoulds) - x)
                    weighted_by_musts.append(weighted_q)
                    boost = boost / 2
                if len(musts_temp) > 0:
                    boosted_shoulds_minimum_should_match = 0
                else:
                    boosted_shoulds_minimum_should_match = 1
                weighted_must = Bool(should=weighted_by_musts,
                                     minimum_should_match=boosted_shoulds_minimum_should_match,
                                     disable_coord=True,
                                     filter=filters,
                                     must=musts_temp,
                                     must_not=must_nots)
                q = weighted_must
        return q

    def filter_contains_clause(self, obj, clause_id):
        contains_clause = False
        for (k, v) in obj.items():
            if isinstance(v, str):
                if v.startswith(clause_id):
                    return True
            elif isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        contains_clause |= self.filter_contains_clause(e, clause_id)
            elif isinstance(v, dict):
                contains_clause |= self.filter_contains_clause(v, clause_id)

            if contains_clause:
                return contains_clause
        return contains_clause

    def generate_subquery(self, query, where, clause):
        sub_query = self.generate_where(query, clause, False)
        sub_query["clause_fields"] = []
        sub_query["unbound_subquery_variables"] = []
        sub_query["variable_to_agg_field"] = {}
        sub_query["predicate_to_constraints"] = {}
        sub_query["variable_to_predicate"] = {}
        # if sub_query contains variable of parent query
        #  create clause that filters on variable of parent query

        for c in clause["clauses"]:
            if "variable" in c:
                if c["variable"] != where["variable"]:
                    sub_query["unbound_subquery_variables"].append(c["variable"])
                    sub_query["variable_to_agg_field"][c["variable"]] = c["agg_fields"][0]["name"]
                    sub_query["variable_to_predicate"][c["variable"]] = c["predicate"]
                    for f in c["fields"]:
                        if not f["name"].startswith("content") and not f["name"] == "raw_content":
                            sub_query["clause_fields"].append({"name": f["name"],
                                                               "variable": c["variable"]})
            elif "constraint" in c:
                if c["predicate"] not in sub_query["predicate_to_constraints"]:
                    sub_query["predicate_to_constraints"][c["predicate"]] = list()
                sub_query["predicate_to_constraints"][c["predicate"]].append(c["constraint"])
            elif "operator" in c:
                if c["operator"] == "union":
                    for uc in c["clauses"]:
                        if uc["predicate"] not in sub_query["predicate_to_constraints"]:
                            sub_query["predicate_to_constraints"][uc["predicate"]] = list()
                        sub_query["predicate_to_constraints"][uc["predicate"]].\
                            append(uc["constraint"])
        sub_query["search"]

        unbound_subquery_filter_excludes = {}
        clauses_to_remove = []
        if "filters" in clause:
            for f in clause["filters"]:
                if "variable" in f:
                    if f["variable"] in sub_query["unbound_subquery_variables"]:
                        unbound_subquery_filter_excludes[f["variable"]] = f["constraint"]
                        clauses_to_remove.append(f["_id"])
            filters_to_remove = []
            for f in sub_query["search"]["query"]["bool"]["filter"]:
                for clause_to_remove in clauses_to_remove:
                    if self.filter_contains_clause(f, clause_to_remove):
                        filters_to_remove.append(f)

            filters_to_keep = [f for f in sub_query["search"]["query"]["bool"]["filter"] if
                               f not in filters_to_remove]

            sub_query["search"]["query"]["bool"]["filter"] = filters_to_keep

        s = Search().from_dict(sub_query["search"])
        # find filters with unbound subquery variables
        # if filters with unbound subquery variable, remove it from the list of filters
        # take the terms and add it to the matching unbound subquery variables' aggregation excludes
        for unbound_variable in sub_query["unbound_subquery_variables"]:
            if "exclude" in unbound_variable:
                continue
            exclude = list()
            exclude.extend(unbound_subquery_filter_excludes.get(unbound_variable, []))
            exclude.extend(sub_query["predicate_to_constraints"]
                           .get(sub_query["variable_to_predicate"][unbound_variable], []))
            exclude = "|".join([e + ("(:.*)?") for e in exclude])
            a = A('significant_terms',
                  field=sub_query["variable_to_agg_field"][unbound_variable],
                  size=5, exclude=exclude)
            s.aggs.bucket(unbound_variable, a)

        sub_query["search"] = self.clean_dismax(s.to_dict())
        return sub_query

    def generate_placeholder_for_subquery_values(self, clause,
                                                 where, sub_query):
        contains_parent_variable = False
        for c in clause["clauses"]:
            if "variable" in c:
                if c["variable"] == where["variable"]:
                    contains_parent_variable = True
        if contains_parent_variable:
            sub_query_clause = {}
            sub_query_clause["constraint"] = "__placeholder__"
            sub_query_clause["isOptional"] = False
            sub_query_clause["fields"] = where["fields"]
            # source_fields |= set([field["name"] for field in where["fields"]])
            sub_query_clause["_id"] = clause["_id"]
            es_clause = self.translate_clause_helper(sub_query_clause,
                                                     where["fields"],
                                                     True)
            sub_query["clause_fields"] = where["fields"]
            sub_query["clause_id"] = clause["_id"]
        else:
            es_clause = None
        return es_clause

    def generate_where_union_helper(self, clause, musts, source_fields):
        union_shoulds = []
        for uc in clause["clauses"]:
            fields = uc["fields"]
            source_fields |= set([field["name"] for field in fields])
            if "constraint" in uc:
                es_clause = self.translate_clause_helper(uc, fields, True)
                union_shoulds.append(es_clause)
        if union_shoulds:
            union_q = Bool(should=union_shoulds)
            musts.append(union_q)
        return source_fields

    def generate_where(self, query, where, is_root=False):

        where_clauses = where["clauses"]
        source_fields = set()

        musts = []
        shoulds = []
        filters = []
        must_nots = []

        sub_queries = []

        shoulds_by_predicate = {}

        for clause in where_clauses:
            if "operator" in clause:
                # currently unions only suport a single clause
                # and object must be bound
                if "union" == clause["operator"].lower():
                    source_fields = self.generate_where_union_helper(clause,
                                                                     musts,
                                                                     source_fields)
                    continue
                else:
                    continue
            if "fields" in clause:
                fields = clause["fields"]
                source_fields |= set([field["name"] for field in fields])
            if("constraint" in clause):
                es_clause = self.translate_clause_helper(clause, fields, True)
            elif "clauses" in clause:
                sub_query = self.generate_subquery(query,
                                                   where,
                                                   clause)
                es_clause = self.generate_placeholder_for_subquery_values(clause,
                                                                          where,
                                                                          sub_query)
                sub_queries.append(sub_query)
            else:
                # this is a we need an answer for this clause
                if "filter_for_fields_of_unbound_variables" \
                   not in self.elasticsearch_compiler_options or \
                   self.elasticsearch_compiler_options["filter_for_fields_of_unbound_variables"]:
                    es_clause = self.translate_clause_helper(clause, fields, False)
                else:
                    es_clause = None
            if es_clause:
                if clause.get("isOptional", False):
                    predicate = clause.get("predicate")
                    if predicate not in shoulds_by_predicate:
                        shoulds_by_predicate[predicate] = list()
                    shoulds_by_predicate.get(predicate).append(es_clause)
                else:
                    musts.append(es_clause)

        for sub_query in sub_queries:
            if not sub_query["unbound_subquery_variables"]:
                continue
            unbound_subquery_variables = sub_query["unbound_subquery_variables"]
            sub_query["variable_to_clause_id"] = {}
            for clause in where_clauses:
                if "operator" in clause:
                    if "union" == clause["operator"].lower():
                        union_shoulds = []
                        for uc in clause["clauses"]:
                            if "variable" in uc and uc["variable"] in unbound_subquery_variables:
                                uc["constraint"] = "__placeholder__"
                            uc_es_clause = self.translate_clause_helper(uc,
                                                                        uc["fields"],
                                                                        True)
                            if "variable" in uc:
                                if uc["variable"] not in sub_queries[-1]["variable_to_clause_id"]:
                                    sub_query["variable_to_clause_id"][uc["variable"]] = []
                                sq_vtci = sub_query["variable_to_clause_id"]
                                variable_to_clause_id = sq_vtci[uc["variable"]]
                                variable_to_clause_id.append(uc["_id"])
                                union_shoulds.append(uc_es_clause)
                        if union_shoulds:
                            union_q = Bool(should=union_shoulds)
                            musts.append(union_q)

                elif "constraint" not in clause and "clauses" not in clause:
                    if "variable" in clause and clause["variable"] in unbound_subquery_variables:
                        clause["constraint"] = "__placeholder__"
                        es_clause = self.translate_clause_helper(clause,
                                                                 clause["fields"],
                                                                 True)
                        if clause["variable"] not in sub_queries[-1]["variable_to_clause_id"]:
                            sub_query["variable_to_clause_id"][clause["variable"]] = []
                        sq_vtci = sub_query["variable_to_clause_id"]
                        variable_to_clause_id = sq_vtci[clause["variable"]]
                        variable_to_clause_id.append(clause["_id"])
                        # filter for performance reasons
                        musts.append(es_clause)

        for key, value in shoulds_by_predicate.items():
            if len(value) > 1:
                shoulds.append(DisMax(queries=value))
            else:
                shoulds.append(value[0])

        if "filters" in where:
            filter_clauses = where["filters"]
            for f in filter_clauses:
                source_fields = self.generate_filter(f, filters,
                                                     must_nots, source_fields)

        if self.elasticsearch_compiler_options.get("convert_text_filters_to_shoulds", False):
            valid_filters = list()
            converted_filters = list()
            for f in filters:
                is_matches = False
                if isinstance(f, DisMax):
                    is_matches = True
                    for q in f.queries:
                        if isinstance(q, Range):
                            is_matches = False
                        if isinstance(q, Bool) and q.must_not:
                            is_matches = False
                        break
                if is_matches:
                    converted_filters.append(f)
                else:
                    valid_filters.append(f)

            shoulds.extend(converted_filters)
            filters = valid_filters

        if len(musts) > 0 or not shoulds:
            msm = 0
        else:
            msm = 1

        q = Bool(must=musts,
                 should=shoulds,
                 filter=filters,
                 must_not=must_nots,
                 minimum_should_match=msm)
        if self.boosting_musts_and_shoulds_enabled(musts):
            q = self.boost_musts_and_shoulds(q, musts, shoulds,
                                             filters, must_nots)

        s = Search()
        s.query = q
        if is_root:
            s = self.generate_query_boilerplate(query, s, source_fields)
        else:
            s = self.generate_source_fields(s, source_fields)
        es_result = {}
        es_result["search"] = self.clean_dismax(s.to_dict())
        es_result["type"] = where["type"]
        if len(sub_queries) > 0:
            sub_queries.append(es_result)
            return sub_queries
        return es_result


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ElasticsearchQueryCompiler.name:
        return ElasticsearchQueryCompiler(component_config)
    else:
        raise ValueError("Unsupported query compiler component {}".
                         format(component_name))
