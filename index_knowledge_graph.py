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

    input_path = args[0]
    output_file = args[1]
    properties_file = args[2]

    properties = load_json_file(properties_file)
    interesting_methods = properties.get("methods", [])
    interesting_segments = properties.get("segments", [])

    o = codecs.open(output_file, 'w', 'utf-8')
    for jl in jl_file_iterator(input_path):
        if "knowledge_graph" not in jl:
            continue

        kg = jl["knowledge_graph"]
        indexed = {}
        jl["indexed"] = indexed
        if "_id" in jl:
            jl["doc_id"] = jl["_id"]
        jl.pop("_id", None)

        for (pred, objs) in kg.iteritems():
            for obj in objs:

                key = obj["key"]
                value = obj["value"]
                result = {}
                if key: 
                    result["key"] = key
                if value:
                    result["value"] = value
                if pred not in indexed:
                    indexed[pred] = {}
                if "high_confidence_keys" not in indexed[pred]:
                    indexed[pred]["high_confidence_keys"] = []
                high_confidence_keys = set(indexed[pred]["high_confidence_keys"])
                if obj.get("confidence", 0.0) > 0.7:
                    high_confidence_keys.add(key)
                indexed[pred]["high_confidence_keys"] = list(high_confidence_keys)

                for prov in obj["provenance"]:
                    method = prov.get("method", "other_method")
                    if method not in interesting_methods:
                        method = "other_method"
                    source = prov["source"]
                    segment = source.get("segment", "other_segment")
                    if segment not in interesting_segments:
                        segment = "other_segment"
                    if method not in indexed[pred]:
                        indexed[pred][method] = {}
                    if segment not in indexed[pred][method]:
                        indexed[pred][method][segment] = []
                    if result not in indexed[pred][method][segment]:
                        indexed[pred][method][segment].append(result)


        o.write(json.dumps(jl) + '\n')

    o.close()
