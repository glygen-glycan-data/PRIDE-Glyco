#!.venv/bin/python

import sys
import pandas as pd

outfile = sys.argv[1]
others = sys.argv[2:]

mds = []
embs = []
for of in others:
    print(of)
    mds.append(pd.read_csv(of.rsplit('.',1)[0]+'.csv'))
    embs.append(pd.read_feather(of))
md = pd.concat(mds,ignore_index=True)
md.to_csv(outfile.rsplit('.',1)[0]+'.csv',index=False)
emb = pd.concat(embs,axis=1)
emb.to_feather(outfile)

