from __future__ import unicode_literals
from flask import Flask
from flask import request
from flask_api import status
from flask_cors import CORS, cross_origin
import gzip
import os
import json
import requests
from io import StringIO
from io import BytesIO
import codecs
from math import log
from .engine import Engine
from .elasticsearch_mapping.generate import generate_from_project_config
from .elasticsearch_mapping.generate import generate_from_etk_config
from .elasticsearch_indexing.index_knowledge_graph import index_knowledge_graph_fields
from urllib.parse import unquote
from urllib.parse import urlparse
from copy import deepcopy
from .sandpaper_utils import load_json_file

app = Flask(__name__)
CORS(app, supports_credentials=True)
engine = None
project_engines = {}
current_project = "static"

_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def load_project_json_file(file_name):
    with codecs.open(os.path.join(_location__, file_name),
                     'r', 'utf-8') as json_file:
        file = json.load(json_file)
        return file


def get_engine(project=None):
    global engine
    global project_engines
    if not project:
        if engine:
            return engine
        else:
            import sys
            c = load_json_file(sys.argv[11])
            engine = Engine(c)
            set_engine(engine)
            return engine
    else:
        if project in project_engines:
            return project_engines.get(project)
        else:
            raise ValueError("project {} has not been configured yet\n".format(project))


def get_default_es_endpoint(project=None):
    global project_engines
    if project and project not in project_engines:
        project = None
    execute_component = get_engine(project).config["coarse"]["execute"]["components"][0]
    if "endpoints" in execute_component:
        default_es_endpoint = execute_component["endpoints"]
    if "host" in execute_component and "port" in execute_component:
        default_es_endpoint = ["http://{}:{}".format(execute_component["host"],
                                                     execute_component["port"])]
    return default_es_endpoint


@app.route("/")
def hello():
    return "DIG Sandpaper\n"


def post_url(url, data):
    url = unquote(url)
    parsed_url = urlparse(url)
    # for some reason requests is ignoring usernames and passwords in urls
    if parsed_url.username:
        response = requests.post(url, auth=(parsed_url.username, parsed_url.password), data=data)
    else:
        response = requests.post(url, data=data)
    return response


def put_url(url, data):
    url = unquote(url)
    parsed_url = urlparse(url)
    # for some reason requests is ignoring usernames and passwords in urls
    if parsed_url.username:
        response = requests.put(url, auth=(parsed_url.username, parsed_url.password), data=data)
    else:
        response = requests.put(url, data=data)
    return response


def get_url(url):
    url = unquote(url)
    parsed_url = urlparse(url)
    # for some reason requests is ignoring usernames and passwords in urls
    if parsed_url.username:
        response = requests.get(url, auth=(parsed_url.username, parsed_url.password))
    else:
        response = requests.get(url)
    return response


def get_project_config(url, project):
    if url and project:
        response = get_url('{}/projects/{}'.format(url, project))
    elif url and not project:
        response = get_url(url)
    elif not url and project:
        response = get_url('{}/projects/{}'.format('http://localhost:12497', project))
    else:
        return "Please provide either a url or mydig url and project to get a project config\n",
        status.HTTP_400_BAD_REQUEST

    project_config = response.json()
    response.raise_for_status()
    return project_config


def call_generate_mapping(url, project, project_config=None, shards=5):
    if not project_config:
        project_config = get_project_config(url, project)
    return generate_from_project_config(project_config, shards=shards)


def call_generate_mapping_from_etk_config(etk_config, shards=5):
    return generate_from_etk_config(etk_config, shards=shards)


@app.route("/mapping/generate/etk", methods=['POST'])
def generate_mapping_from_etk():
    shards = request.args.get('shards', 5)
    etk_config = request.json
    m = call_generate_mapping_from_etk_config(etk_config, shards=shards)
    return json.dumps(m)


@app.route("/mapping/generate", methods=['GET'])
def generate_mapping():
    url = request.args.get('url', None)
    project = request.args.get('project', None)
    shards = request.args.get('shards', 5)
    if request.data:
        project_config = request.json
    else:
        project_config = get_project_config(url, project)
    m = call_generate_mapping(url, project, project_config, shards=shards)
    return json.dumps(m)


