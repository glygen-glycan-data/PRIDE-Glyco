#!.venv/bin/python

import sys
import pandas as pd
from qdrant_client import QdrantClient, models

df = pd.read_feather(sys.argv[1])
md = pd.read_csv(sys.argv[1].rsplit('.',1)[0]+'.csv')

vecdb = QdrantClient(path="./pride-embeddings1.vdb")

if vecdb.collection_exists(collection_name="prideembeddings"):
    vecdb.delete_collection(collection_name="prideembeddings")

vecdb.create_collection(
    collection_name="prideembeddings",
    vectors_config=models.VectorParams(
        size=df.shape[0],  # Dimensionality of your vectors
        distance=models.Distance.COSINE
    ),
)
records = []
for i,rec in enumerate(md.to_dict(orient='records')):
    rec = models.PointStruct(
            id=i,
            vector=df[rec['prideacc']],
            payload=rec,
        )
    records.append(rec)
    if len(records) >= 100:
        vecdb.upsert("prideembeddings",records)
        records = []
vecdb.upsert("prideembeddings",records)

