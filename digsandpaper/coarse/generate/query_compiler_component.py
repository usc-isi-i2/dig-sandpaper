import json
import codecs
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import MultiMatch, Match, DisMax, Bool, Exists

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
            match_field_params["boost"] = clause.get("weight", 1.0)
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
            if "fields" not in f:
                continue
            source_fields |= set([field["name"] for field in f["fields"]])
            for field in f["fields"]:
                filters.append(self.translate_filter(f, field))

        for s in select_variables:
            if "fields" not in s:
                continue
            source_fields |= set([field["name"] for field in s["fields"]])

        s = Search()
        s.query = Bool(must=musts,
                       should=shoulds,
                       filter=filters,
                       must_not=must_nots)
        s = s.source(include=list(source_fields))
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
