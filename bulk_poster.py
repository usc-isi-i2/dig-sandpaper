#!/usr/bin/python
import requests
import codecs
from optparse import OptionParser


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


parser = OptionParser()
(c_options, args) = parser.parse_args()

inputFile = args[0]
host = args[1]
port = args[2]
index = args[3]
t = args[4]
with codecs.open(inputFile, 'r', 'utf-8') as f:
    docs = f.read().splitlines()
url = "http://{}:{}/{}/{}/_bulk".format(host, port, index, t)
print("starting to post")
counter = 0
for chunk in chunker(docs, 1000):
    bulk_request = '{"index":{}}\n' + '\n{"index":{}}\n'.join(chunk) + '\n'
    counter += len(chunk)
    r = requests.post(url, bulk_request)
    print(len(r.json()["items"]))
print(counter)
