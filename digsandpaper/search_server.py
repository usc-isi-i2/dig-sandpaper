from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import json
app = Flask(__name__)
CORS(app, supports_credentials=True)
engine = None


@app.route("/")
def hello():
    return "DIG Sandpaper"


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
