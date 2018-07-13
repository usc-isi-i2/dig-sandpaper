import codecs
import json
import numbers


def load_json_file(file_name):
    with codecs.open(file_name, 'r', 'utf-8') as json_file:
        rules = json.load(json_file)
        return rules


def convert_jsonld_cdr(doc):
    """
    converts json ld output of etk to cdr object
    :param doc: the input Knowledge graph in json ld format
    :return: a cdr object with embedded knowledge graph and doc_id.
    # TODO DIG UI needs a @timestamp_crawl(?) add this too
    """
    new_docs = list()
    new_doc = dict()
    kg = dict()
    for key in list(doc):
        if key == '@id':
            new_doc['doc_id'] = doc['@id']
        elif key == '@context':
            new_doc[key] = doc[key]
        elif key == '@type':
            kg['type'] = list()
            types = doc['@type']
            if not isinstance(types, list):
                types = [types]
            for type in types:
                kg['type'].append({'value': type, 'key': create_key_from_value(type, 'type')})
        else:
            kg[key] = list()
            objs = doc[key]
            if not isinstance(objs, list):
                objs = [objs]
            for obj in objs:
                if '@id' in obj and '@context' in obj:
                    new_docs.extend(convert_jsonld_cdr(obj))
                if '@id' in obj:
                    kg[key].append({'value': obj['@id'], 'key': obj['@id']})
                elif '@value' in obj:
                    val = obj['@value']
                    k_val = create_key_from_value(val, key)
                    kg[key].append({'value': val, 'key': k_val})

    new_doc['knowledge_graph'] = kg
    new_docs.append(new_doc)
    return new_docs


def create_key_from_value(value, field_name):
    key = value

    if (isinstance(key, str) or
        isinstance(key, numbers.Number)) and 'date' not in field_name:  # TODO this 'date' fix is a hack
        # try except block because unicode characters will not be lowered
        try:
            key = str(key).strip().lower()
        except:
            pass

    return key
