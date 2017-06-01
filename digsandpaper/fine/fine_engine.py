import json

class FineEngine(object):

    def __init__(self, config):
        self.config = config
        self._initialize()

    def _initialize(self):
        self.name = ""

    def is_number(s):
        try:
            float(s) 
        except ValueError:
            return False

        return True

    def find_values(self, doc, field_elements):
        #print field_elements
        while len(field_elements) > 1:
            field_element = field_elements.pop(0)
            if '[' in field_element:
                if not field_element.startswith('['):
                    array_field_elements = field_element.split('[', 1)
                    array_field_element = array_field_elements[0]
                    doc = doc[array_field_element]
                    field_element = array_field_elements[1]
                array_elements = field_element.split(']')
                for array_element in array_elements:
                    if not array_element:
                        continue
                    if array_element.startswith('['):
                        array_element = array_element[1:]
                    if array_element.isdigit() and isinstance(doc, list):
                        doc = doc[int(array_element)]
                    else:
                        doc = doc[array_element]
            else:
                if field_element not in doc:
                    doc[field_element] = {}
                doc = doc[field_element]
        field_element = field_elements[0]
        #print "getting {}".format(field_element)
        if isinstance(doc, list):
            if len(doc)> 0:
                values = list()
                for d in doc:
                    #print json.dumps(d)
                    v = d.get(field_element, None)
                    if v:
                        values.append(v)
                return values
            return None
        return doc.get(field_element, None)

    def execute(self, expanded_queries, coarse_results):
        
        all_answers = []
        for (query, results) in zip(expanded_queries, coarse_results):
            answer_context = {}
            answers = []
            answer_variables = []
            answer_context["answers"] = answers
            answer_context["variables"] = answer_variables
            sparql = query.get("SPARQL")
            select = sparql.get("select")
            variables = select.get("variables")
            where = sparql.get("where")
            clauses = where.get("clauses")
            for v in variables:
                answer_variables.append(v["variable"])
            answer_variables.append("_score")

            result = results.to_dict()

            for hit in result["hits"]["hits"]:
                #print json.dumps(hit["_source"].get("knowledge_graph", "{}").get("ethnicity", {}), indent=4)

                matches = [match.split(":") for match in  hit.get("matched_queries", list())]
                answer = []
                for v in variables:
                    #print "variable {}".format(v)

                    potential_matched_clauses = []
                    if where["variable"] == v["variable"]:
                        potential_matched_clauses.append({"fields":[{"name":"doc_id","weight":1.0}]})
                    for c in clauses:
                        if c.get("variable") == v["variable"]:
                            potential_matched_clauses.append(c)
                    best_field = ""
                    best_weight = 0.0
                    best_value = None
                    for c in potential_matched_clauses:
                        #print json.dumps(c)
                        clause_id = c.get("_id", "")
                        matches_for_clause = [match for match in matches if match[0].startswith(clause_id) and clause_id]
                        #print "clause_id {}".format(clause_id)
                        #print "matches for clause {}".format(json.dumps(matches_for_clause))
                        for field in c.get("fields", []):
                            
                            name = field["name"]
                            if name in ["content_extraction.content_relaxed.text",
    "content_extraction.content_strict.text",
    "content_extraction.title.text"]:
                                continue
                            weight = field.get("weight", 1.0)
                            #print "trying {} {}".format(name, weight)
                            value = None

                            if len(matches_for_clause) > 0:
                                #print "matches_for_clause"
                                for match in matches_for_clause:
                                    if match[1] == name:
                                         value = match[2]
                            else:
                                field_elements = name.split(".")
                                #print "split field elements {}".format(field_elements)
                                value = self.find_values(hit["_source"], field_elements)
                                #print "found {}".format(value)

                            if value:
                                if isinstance(value, basestring) or not isinstance(value, list):
                                    val = list()
                                    val.append(value)
                                    value = val
                                for vv in value:
                                    #print vv[:10]
                                    if weight > best_weight:
                                        #print "best {} {}".format(name, weight)
                                        best_field = name
                                        best_weight = weight
                                        best_value = vv
                                    elif weight == best_weight and (isinstance(best_value, basestring) 
                                                                  and isinstance(vv, basestring) 
                                                                  and len(best_value) < len(vv)):
                                        #print "updating tie {} {}".format(best_value, vv)
                                        best_field = name
                                        best_weight = weight
                                        best_value = vv
                                    #print best_value

                    if best_value:
                       answer.append(best_value)
                    else:
                        answer.append("")
                answer.append(hit["_score"])  
                answers.append(answer)

            # assume we're aggregating on the first field
            
            t = query["type"].lower()

            if t == "point fact":
                t = t
            elif t == "mode":
                value_count = {}
                for answer in answers:
                    value = answer[0]
                    value_count[value] = value_count.get(value, 0) + 1
                mode_value = None
                mode_count = None
                for (k,v) in value_count.iteritems():
                    if not mode_count:
                        mode_value = k
                        mode_count = v
                    elif v > mode_count:
                        mode_value = k
                        mode_count = v
                answer_context["agg"] = mode_value
            elif t == "avg":
                count = 0
                total = 0 
                for answer in answers:
                    value = answer[0]
                    if value and is_number(value):
                        count = count + 1
                        total = total + float(value)
                if count > 0:
                    answer_context["agg"] = total / count
            elif t == "min":
                minimum = None 
                for answer in answers:
                    value = answer[0]
                    if value and is_number(value):
                        if not minimum:
                            minimum = float(value)
                        elif float(value) < minimum:
                            minimum = float(value)
                if minimum:
                    answer_context["agg"] = minimum
            elif t == "max":
                maximum = None 
                for answer in answers:
                    value = answer[0]
                    if value and is_number(value):
                        if not maximum:
                            maximum = float(value)
                        elif float(value) > maximum:
                            maximum = float(value)
                if maximum:
                    answer_context["agg"] = maximum

            if "id" in query:
                answer_context["question_id"] = query["id"]
            if "type" in query:
                answer_context["type"] = query["type"]
            all_answers.append(answer_context)
        return all_answers
