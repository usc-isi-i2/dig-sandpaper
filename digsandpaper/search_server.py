from flask import Flask
from flask import request
import json
app = Flask(__name__)

engine = None


@app.route("/")
def hello():
    return "DIG Sandpaper"


@app.route("/search", methods=['POST'])
def search():
    return "Hello World!"


@app.route("/search/coarse", methods=['POST'])
def coarse():
    query = json.loads(request.data)
    (qs, rs) = engine.execute_coarse(query)
    rs_as_dicts = [r.to_dict() for r in rs]
    return json.dumps(rs_as_dicts)


@app.route("/search/fine", methods=['POST'])
def fine():
    return "Hello World!"


def set_engine(e):
    global engine
    engine = e
