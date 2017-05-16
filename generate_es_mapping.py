import codecs
import json

from optparse import OptionParser


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules

def jl_file_iterator(file):
    with codecs.open(file, 'r', 'utf-8') as f:
        for line in f:
            document = json.loads(line)
            yield document


if __name__ == "__main__":

    parser = OptionParser()
    (c_options, args) = parser.parse_args()

    extraction_config = args[0]
    output_file = args[1]
    properties_file = args[2]
    default_mapping_file = args[3]

    properties = load_json_file(properties_file)
    extraction_config = load_json_file(extraction_config)
    default_mapping = load_json_file(default_mapping_file)
    methods = properties.get("methods", [])
    segments = properties.get("segments", [])
    methods.append("other_method")
    segments.append("other_segment")


    root = {}
    root_props = {}
    root["indexed"] = {"properties": root_props}
    semantic_types = frozenset()
    for data_extraction in extraction_config["data_extraction"]:
        semantic_types = semantic_types | frozenset(data_extraction["fields"].keys())

    for semantic_type in semantic_types:
        semantic_type_props = {"high_confidence_keys":{"type": "string",
                                         "index": "not_analyzed"}}
        root_props[semantic_type] = {"properties":semantic_type_props}
        for method in methods:
            method_props = {}
            semantic_type_props[method] = {"properties": method_props}
            for segment in segments:
                segment_props = {"key": {"type": "string",
                                         "index": "not_analyzed"},
                                 "value": {"type": "string"}
                                }
                if semantic_type == "email":
                    segment_props["value"]["analyzer"] = "url_component_analyzer"
                method_props[segment] = {"properties": segment_props}


    default_mapping["mappings"]["ads"]["properties"]["indexed"] = root["indexed"]
    o = codecs.open(output_file, 'w', 'utf-8')
    o.write(json.dumps(default_mapping, indent=4, sort_keys=True) + '\n')
    o.close()