@app.route("/mapping", methods=['PUT', 'POST'])
def add_mapping():
    shards = request.args.get('shards', 5)
    url = request.args.get('url', None)
    project = request.args.get('project', None)
    etk = request.args.get('etk', False)
    if etk:
        etk_config = request.json
        m = call_generate_mapping_from_etk_config(etk_config, shards=shards)
        index = request.args.get('index', None)
        if not index:
            return "Please provide an index to create for the mapping \n",\
                   status.HTTP_400_BAD_REQUEST
    else:
        if request.data:
            project_config = request.json
        else:
            project_config = get_project_config(url, project)
        m = call_generate_mapping(url, project, project_config, shards=shards)
        index = request.args.get('index', project_config["index"]["full"])
    if 'endpoint' in request.args:
        endpoint = request.args.get('endpoint')
    else:
        endpoint = get_default_es_endpoint(project)
    if not isinstance(endpoint, str):
        endpoint = endpoint[0]
    response = put_url('{}/{}'.format(endpoint, index),
                       data=json.dumps(m))
    response.raise_for_status()
    return "index {} added for project {}\n".format(index, project)


def jl_file_iterator(file):
    line = file.readline()
    while line:
        document = json.loads(line)
        yield document
        line = file.readline()


def _is_acceptable_content_type(request):
    return ('Content-Type' in request.headers and
            request.headers['Content-Type'] == 'application/x-gzip' or
            request.headers['Content-Type'] == 'application/json' or
            request.headers['Content-Type'] == 'application/x-jsonlines')


def _index_fields(request):
    if (request.headers['Content-Type'] == 'application/x-gzip'):
        gz_data_as_file = BytesIO(request.data)
        uncompressed = gzip.GzipFile(fileobj=gz_data_as_file, mode='rb')
        jls = uncompressed.read()
    elif (request.headers['Content-Type'] == 'application/json' or
          request.headers['Content-Type'] == 'application/x-jsonlines'):
        jls = request.data
    else:
        return ""
    reader = codecs.getreader('utf-8')
    jls_as_file = reader(BytesIO(jls))
    jls = [json.dumps(jl) for jl in [index_knowledge_graph_fields(jl)
                                     for jl in jl_file_iterator(jls_as_file)]
           if jl is not None]
    return jls


@app.route("/indexing/fields", methods=['POST'])
def index_fields():
    if not _is_acceptable_content_type(request):
        return "Only supported content types are {} {} and {}".format('application/x-gzip',
                                                                      'application/json',
                                                                      'application/x-jsonlines'),
        status.HTTP_400_BAD_REQUEST

    jls = _index_fields(request)
    indexed_jls = "\n".join(jls)
    if (request.headers['Content-Type'] == 'application/x-gzip'):
        indexed_jls_as_file = StringIO()
        compressed = gzip.GzipFile(mode='wb',
                                   fileobj=indexed_jls_as_file)
        compressed.write(indexed_jls)
        compressed.close()
        return indexed_jls_as_file.getvalue()
    else:
        return indexed_jls


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


@app.route("/indexing", methods=['POST'])
def index():
    project = request.args.get('project', None)
    endpoint = request.args.get('endpoint', get_default_es_endpoint(project))
    if not isinstance(endpoint, str):
        endpoint = endpoint[0]
    index = request.args.get('index', None)
    t = request.args.get('type', "ads")
    if not _is_acceptable_content_type(request):
        return "Only supported content types are {} {} and {}".format('application/x-gzip',
                                                                      'application/json',
                                                                      'application/x-jsonlines'),
        status.HTTP_400_BAD_REQUEST

    jls = _index_fields(request)
    log_requests = get_engine(project).config.get("indexing", {}).get("log_requests", None)
    if log_requests:
        with open(os.path.join(log_requests, "indexing.{}.jl".format(index)), "a") as myfile:
            for jl in jls:
                myfile.write(jl + '\n')
    url = "{}/{}/{}/_bulk".format(endpoint, index, t)
    counter = 0
    failed = 0
    successful = 0
    # this is inefficent
    for chunk in chunker(jls, 100):
        bulk_request = ""
        bulk_request_format = '{"index":{}}\n'
        for c in chunk:
            doc_id = json.loads(c).get("doc_id", None)
            if doc_id:
                doc_request = '{"index":{"_id":"' + doc_id + '"}}\n' + c + '\n'
            else:
                doc_request = bulk_request_format + c + '\n'
            bulk_request = bulk_request + doc_request
        counter += len(chunk)
        r = post_url(url, bulk_request)
        bulk_response = r.json()
        for doc_response in bulk_response.get("items", []):
            index_response = doc_response.get("index", {})
            failed = index_response.get("_shards", {}).get("failed", 0)
            successful = index_response.get("_shards", {}).get("successful", 0)
        log_responses = get_engine(project).config.get("indexing", {}).get("log_responses", None)
        if log_responses:
            with open(os.path.join(log_responses,
                                   "indexing.{}.responses.jl".format(index)),
                      "a") as myfile:
                myfile.write(json.dumps(bulk_response))
                myfile.write("\n")

    return "Posted {} documents. {} successful. {} failed.\n".format(counter, successful, failed)


