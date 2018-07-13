from optparse import OptionParser
from pyspark import SparkContext, SparkConf, StorageLevel
import json
import codecs


def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules


def index_knowledge_graph_fields(jl, interesting_methods, interesting_segments,
                                 max_key_count, max_provenance_count):
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
        try:
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
        except Exception as e:
            # print json.dumps(jl['knowledge_graph'], indent=2)
            print('Failed:', jl['doc_id'])
            # raise e
            return {}

        indexed[pred]["high_confidence_keys"] = list(indexed[pred]["high_confidence_keys"])
    if total_key_count < max_key_count and total_provenance_count < max_provenance_count:
        return jl
    else:
        return {}


if __name__ == '__main__':
    compression = "org.apache.hadoop.io.compress.BZip2Codec"

    parser = OptionParser()

    (c_options, args) = parser.parse_args()
    input_path = args[0]
    output_path = args[1]
    properties_file = args[2]

    properties = load_json_file(properties_file)
    interesting_methods = properties.get("methods", [])
    interesting_segments = properties.get("segments", [])
    max_key_count = properties.get("max_key_count", 100)
    max_provenance_count = properties.get("max_provenance_count", 1000)

    sc = SparkContext(appName="DIG-GENERATE_KNOWLEDGE_GRAPH_INDEX_FIELDS")
    conf = SparkConf()

    docs = sc.sequenceFile(input_path).\
                   mapValues(lambda doc: json.dumps(index_knowledge_graph_fields(json.loads(doc), 
                                                                      interesting_methods,
                                                                      interesting_segments,
                                                                      max_key_count,
                                                                      max_provenance_count))).filter(lambda (k, v): v != "{}")

    docs.saveAsSequenceFile(output_path, compressionCodecClass=compression)
