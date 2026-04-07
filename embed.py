#!.venv/bin/python
import sys, json, os.path, nltk, glob
from openai import OpenAI
from dotenv import load_dotenv
import time
import pandas as pd
from lockfile import FileLock
import argparse
from distproc import DistributedProcessing as dp

parser = argparse.ArgumentParser()
parser.add_argument(
    '--jsondocs',
    type = str,
    required = True,
    help = 'Directory or file-glob of PRIDE JSON documents.'
)
parser.add_argument(
    '--outbase',
    type = str,
    required = True,
    help = 'Output filename base for embeddings.'
)

dp.add_arguments(parser)

load_dotenv()
client = OpenAI()

MODEL="text-embedding-3-small"
def get_embedding(client, *texts, model=MODEL):
    response = client.embeddings.create(
        input=texts,
        model=model
    )
    return [ d.embedding for d in response.data ]

def handle_document1(prideacc,data):
    docmetadata = []
    embeds = {}
    texts = []
    headers=dict(projectDescription="Project Description",
                 sampleProcessingProtocol="Sample Processing Protocol",
                 dataProcessingProtocol="Data Processing Protocol")
    for k in data:
        if k == "title":
            texts.append("")
            texts.append("# %s"%data[k])
            texts.append("")
        if k in ('projectDescription','sampleProcessingProtocol','dataProcessingProtocol'):
            if data.get(k):
                texts.append("## %s"%(headers[k]))
                texts.append("")
                texts.append(data[k])
                texts.append("")
        elif k == 'keywords':
            texts.append("## Keywords")
            texts.append("")
            texts.append("; ".join(data[k]))
            texts.append("")

    docmetadata.append(dict(prideacc=prideacc,text="\n".join(texts)))
    texts = [ md['text'] for md in docmetadata ]
    for md, emb in zip(docmetadata,get_embedding(client,*texts)):
        key = md['prideacc']
        embeds[key] = emb
    return pd.DataFrame(docmetadata), pd.DataFrame(embeds)

def handle_document(prideacc,data):
    docmetadata = []
    embeds = {}
    for k in data:
        if k in ('title','projectDescription','sampleProcessingProtocol','dataProcessingProtocol'):
            text = data[k]
            for i,chunk in enumerate(nltk.tokenize.sent_tokenize(text)):
                docmetadata.append(dict(prideacc=prideacc,section=k,index=i,text=chunk))
        elif k in ('keywords',):
            text = "Keywords: " + "; ".join(data[k]) + "."
            docmetadata.append(dict(prideacc=prideacc,section=k,index=0,text=text))
    texts = [ md['text'] for md in docmetadata ]
    for md, emb in zip(docmetadata,get_embedding(client,*texts)):
        key = (md['prideacc'],md['section'],md['index'])
        embeds[key] = emb
    return pd.DataFrame(docmetadata), pd.DataFrame(embeds)

def handle_json_file(files,**kwargs):
    metadata = []
    embeddings = []
    for fn in files:
        data = json.load(open(fn))
        prideacc = os.path.split(fn)[1].rsplit('.')[0]
        md,emb = handle_document1(prideacc,data)
        metadata.append(md)
        embeddings.append(emb)
    md = pd.concat(metadata,ignore_index=True)
    emb = pd.concat(embeddings,axis=1)
    return md,emb


args = parser.parse_args()
workers = dp.parse_args(parser)
base = args.outbase

if os.path.isdir(args.jsondocs):
    allfiles = glob.glob(args.jsondocs + "/*.json")
else:
    allfiles = glob.glob(args.jsondocs)

batch = 50
tasks = []
for i in range(0,len(allfiles),batch):
    tasks.append(allfiles[i:(i+batch)])

savebatch = 50
counter = 0
metadata = []
embeddings = []
for result in dp.process(workers,handle_json_file,tasks):
    metadata.append(result[0])
    embeddings.append(result[1])
    if len(metadata) >= savebatch:
        csvfile = "%s-%04d.csv"%(base,counter)
        md = pd.concat(metadata,ignore_index=True)
        md.to_csv(csvfile,index=False)
        fthfile = "%s-%04d.fth"%(base,counter)
        df = pd.concat(embeddings,axis=1)
        df.to_feather(fthfile)
        counter += 1
        metadata = []
        embeddings = []
if len(metadata) > 0:
    csvfile = "%s-%04d.csv"%(base,counter)
    md = pd.concat(metadata,ignore_index=True)
    md.to_csv(csvfile,index=False)
    fthfile = "%s-%04d.fth"%(base,counter)
    df = pd.concat(embeddings,axis=1)
    df.to_feather(fthfile)