@app.route("/search", methods=['POST'])
def search():
    project = request.args.get("project", None)
    query = request.json
    (qs, rs) = get_engine(project).execute_coarse(query)
    answers = get_engine(project).execute_fine(qs, rs)
    return json.dumps(answers)


def coarse_results_to_dict(r):
    if isinstance(r, list):
        return [rr.to_dict() for rr in r]
    else:
        return r.to_dict()


@app.route("/search/coarse", methods=['POST'])
def coarse():
    project = request.args.get("project", None)
    query = request.json
    log_requests = get_engine(project).config.get("coarse", {}).get("log_requests", None)
    if log_requests:
        with open(os.path.join(log_requests,
                               "coarse.{}.jl".format(current_project)),
                  "a") as myfile:
            myfile.write(json.dumps(query) + '\n')
    (qs, rs) = get_engine(project).execute_coarse(query)
    qs_with_rs = [{"query": q, "result": coarse_results_to_dict(r)} for q, r in zip(qs, rs)]
    return json.dumps(qs_with_rs)


@app.route("/search/coarse/generate", methods=['POST'])
def coarse_generate():
    project = request.args.get("project", None)
    query = request.json
    qs = get_engine(project).generate_coarse(query)
    return json.dumps(qs)


@app.route("/search/fine", methods=['POST'])
def fine():
    return "Hello World!\n"


def set_engine(e, project=None):
    global engine
    engine = e
    if project:
        global project_engines
        if project in project_engines:
            old_e = project_engines[project]
            project_engines[project] = e
            old_e.teardown()
        else:
            project_engines[project] = e


def multiply_values(w, multiplier):
    for k, v in w.items():
        if isinstance(v, (int, float, complex)):
            w[k] = v * multiplier
        elif isinstance(v, dict):
            multiply_values(v, multiplier)


def update_endpoint(config, endpoint):
    if endpoint:
        execute_component = config["coarse"]["execute"]["components"][0]
        execute_component.pop("host", None)
        execute_component.pop("port", None)
        if isinstance(endpoint, str):
            endpoints = list()
            endpoints.append(unquote(endpoint))
        else:
            endpoints = endpoint
        execute_component["endpoints"] = endpoints
        return config


def invert_subproperty_relationships(prop,
                                     subproperty_relationships,
                                     inverted, supers=list()):
    if subproperty_relationships:
        new_supers = list()
        new_supers.extend(supers)
        new_supers.append(prop)
        for subproperty, subsubproperty_relationships in subproperty_relationships.items():
            invert_subproperty_relationships(subproperty,
                                             subsubproperty_relationships,
                                             inverted, new_supers)
    else:
        inverted[prop] = supers


