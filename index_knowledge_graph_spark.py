from optparse import OptionParser
from pyspark import SparkContext, SparkConf, StorageLevel
import json
import codecs

def load_json_file(file_name):
    rules = json.load(codecs.open(file_name, 'r', 'utf-8'))
    return rules

def index_knowledge_graph_fields(jl, interesting_methods, interesting_segments):
    if "knowledge_graph" not in jl:
        return jl

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
                indexed[pred]["high_confidence_keys"] = set()
            
            if obj.get("confidence", 0.0) > 0.7:
            	indexed[pred]["high_confidence_keys"].add(key)

            tally = {}
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
                # if result not in indexed[pred][method][segment]:
                this_added = False
                if not method in tally:
                	tally[method] = {}
                if not segment in tally[method]:
                	tally[method][segment] = {segment: True}
                else:
                	this_added = True
                if not this_added:
                    indexed[pred][method][segment].append(result)

        indexed[pred]["high_confidence_keys"] = list(indexed[pred]["high_confidence_keys"])
    return jl

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

    sc = SparkContext(appName="DIG-GENERATE_KNOWLEDGE_GRAPH_INDEX_FIELDS")
    conf = SparkConf()

    docs = sc.sequenceFile(input_path).\
                   mapValues(lambda doc: json.dumps(index_knowledge_graph_fields(json.loads(doc), 
                                      	                     	      interesting_methods,
                                      	                     	      interesting_segments)))
                   

    #docs.saveAsSequenceFile(output_path, compressionCodecClass=compression)
    docs.values().saveAsTextFile(output_path)