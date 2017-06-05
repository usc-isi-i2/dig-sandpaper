import json
import codecs
import random
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
from elasticsearch_dsl.query import MultiMatch, Match, MatchPhrase, DisMax, Bool, Exists, ConstantScore, Range

__name__ = "QueryCompiler"
name = __name__


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


class ElasticsearchQueryCompiler(object):

    name = "ElasticsearchQueryCompiler"
    component_type = __name__

    def __init__(self, config):
        self.config = config
        self._configure()

    def _configure(self):
        file = self.config["elasticsearch_compiler_options"]
        self.elasticsearch_compiler_options = load_json_file(file)

    def translate_filter(self, f, field):
        range_operators = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}
        op = f["operator"]
        if op in range_operators:
            range_params = {}
            range_field_params = {}
            range_field_params[range_operators[op]] = f["constraint"]
            range_params[field["name"]] = range_field_params
            range_field_params["_name"] = "{}:{}:{}".format(f.get("_id"),
                                                            field.get("name"),
                                                            f.get("constraint"))
            return Range(**range_params)
        else:
            match_params = {}
            match_field_params = {}
            match_field_params["boost"] = field.get("weight", 1.0) * 5
            match_field_params["query"] = f["constraint"]
            match_field_params["_name"] = "{}:{}:{}".format(f.get("_id"),
                                                            field.get("name"),
                                                            f.get("constraint"))
            match_params[field["name"]] = match_field_params
            query_type = f.get("query_type", "match")
            if query_type == "match_phrase":
                match_field_params["slop"] = 25
                return MatchPhrase(**match_params)
            else: 
                match_field_params["minimum_should_match"] = max(1, len(f.get("constraint").split(" "))/2)
                return Match(**match_params)

    def translate_clause(self, clause, field):
        if("constraint" in clause):
            match_params = {}
            query_type = clause.get("query_type", "match")
            match_field_params = {}
            match_field_params["query"] = clause["constraint"]
            #match_field_params["type"] = query_type
            match_field_params["boost"] = field.get("weight", 1.0)
            match_field_params["_name"] = "{}:{}:{}".format(clause.get("_id"),
                                                            field.get("name"),
                                                            clause.get("constraint"))
            match_params[field["name"]] = match_field_params
            if query_type == "match_phrase":
                match_field_params["slop"] = 25
                return MatchPhrase(**match_params)
            else:
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
            for e in query:
                self.clean_dismax(e)
        return query

    # have to return source_fields because set union operation produces a new set
    def generate_filter(self, f, filters, source_fields):
        if "operator" not in f:
            return source_fields

        operator = f["operator"]
        if isinstance(operator, list) and len(operator) == 1:
            operator = operator[0]
        compound_filter = operator == "and" or operator == "or"
        if "fields" not in f and not compound_filter:
            return source_fields
        if compound_filter:
            clauses = f["clauses"]
            sub_filters = []
            for clause in clauses:
                source_fields = self.generate_filter(clause,
                                                     sub_filters,
                                                     source_fields)
            if operator == "and" and len(sub_filters) > 1:
                q = Bool(filter=sub_filters)
            elif operator == "or":
                q = Bool(should=[ConstantScore(filter=sf)
                                 for sf in sub_filters])
            else:
                q = sub_filters[0]
            filters.append(q)
        else:
            source_fields |= set([field["name"] for field in f["fields"]])
            if len(f["fields"]) == 1:
                filters.append(self.translate_filter(f, field))
            else:
                sub_filters = []
                for field in f["fields"]:
                    sub_filters.append(self.translate_filter(f, field))
                q = DisMax(queries=sub_filters)
                filters.append(q)
        return source_fields

    def generate_query_boilerplate(self, query, s, source_fields):

        select_variables = query["SPARQL"]["select"]["variables"]
        for sv in select_variables:
            if "fields" not in sv:
                continue
            source_fields |= set([field["name"] for field in sv["fields"]])

        if "default_source_fields" in self.elasticsearch_compiler_options:
            default_source_fields = self.elasticsearch_compiler_options["default_source_fields"]
            if isinstance(default_source_fields, basestring):
                default_source_fields = [default_source_fields]
            source_fields |= set(default_source_fields)

        if "excluded_source_fields" in self.elasticsearch_compiler_options:
            excluded_source_fields = self.elasticsearch_compiler_options["excluded_source_fields"]
            source_fields = source_fields.difference(excluded_source_fields)
            s = s.source(includes=list(source_fields), excludes=excluded_source_fields)
        else:
            s = s.source(includes=list(source_fields))

        limit = 20
        if "group-by" in query["SPARQL"]:
            if "limit" in query["SPARQL"]["group-by"]:
                limit = int(query["SPARQL"]["group-by"]["limit"])
                s = s.extra(size=limit)

            if "offset" in query["SPARQL"]["group-by"]:
                s = s.extra(from_=int(query["SPARQL"]["group-by"]["offset"]))
            else:
                s = s.extra(from_=0)

        highlight_fields = dict((source_field, {}) for source_field in list(source_fields))

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
                    variable = sv["variable"]

                    asc_or_desc = "desc"
                    order_function = "_count"
                    if order_by_values:
                        order_by_value = order_by_values[0]
                        asc_or_desc = order_by_value.get("order", "asc")
                        if "function" not in order_by_value:
                            order_function = "_term" 
                        else:
                            order_function = "_{}".format(order_by_value["function"].lower())
                    order = { order_function : asc_or_desc }
                    
                    a = A('terms', field=sv["fields"][0]["name"], 
                          size=limit, order=order)
                    s.aggs.bucket(sv["variable"], a)
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
            if "fields" not in clause:
                # todo everything should have fields fields
                continue
            fields = clause["fields"]

            source_fields |= set([field["name"] for field in fields])
            if("constraint" in clause):
                es_clause = self.translate_clause_helper(clause, fields, True)
            elif "clauses" in clause:
                sub_query = self.generate_where(query, clause, False)
                # if sub_query contains variable of parent query
                #  create clause that filters on variable of parent query
                sub_query_clause = {}
                sub_query_clause["constraint"] = "__placeholder__"
                sub_query_clause["isOptional"] = False
                sub_query_clause["fields"] = where["fields"]
                source_fields |= set([field["name"] for field in where["fields"]])
                sub_query_clause["_id"] = clause["_id"]
                es_clause = self.translate_clause_helper(sub_query_clause, where["fields"], True)
                
                sub_query["clause_fields"] = where["fields"]
                sub_query["clause_id"] = clause["_id"]
                sub_queries.append(sub_query)
                # else 
                #   create clause that's constrained on variable of clause
                #clause["constraint"] = "__placeholder__"
                #es_clause = self.translate_clause_helper(clause, fields, True)
                #sub_query["clause_name"] = es_clause["_name"]
            else:
                es_clause = self.translate_clause_helper(clause, fields, False)
            if clause.get("isOptional", False):
                predicate = clause.get("predicate")
                if not predicate in shoulds_by_predicate:
                    shoulds_by_predicate[predicate] = list()
                shoulds_by_predicate.get(predicate).append(es_clause)
            else:
                musts.append(es_clause)

        for key, value in shoulds_by_predicate.iteritems():
            if len(value) > 1:
                shoulds.append(DisMax(queries=value))
            else:
                shoulds.append(value[0])


        if "filters" in where: 
            filter_clauses = where["filters"]
            for f in filter_clauses:
                source_fields = self.generate_filter(f, filters, source_fields)

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
                        break
                if is_matches:
                    converted_filters.append(f)
                else:
                    valid_filters.append(f)

            shoulds.extend(converted_filters)
            filters= valid_filters
        q = Bool(must=musts,
                 should=shoulds,
                 filter=filters,
                 must_not=must_nots)
        if "boost_musts" in self.elasticsearch_compiler_options:
            boost = 10.0
            weighted_by_musts = []
            minimum_should_match = len(shoulds)
            if minimum_should_match > 0:
                for x in range(0, len(shoulds)):
                    weighted_q = Bool(must=musts,
                          should=shoulds,
                          filter=filters,
                          must_not=must_nots,
                          boost=boost,
                          minimum_should_match=minimum_should_match - x)
                    weighted_by_musts.append(weighted_q)
                    boost = boost / 2
                weighted_must = Bool(should=weighted_by_musts, disable_coord=True)
                q = weighted_must

        s = Search()
        s.query = q
        if is_root:
            s = self.generate_query_boilerplate(query, s, source_fields)
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