def apply_config_from_project(url, project, endpoint, index=None,
                              default_config=None, sample=False,
                              search_importance_enabled=False,
                              project_config=None):
    if not project_config:
        project_config = get_project_config(url, project)
    global current_project
    current_project = project
    if not index:
        if not sample:
            index = project_config["index"]["full"]
        else:
            index = project_config["index"]["sample"]
    if not default_config:
        default_config = load_project_json_file("default_config.json")
    c = default_config
    update_endpoint(c, endpoint)

    generate_components = c["coarse"]["generate"]["components"]
    preprocess_components = c["coarse"]["preprocess"]["components"]
    predicate_type_mapping = {}
    type_field_mapping = {}
    type_group_field_mapping = {}
    field_weight_mapping = {}
    elasticsearch_compiler_options = {}
    methods = ["extract_from_landmark", "other_method"]
    segments = ["title", "content_strict", "other_segment"]
    for gc in generate_components:
        if gc["name"] == "TypeIndexMapping":
            gc["type_index_mappings"]["Ad"] = index
        elif gc["name"] == "TypeFieldGroupByMapping":
            type_group_field_mapping = gc["type_field_mappings"]
        elif gc["name"] == "TypeFieldMapping":
            type_field_mapping = gc["type_field_mappings"]
        elif gc["name"] == "FieldWeightMapping":
            field_weight_mapping = gc["field_weight_mappings"]
        elif gc["name"] == "ElasticsearchQueryCompiler":
            elasticsearch_compiler_options = gc["elasticsearch_compiler_options"]

    for pc in preprocess_components:
        if pc["name"] == "PredicateDictConstraintTypeMapper":
            predicate_type_mapping = pc["predicate_range_mappings"]

    pinpoint_config = project_config.get("pinpoint", {})
    if "custom_field_mappings" in pinpoint_config:
        for t, fields in pinpoint_config["custom_field_mappings"].items():
            type_field_mapping[t] = fields

    for field_name, spec in project_config["fields"].items():
        predicate_type_mapping[field_name] = field_name.lower()
        type_group_field_mapping[field_name.lower()] = \
            "indexed.{}.high_confidence_keys".format(field_name)

        if "search_importance" in spec and search_importance_enabled:
            search_importance = spec["search_importance"]
            if search_importance > 1:
                multiplier = log(search_importance, 4)
            else:
                multiplier = 0.25
            weights = deepcopy(field_weight_mapping["indexed"]["*"])
            field_weight_mapping["indexed"][field_name] = weights
            multiply_values(weights, multiplier)

        fields = list()
        for method in methods:
            for segment in segments:
                fields.append("indexed.{}.{}.{}.value".format(field_name, method, segment))
                if spec.get("type", "string") == "email" or "email" in field_name.lower():
                    fields.append("indexed.{}.{}.{}.key".format(field_name, method, segment))
        type_field_mapping[field_name.lower()] = fields

        if "scoring_coefficient" in spec and \
           spec.get("type", "string").lower() == "number" and \
           spec.get("enable_scoring_coefficient", False):
            if "predicate_scoring_coefficients" not in elasticsearch_compiler_options:
                elasticsearch_compiler_options["predicate_scoring_coefficients"] = {}
            psc = elasticsearch_compiler_options["predicate_scoring_coefficients"]
            psc[field_name] = spec["scoring_coefficient"]

    subproperty_relationships = pinpoint_config.get("subproperty_relationships", {})
    inverted_relationships = {}
    if subproperty_relationships:
        for prop, sp_r in subproperty_relationships.items():
            invert_subproperty_relationships(prop, sp_r,
                                             inverted_relationships)
    for field_name, spec in project_config["fields"].items():
        fields = type_field_mapping[field_name.lower()]
        if not subproperty_relationships:
            if spec.get("type", "string") == "string" and\
                ("email" not in field_name.lower() and
                 "website" not in field_name.lower() and
                 "tld" not in field_name.lower() and
                 "date" not in field_name.lower() and
                 "image" not in field_name.lower()):
                fields.extend(type_field_mapping["owl:Thing"])
        else:
            supers = inverted_relationships.get(field_name.lower(), list())
            for super in supers:
                fields.extend(type_field_mapping[super])
    set_engine(Engine(c), project)


def dereference_config(config):
    if isinstance(config, dict):
        for k, v in config.items():
            if isinstance(v, str):
                if v.endswith('.json'):
                    sub_config = load_json_file(v)
                    config[k] = sub_config
            elif isinstance(v, list):
                for e in v:
                    dereference_config(e)
            elif isinstance(v, dict):
                dereference_config(v)
    return config


@app.route("/config", methods=['POST', 'GET'])
def config():
    if request.method == "POST":
        url = request.args.get('url', None)
        project = request.args.get('project', None)
        endpoint = request.args.get('endpoint', get_default_es_endpoint())
        index = request.args.get('index', None)
        sample = request.args.get('sample', False)
        search_importance_enabled = request.args.get('searchimportanceenabled',
                                                     False)
        if request.data and len(request.data) > 0:
            project_config = request.json
        else:
            project_config = None
        apply_config_from_project(url, project, endpoint, index,
                                  None, sample,
                                  search_importance_enabled,
                                  project_config)

        return "Applied config for project {}\n".format(project)
    elif request.method == "GET":
        project = request.args.get('project', None)
        config = get_engine(project).config
        if config:
            return json.dumps(dereference_config(config))
        else:
            return "No project config exists for project {}\n".format(project),\
                   status.HTTP_400_BAD_REQUEST


