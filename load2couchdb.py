#!.venv/bin/python
import sys, json, gzip
from couchws import *

db = sys.argv[1]
response = couch_webservice_request(db, method='PUT',
                                    username='admin', password='admin')
if sys.argv[2].endswith('.gz'):
    all_docs = json.loads(gzip.open(sys.argv[2]).read().decode())
else:
    all_docs = json.loads(open(sys.argv[2]).read())
idkey = None
if len(sys.argv) > 3:
    idkey = sys.argv[3]
if idkey:
    for doc in all_docs:
        doc["_id"] = doc[idkey]
    all_docs = dict(docs=all_docs)
request = "/"+db+"/"+"_bulk_docs"
response = couch_webservice_request(request, all_docs, method='POST', username='admin', password='admin')
print(json.dumps(response,indent=2))

