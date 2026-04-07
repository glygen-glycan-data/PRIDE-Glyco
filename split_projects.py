#!.venv/bin/python

import sys, json

docs = json.load(open(sys.argv[1]))
for d in docs:
    acc = d['accession']
    with open(acc+".json",'w') as wh:
        wh.write(json.dumps(d))
