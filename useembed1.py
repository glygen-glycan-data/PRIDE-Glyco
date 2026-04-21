#!.venv/bin/python

import sys, traceback, time
import pandas as pd
from qdrant_client import QdrantClient, models

df = pd.read_feather(sys.argv[1])
md = pd.read_csv(sys.argv[1].rsplit('.',1)[0]+'.csv')

# vecdb = QdrantClient(path="./pride-embeddings.vdb")
vecdb = QdrantClient("http://localhost:6333")

if vecdb.collection_exists(collection_name="prideembeddings"):
    vecdb.delete_collection(collection_name="prideembeddings")

vecdb.create_collection(
    collection_name="prideembeddings",
    vectors_config=models.VectorParams(
        size=df.shape[0],  # Dimensionality of your vectors
        distance=models.Distance.COSINE
    ),
)
curpracc = None
records = []
nrec = md.shape[0]
npr = len(set(md['prideacc']))
seenpr = set()
j = 0 
for i,rec in enumerate(md.to_dict(orient='records')):
    # print(rec)
    if rec['prideacc'] != curpracc:
        j += 1
        curpracc = rec['prideacc']
    rec = models.PointStruct(
            id=i,
            vector=df[(rec['prideacc'],rec['section'],rec['index'])],
            payload=rec,
        )
    # print(rec)
    records.append(rec)
    if len(records) >= 100:
        for attempts in range(10):
            try:
                vecdb.upsert("prideembeddings",records)
                print(i+1,round(100*(i+1)/nrec,2),j,round(100*j/npr,2),file=sys.stderr)
                sys.stderr.flush()
                break
            except:
                traceback.print_exc()
                time.sleep(10)

        records = []
vecdb.upsert("prideembeddings",records)

