#!.venv/bin/python

import sys
import pandas as pd
import os.path
from qdrant_client import QdrantClient, models

import warnings
warnings.filterwarnings("ignore", message=".*Local mode is not recommended.*")

vecdbfn = sys.argv[1]
sys.argv.pop(1)

emb = pd.read_feather(vecdbfn.rsplit('.',1)[0]+".fth")
vecdb = QdrantClient(path=os.path.abspath(vecdbfn))

for prideacc in sys.argv[1:]:
    if prideacc not in emb:
        continue
    print("Query:",prideacc)
    hits = vecdb.query_points(
        collection_name="prideembeddings",
        query=emb[prideacc].values,
        limit=30+1
    ).points
    for hit in hits:
        if hit.payload['prideacc'] != prideacc:
            print(f"ID: {hit.id}, Score: {hit.score}, Accession: {hit.payload['prideacc']}")
