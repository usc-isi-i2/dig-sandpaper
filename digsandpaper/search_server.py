from flask import Flask
from flask import request
from flask_api import status
from flask_cors import CORS, cross_origin
import json
import requests
from elasticsearch_mapping.generate import generate_from_project_config
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
