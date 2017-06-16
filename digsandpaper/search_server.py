from flask import Flask
from flask import request
from flask_api import status
from flask_cors import CORS, cross_origin
import json
import requests
import StringIO
import codecs
from elasticsearch_mapping.generate import generate_from_project_config
from elasticsearch_indexing.index_knowledge_graph import index_knowledge_graph_fields
from urllib import unquote

app = Flask(__name__)
CORS(app, supports_credentials=True)
engine = None


@app.route("/")
def hello():
    return "DIG Sandpaper"


@app.route("/mapping", methods=['GET'])
def generate_mapping():
    url = request.args.get('url', None)
    project = request.args.get('project', None)
    if url and project:
        url = unquote(url)
        response = requests.get('{}/projects/{}'.format(url, project))
    elif url and not project:
        url = unquote(url)
        response = requests.get(url)
    elif not url and project:
        response = requests.get('{}/projects/{}'.format(default_url, project))
    else:
        return "Please provide either a url and/or a project as url params to retrieve fields to generate an elasticserach mapping", status.HTTP_400_BAD_REQUEST

    project_config = response.json()
    m = generate_from_project_config(project_config)
    return json.dumps(m)

def jl_file_iterator(file):
    line = file.readline()
    while line :
        document = json.loads(line)
        yield document
        line = file.readline()

@app.route("/indexing/fields", methods=['POST'])
def index_fields():
    if (request.headers['Content-Type'] == 'application/x-gzip'):
        gz_data_as_file = StringIO.StringIO(request.data)
        uncompressed = gzip.GzipFile(fileobj=gz_data_as_file, mode='rb')
        jls = uncompressed.read().decode('utf-8') 
    elif (request.headers['Content-Type'] == 'application/json' or
          request.headers['Content-Type'] == 'application/x-jsonlines'):
        jls = request.data.decode('utf-8')
    else:
        return "Only supported content types are application/x-gzip, application/json and application/x-jsonlines", status.HTTP_400_BAD_REQUEST
    reader = codecs.getreader('utf-8')
    jls_as_file = reader(StringIO.StringIO(jls))
    jls = [json.dumps(jl) for jl in [index_knowledge_graph_fields(jl) for jl in jl_file_iterator(jls_as_file)] if jl is not None]
    indexed_jls = "\n".join(jls)
    if (request.headers['Content-Type'] == 'application/x-gzip'):
        indexed_jls_as_file = StringIO.StringIO()
        compressed = gzip.GzipFile(
            filename=FILENAME, mode='wb', fileobj=indexed_jls_as_file)
        compressed.write(indexed_jls)
        compressed.close()
        return indexed_jls_as_file.getvalue()
    else:
        return indexed_jls


@app.route("/search", methods=['POST'])
def search():
    query = json.loads(request.data)
    (qs, rs) = engine.execute_coarse(query)
    answers = engine.execute_fine(qs, rs)
    return json.dumps(answers)


@app.route("/search/coarse", methods=['POST'])
def coarse():
    query = json.loads(request.data)
    (qs, rs) = engine.execute_coarse(query)
    qs_with_rs = [{"query": q, "result": r.to_dict()} for q, r in zip(qs, rs)]
    return json.dumps(qs_with_rs)

@app.route("/search/coarse/generate", methods=['POST'])
def coarse_generate():
    query = json.loads(request.data)
    qs = engine.generate_coarse(query)
    return json.dumps(qs)

@app.route("/search/fine", methods=['POST'])
def fine():
    return "Hello World!"


def set_engine(e):
    global engine
    engine = e
