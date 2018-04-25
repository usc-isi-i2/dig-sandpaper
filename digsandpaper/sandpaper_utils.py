import codecs
import json


def load_json_file(file_name):
    with codecs.open(file_name, 'r', 'utf-8') as json_file:
        rules = json.load(json_file)
        return rules
