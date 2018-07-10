import codecs
import json
import os
import requests
import copy
from urllib.parse import urlparse
from optparse import OptionParser
from digsandpaper.sandpaper_utils import load_json_file


_location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

elasticsearch_numeric_types = ["long", "integer", "short", "byte",
                               "double", "float", "half_float", "scaled_float"]


def load_project_json_file(file_name):
    with codecs.open(os.path.join(_location__, file_name),
                     'r', 'utf-8') as json_file:
        file = json.load(json_file)
        return file


def jl_file_iterator(file):
    with codecs.open(file, 'r', 'utf-8') as f:
        for line in f:
            document = json.loads(line)
            yield document


def generate(default_mapping, semantic_types,
             methods=["extract_from_landmark", "other_method"],
             segments=["title", "content_strict", "other_segment"],
             semantic_type_to_data_type={}):
    root = {}
    root_props = {}
    root["indexed"] = {"properties": root_props,
                       "dynamic": "true"}
    default_prov_ev_props = {"extracted_value": {"type": "string"},
                             "confidence": {"properties": {"extraction": {"type": "double"}}}}
    default_prov_props = {"properties": default_prov_ev_props}
    default_knowledge_graph_props = {"key": {"type": "string",
                                             "index": "not_analyzed"},
                                     "provenance": default_prov_props,
                                     "value": {"type": "string"},
                                     "data": {"enabled": False},
                                     "confidence": {"type": "double"}}
    kg_to_copy = {"properties": default_knowledge_graph_props}
    knowledge_graph = {}
    default_mapping["mappings"]["ads"]["properties"]["knowledge_graph"] = \
        {"properties": knowledge_graph,
         "dynamic": "true"}

    for semantic_type in semantic_types:
        # not copying yet
        if semantic_type_to_data_type.get(semantic_type, "string") in elasticsearch_numeric_types:
            data_type = semantic_type_to_data_type[semantic_type]
        elif semantic_type_to_data_type.get(semantic_type, "string").lower() == "number":
            data_type = "double"
        elif semantic_type_to_data_type.get(semantic_type, "string").lower() == "text":
            data_type = "text"
        elif semantic_type_to_data_type.get(semantic_type, "string").lower() == "date":
            data_type = "date"
        else:
            data_type = "string"
        knowledge_graph[semantic_type] = copy.deepcopy(kg_to_copy)
        semantic_type_props = {"high_confidence_keys": {"type": data_type,
                                                        "index": "not_analyzed"
                                                        },
                               "key_count": {"index": "no",
                                             "type": "long"},
                               "provenance_count": {"index": "no",
                                                    "type": "long"},
                               }
        if data_type in elasticsearch_numeric_types:
            knowledge_graph[semantic_type]["properties"]["key"]["type"] = data_type
            knowledge_graph[semantic_type]["properties"]["value"]["type"] = data_type
            semantic_type_props["high_confidence_keys"]["ignore_malformed"] = True
        elif data_type == "date":
            knowledge_graph[semantic_type]["properties"]["value"]["type"] = "date"
            knowledge_graph[semantic_type]["properties"]["value"][
                "format"] = "strict_date_optional_time||epoch_millis"
            knowledge_graph[semantic_type]["properties"]["key"]["type"] = "date"
            knowledge_graph[semantic_type]["properties"]["key"][
                "format"] = "strict_date_optional_time||epoch_millis"
        root_props[semantic_type] = {"properties": semantic_type_props}
        for method in methods:
            method_props = {}
            semantic_type_props[method] = {"properties": method_props}
            for segment in segments:

                segment_props = {"key": {"type": "string",
                                         "index": "not_analyzed"},
                                 "value": {"type": data_type}
                                 }
                if data_type == "email" or semantic_type == "email":
                    segment_props["value"]["analyzer"] = "url_component_analyzer"
                elif semantic_type == "website":
                    segment_props["value"]["analyzer"] = "url_component_analyzer"
                elif data_type == "date":
                    segment_props["value"]["type"] = "date"
                    segment_props["value"]["format"] = "strict_date_optional_time||epoch_millis"
                elif data_type in elasticsearch_numeric_types:
                    segment_props["value"]["ignore_malformed"] = True
                elif data_type == "text":
                    segment_props["value"]["analyzer"] = "english"
                method_props[segment] = {"properties": segment_props}

    default_mapping["mappings"]["ads"]["properties"]["indexed"] = root["indexed"]

    return default_mapping


