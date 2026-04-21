#!.venv/bin/python

from qdrant_client import QdrantClient, models

def find_common_sentences(vecdb,md,emb,tp,tn,scthr=0.8,tpfrac=0.5):
    tp = set(tp)
    tn = set(tn)
    goodrows = []
    for row in md[md['prideacc'].isin(tp)].to_dict(orient='records'):
        # print(row)
        search_result = vecdb.query_points(
            collection_name="prideembeddings",
            query=emb[(row['prideacc'],row['section'],row['index'])].values,
            limit=100,
            timeout=300,
            score_threshold=scthr,
            search_params=models.SearchParams(
                exact=True  # Enables exact search, bypassing HNSW
            )
        )
        praccs = set([row['prideacc']])
        for i,hit in enumerate(search_result.points):
            if hit.payload == row:
                continue
            # print(i+1,hit.id,hit.score,hit.payload)
            praccs.add(hit.payload['prideacc'])
        tpcount = len(praccs&tp)
        # tncount = len(praccs&tn)
        othercount = len(praccs)-tpcount
        if tpcount < 5:
            continue
        print(row)
        print(len(search_result.points),len(praccs),tpcount,othercount)
        if tpcount >= 5 and othercount < 5:
            goodrows.append(row)
            print(row)
    
if __name__ == "__main__":

    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    import sys

    emb = pd.read_feather(sys.argv[1])
    md = pd.read_csv(sys.argv[1].rsplit('.',1)[0]+'.csv')

    tp = set()
    for fn in sys.argv[2].split():
        tp1= set(open(fn).read().split())
        tp1 &= set(md['prideacc'])
        tp |= tp1
    tp = list(tp)

    tn = []
    if len(sys.argv) > 3:
        tn = set()
        for fn in sys.argv[3].split():
            tn1 = set(open(fn).read().split())
            tn1 &= set(md['prideacc'])
            tn |= tn1
        tn = list(tn)

    assert len(set(tp) & set(tn)) == 0

    vecdb = QdrantClient("http://localhost:6333")
    collection_info = vecdb.get_collection("prideembeddings")
    print("Collection info:", collection_info)

    find_common_sentences(vecdb,md,emb,tp,tn)
