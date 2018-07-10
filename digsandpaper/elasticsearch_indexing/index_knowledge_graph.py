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


def index_knowledge_graph_fields(jl, interesting_methods=["extract_from_landmark"],
                                 interesting_segments=["title", "content_strict"],
                                 max_key_count=500,
                                 max_provenance_count=500):

    if "knowledge_graph" not in jl:
        return jl

    kg = jl["knowledge_graph"]
    indexed = {}
    jl["indexed"] = indexed
    if "_id" in jl:
        jl["doc_id"] = jl["_id"]
    jl.pop("_id", None)

    total_provenance_count = 0
    total_key_count = 0

    for (pred, objs) in kg.items():
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
                indexed[pred]["high_confidence_keys"] = set()
            if "key_count" not in indexed[pred]:
                indexed[pred]["key_count"] = 0
            indexed[pred]["key_count"] = indexed[pred]["key_count"] + 1
            total_key_count = total_key_count + 1
            if "provenance_count" not in indexed[pred]:
                indexed[pred]["provenance_count"] = 0

            if obj.get("confidence", 0.0) > 0.7:
                indexed[pred]["high_confidence_keys"].add(key)

            if 'provenance' in obj:
                tally = {}
                for prov in obj["provenance"]:
                    indexed[pred]["provenance_count"] = indexed[pred]["provenance_count"] + 1
                    total_provenance_count = total_provenance_count + 1
                    method = prov.get("method", "other_method")
                    if method not in interesting_methods:
                        method = "other_method"
                    source = prov.get("source", {})
                    segment = source.get("segment", "other_segment")
                    if segment not in interesting_segments:
                        segment = "other_segment"
                    if method not in indexed[pred]:
                        indexed[pred][method] = {}
                    if segment not in indexed[pred][method]:
                        indexed[pred][method][segment] = []
                    # if result not in indexed[pred][method][segment]:
                    this_added = False
                    if method not in tally:
                        tally[method] = {}
                    if segment not in tally[method]:
                        tally[method][segment] = {segment: True}
                    else:
                        this_added = True
                    if not this_added:
                        indexed[pred][method][segment].append(result)
            else:
                if 'other_method' not in indexed[pred]:
                    indexed[pred]['other_method'] = {}
                if 'other_segment' not in indexed[pred]['other_method']:
                    indexed[pred]['other_method']['other_segment'] = []
                indexed[pred]['other_method']['other_segment'].append(result)

        indexed[pred]["high_confidence_keys"] = list(indexed[pred]["high_confidence_keys"])
    if total_key_count < max_key_count and total_provenance_count < max_provenance_count:

        return jl
    else:
        return None


if __name__ == "__main__":

    parser = OptionParser()
    (c_options, args) = parser.parse_args()

    input_path = args[0]
    output_file = args[1]
    if len(args) > 2:
        properties_file = args[2]
    else:
        properties_file = None

    if properties_file:
        properties = load_json_file(properties_file)
    else:
        properties = {}
    interesting_methods = properties.get("methods", [])
    interesting_segments = properties.get("segments", [])
    max_key_count = properties.get("max_key_count", 100)
    max_provenance_count = properties.get("max_provenance_count", 1000)

    o = codecs.open(output_file, 'w', 'utf-8')
    for jl in jl_file_iterator(input_path):
        jl = index_knowledge_graph_fields(jl, interesting_methods, interesting_segments,
                                          max_key_count, max_provenance_count)
        if jl:
            o.write(json.dumps(jl) + '\n')

    o.close()