def generate_from_etk_config(etk_config, default_mapping=None, shards=5,
                             methods=["extract_from_landmark", "other_method"],
                             segments=["title", "content_strict", "other_segment"]):
    if not default_mapping:
        default_mapping = load_project_json_file("default_mapping.json")
    semantic_types = frozenset()
    for data_extraction in etk_config["data_extraction"]:
        semantic_types = semantic_types | frozenset(data_extraction["fields"].keys())
    mapping = generate(default_mapping, semantic_types, methods, segments)
    mapping['settings']['index']['number_of_shards'] = shards
    return mapping


def generate_from_project_config(project_config, default_mapping=None, shards=5,
                                 methods=["extract_from_landmark", "other_method"],
                                 segments=["title", "content_strict", "other_segment"]):
    if not default_mapping:
        default_mapping = load_project_json_file("default_mapping.json")
    semantic_types = frozenset(project_config["fields"].keys())
    semantic_type_to_data_type = {}
    for semantic_type in semantic_types:
        semantic_type_to_data_type[semantic_type] = \
            project_config["fields"][semantic_type].get("type", "string")
    mapping = generate(default_mapping, semantic_types, methods,
                       segments, semantic_type_to_data_type)
    mapping['settings']['index']['number_of_shards'] = shards
    return mapping


if __name__ == "__main__":

    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-u", "--url", action="store",
                      type="string", dest="url", default=None)
    parser.add_option("-c", "--config", action="store",
                      type="string", dest="config")
    parser.add_option("-e", "--etk", action="store_true",
                      dest="etk", default=False)
    parser.add_option("-p", "--properties", action="store",
                      type="string", dest="properties")
    parser.add_option("-o", "--output", action="store",
                      type="string", dest="output")
    parser.add_option("-d", "--default_mapping", action="store",
                      type="string", dest="default_mapping")
    parser.add_option("-s", "--shards", action="store",
                      type="string", dest="shards", default="5")
    (c_options, args) = parser.parse_args()

    config_file = c_options.config
    properties_file = c_options.properties
    output_file = c_options.output
    default_mapping_file = c_options.default_mapping
    url = c_options.url
    etk = c_options.etk
    shards = c_options.shards
    if properties_file:
        properties = load_json_file(properties_file)
    else:
        properties = {}
    if not url and config_file:
        config = load_json_file(config_file)
    elif url:
        parsed_url = urlparse(url)
        if parsed_url.username:
            response = requests.get(url, auth=(parsed_url.username, parsed_url.password))
        else:
            response = requests.get(url)
        config = response.json()

    default_mapping = None
    if default_mapping_file:
        default_mapping = load_json_file(default_mapping_file)

    methods = properties.get("methods", ["extract_from_landmark"])
    segments = properties.get("segments", ["title", "content_strict"])
    methods.append("other_method")
    segments.append("other_segment")

    if default_mapping_file:
        default_mapping = load_json_file(default_mapping_file)
    else:
        default_mapping = load_project_json_file("default_mapping.json")

    if etk:
        mapping = generate_from_etk_config(config, default_mapping, shards, methods, segments)
    else:
        mapping = generate_from_project_config(config, default_mapping, methods, segments)

    o = codecs.open(output_file, 'w', 'utf-8')
    o.write(json.dumps(mapping, indent=4, sort_keys=True) + '\n')
    o.close()
