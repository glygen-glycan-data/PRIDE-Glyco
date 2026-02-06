## Quick Setup 
```
% python3.12 -m venv .venv
% .venv/bin/python -m pip install -r requirements.txt
% ./downloadall.py > projects.json
% ls -l projects.json
% jq -r '.[].accession' < projects.json | wc -l
36696
```
