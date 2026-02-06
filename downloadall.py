#!.venv/bin/python

import json, time, sys

from pridepy.project.project import Project

p = Project()
page = 0
pagesize = 100
print("[",end="")
first = True
while True:
    result = p.get_projects(pagesize, page, 'ASC', 'accession')
    if len(result) == 0:
        break
    for r in result:
        if first:
            print(json.dumps(r,indent=2),end="")
            first = False
        else:
            print(",\n"+json.dumps(r,indent=2),end="")
    page += 1
    time.sleep(3)
print("]")