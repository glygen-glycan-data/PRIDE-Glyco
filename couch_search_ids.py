#!.venv/bin/python

import sys, json
from couchws import *

payloadstr = open(sys.argv[1]).read()
ids = open(sys.argv[2]).read().split()
try:
    ids = [ int(i) for i in ids ]
except ValueError:
    pass
payloadstr = payloadstr.replace("___XXX_IDS_XXX___",",".join(map(lambda s: ('%r'%(s,)).replace('\'','"'),ids)))
payload = json.loads(payloadstr)

pagesize = 100
payload["limit"] = pagesize
request = '/pride/_find'
response = couch_webservice_request(request,payload,method='POST',
                                    username='admin', password='admin')
payload["bookmark"] = response["bookmark"]
all_docs = response["docs"]
nret = len(all_docs)

count = 1
while nret >= pagesize:
    # print(json.dumps(payload,indent=2))
    payload["skip"] = len(all_docs)
    response = couch_webservice_request(request,payload,method='POST',
                                        username='admin', password='admin')
    # print(response)
    # print(sorted([ d['accession'] for d in response["docs"]])[:5])
    all_docs.extend(response["docs"])
    nret = len(response["docs"])
    # print(f"{count}: Returned: {nret}")
    count += 1

print(json.dumps(all_docs,indent=2))











