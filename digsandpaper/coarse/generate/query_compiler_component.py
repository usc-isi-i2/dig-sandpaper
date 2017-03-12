import json
import codecs
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import MultiMatch, Match, DisMax, Bool, Exists, ConstantScore, Range

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
            return Range(**range_params)
        else:
            match_params = {}
            match_field_params = {}
            match_field_params["query"] = f["constraint"]
            #match_field_params["type"] = f.get("query_type", "phrase")
            match_params[field["name"]] = match_field_params
            return Match(**match_params)

    def translate_clause(self, clause, field):
        if("constraint" in clause):
            match_params = {}
            query_type = clause.get("query_type", "phrase")
            match_field_params = {}
            match_field_params["query"] = clause["constraint"]
            #match_field_params["type"] = query_type
            match_field_params["boost"] = field.get("weight", 1.0)
            match_params[field["name"]] = match_field_params
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

        compound_filter = f["operator"] == "and" or f["operator"] == "or"
        if "fields" not in f and not compound_filter:
            return source_fields
        if compound_filter:
            clauses = f["clauses"]
            sub_filters = []
            for clause in clauses:
                source_fields = self.generate_filter(clause,
                                                     sub_filters,
                                                     source_fields)
            if f["operator"] == "and":
                q = Bool(filter=sub_filters)
            elif f["operator"] == "or":
                q = Bool(should=[ConstantScore(filter=sf)
                                 for sf in sub_filters])
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

    def generate(self, query):
        where = query["SPARQL"]["where"]
        where_clauses = where["clauses"]
        filter_clauses = where["filters"]
        select_variables = query["SPARQL"]["select"]["variables"]

        source_fields = set()

        musts = []
        shoulds = []
        filters = []
        must_nots = []

        for clause in where_clauses:
            if "fields" not in clause:
                # todo everything should have fields fields
                continue
            fields = clause["fields"]

            source_fields |= set([field["name"] for field in fields])
            if("constraint" in clause):
                if len(fields) == 1:
                    es_clause = self.translate_clause(clause, fields[0])
                else:
                    sub_queries = []
                    for field in clause["fields"]:
                        sub_queries.append(self.translate_clause(clause,
                                                                 field))
                    es_clause = DisMax(queries=sub_queries)
            else:
                if len(fields) == 1:
                    es_clause = self.translate_clause(clause, fields[0])
                else:
                    sub_queries = []
                    for field in clause["fields"]:
                        sub_queries.append(self.translate_clause(clause,
                                                                 field))
                    es_clause = Bool(should=sub_queries)
            if clause.get("isOptional", False):
                shoulds.append(es_clause)
            else:
                musts.append(es_clause)

        for f in filter_clauses:
            source_fields = self.generate_filter(f, filters, source_fields)

        for s in select_variables:
            if "fields" not in s:
                continue
            source_fields |= set([field["name"] for field in s["fields"]])

        q = Bool(must=musts,
                 should=shoulds,
                 filter=filters,
                 must_not=must_nots)
        if "boost_musts" in self.elasticsearch_compiler_options:
            q1 = Bool(must=musts,
                      should=shoulds,
                      filter=filters,
                      must_not=must_nots)
            q2 = Bool(must=musts + shoulds,
                      filter=filters,
                      must_not=must_nots,
                      boost=self.elasticsearch_compiler_options["boost_musts"])
            weighted_must = Bool(should=[q1, q2])
            q = weighted_must

        s = Search()
        s.query = q
        if "default_source_fields" in self.elasticsearch_compiler_options:
            default_source_fields = self.elasticsearch_compiler_options["default_source_fields"]
            if isinstance(default_source_fields, basestring):
                default_source_fields = [default_source_fields]
            source_fields |= set(default_source_fields)

        s = s.source(includes=list(source_fields))
        if "group-by" in query["SPARQL"]:
            if "limit" in query["SPARQL"]["group-by"]:
                s = s.extra(size=int(query["SPARQL"]["group-by"]["limit"]))

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

        if "ELASTICSEARCH" not in query:
            query["ELASTICSEARCH"] = {}
        query["ELASTICSEARCH"]["search"] = self.clean_dismax(s.to_dict())

        return query


def get_component(component_config):
    component_name = component_config["name"]
    if component_name == ElasticsearchQueryCompiler.name:
        return ElasticsearchQueryCompiler(component_config)
    else:
        raise ValueError("Unsupported query compiler component {}".
                         format(component_name))
