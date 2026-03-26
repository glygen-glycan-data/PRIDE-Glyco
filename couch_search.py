#!.venv/bin/python

import sys, json
from couchws import *

payload = {
  "selector": {
    "submissionType": "COMPLETE",
    "organisms": {
      "$elemMatch": {
        "name": "Homo sapiens (human)"
      }
    },
    "identifiedPTMStrings": {
      "$elemMatch": {
        "name" : {
          "$in": ["deamidated residue","Deamidated"]
        }
      }
    },
    "$text": "sampleProcessingProtocol:PNGase"
  }
}

if len(sys.argv) > 1:
    payload = json.loads(open(sys.argv[1]).read())

pagesize = 100
payload["limit"] = pagesize
request = '/pride/_find'
response = couch_webservice_request(request,payload,method='POST',
                                    username='admin',password='admin')
payload["bookmark"] = response["bookmark"]
all_docs = response["docs"]
nret = len(all_docs)

count = 1
while nret >= pagesize:
    # print(json.dumps(payload,indent=2))
    payload["skip"] = len(all_docs)
    response = couch_webservice_request(request,payload,method='POST',
                                        username='admin',password='admin')
    # print(response)
    # print(sorted([ d['accession'] for d in response["docs"]])[:5])
    all_docs.extend(response["docs"])
    nret = len(response["docs"])
    # print(f"{count}: Returned: {nret}")
    count += 1

print(json.dumps(all_docs,indent=2))

# print("Get pride entry by _id")
# id = response["docs"][0]["_id"]
# request = '/pride/'+id
# response = couch_webservice_request(request,username='admin', password='admin')
# print(json.dumps(response,indent=2))

















