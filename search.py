#!.venv/bin/python

import json, time, sys

from pridepy.project.project import Project

# keywords = []
# filters = []
# for arg in sys.argv[1:]:
#     if ':' in arg:
#         k,v = [ s.strip() for s in arg.split(":",1) ]
#         filters.append(f"{k}=={v}")
#     else:
#         keywords.append(arg)

# keywords = ",".join(keywords)
# filters = ",".join(filters)

keywords = "deamidation,PNGase"
filters = "organisms==Homo sapiens (human),submissionType==COMPLETE"

p = Project()
all_results = []
page = 0
while True:
    result = p.search_by_keywords_and_filters(keywords, filters, 100, page, 'ASC', 'accession')
    if len(result) == 0:
        break
    all_results.extend(result)
    page += 1
    time.sleep(3)
print(f"{len(all_results)} projects reteived.",file=sys.stderr)
print(json.dumps(all_results,indent=2))
