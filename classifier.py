#!.venv/bin/python

import random

import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import shuffle

def train_document_classifier(embeddings, seeds, neg_seeds, test=0.2, bgsize=1.0, random_state=None, **kwargs):
    """
    Trains a Logistic Regression model to identify documents similar to a seed set.
    
    Args:
        seed_embeddings (np.ndarray): Embeddings of the positive "seed" documents.
        background_embeddings (np.ndarray): Embeddings of other/negative documents.
        random_state (int): Seed for reproducibility.
        
    Returns:
        LogisticRegression: The trained model.
    """
    seeds = list(set(seeds)&set(embeddings.columns))
    neg_seeds = list(set(neg_seeds)&set(embeddings.columns))
    bg = list(set(embeddings.columns)-set(seeds))
    nbgsel = int(round(len(seeds)*bgsize))
    if len(bg) < len(neg_seeds):
        raise ValueError("Not enough background embeddings to create selected background.")
    if len(bg) < nbgsel:
        raise ValueError("Not enough background embeddings to create selected background.")

    if test > 0.0:
        # 1. Split the original seed set
        pos_train_accs, pos_test_accs = train_test_split(
            seeds, 
            test_size=test, 
            random_state=random_state
        )
        have_test = True
    else:
        pos_train_accs = list(seeds)
        pos_test_accs = []
        have_test = False

    selected_accessions = list(seeds)
    train_accessions = list(pos_train_accs)
    test_accessions = list(pos_test_accs)

    num_train_samples = len(pos_train_accs)
    num_bg_train_samples = int(round(num_train_samples*bgsize))
    num_test_samples = len(pos_test_accs)
    num_bg_test_samples = nbgsel-num_bg_train_samples

    random.seed(random_state)

    selbg = neg_seeds + list(random.sample(list(set(bg)-set(neg_seeds)),
                                           nbgsel-len(neg_seeds)))
    random.shuffle(selbg)
    seltrainbg = selbg[:num_bg_train_samples]
    seltestbg = selbg[num_bg_train_samples:]

    selected_accessions += selbg
    train_accessions += seltrainbg
    test_accessions += seltestbg 

    # 2. Randomly sample background (negative) embeddings for 50/50 balance
    # Shuffle background embeddings first to ensure random sampling
    
    np.random.seed(random_state)
    
    pos_train = embeddings[pos_train_accs].values.T
    if have_test:
        pos_test = embeddings[pos_test_accs].values.T
    
    # Extract the exact number of negative examples needed for testing and training

    neg_train =  embeddings[seltrainbg].values.T
    if have_test:
        neg_test = embeddings[seltestbg].values.T
    
    # 3. Assemble the training and testing datasets
    # Combine positive (1) and negative (0) features
    X_train = np.vstack([pos_train, neg_train])
    y_train = np.concatenate([np.ones(num_train_samples), np.zeros(num_bg_train_samples)])
    
    if have_test:
        X_test = np.vstack([pos_test, neg_test])
        y_test = np.concatenate([np.ones(num_test_samples), np.zeros(num_bg_test_samples)])
    
    # 4. Shuffle the datasets so labels are randomized (not all 1s followed by all 0s)
    X_train, y_train = shuffle(X_train, y_train, random_state=random_state)
    if have_test:
        X_test, y_test = shuffle(X_test, y_test, random_state=random_state)
    
    print(f"Training data shape: {X_train.shape} (Positives: {num_train_samples}, Negatives: {num_bg_train_samples})")
    if have_test:
        print(f"Testing data shape: {X_test.shape} (Positives: {num_test_samples}, Negatives: {num_bg_test_samples})")
    
    # 5. Initialize and train the Logistic Regression model
    model = LogisticRegression(max_iter=1000, random_state=random_state, **kwargs)
    model.fit(X_train, y_train)
    
    # 6. Evaluate the model on the withheld test set
    if not have_test:
        return model, train_accessions, test_accessions
    
    y_pred = model.predict(X_test)
    
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    # target_names let us interpret the 1s and 0s easily in the terminal
    print(classification_report(y_test, y_pred, target_names=["Background (0)", "Seed-like (1)"]))
    
    return model, train_accessions, test_accessions

if __name__ == "__main__":

    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt
    import sys

    emb = pd.read_feather(sys.argv[1])
    # md = pd.read_csv(sys.argv[1].rsplit('.',1)[0]+'.csv')

    tp = set()
    for fn in sys.argv[2].split():
        tp1= set(open(fn).read().split())
        tp1 &= set(emb.columns)
        tp |= tp1
    tp = list(tp)

    tn = []
    if len(sys.argv) > 3:
        tn = set()
        for fn in sys.argv[3].split():
            tn1 = set(open(fn).read().split())
            tn1 &= set(emb.columns)
            tn |= tn1
        tn = list(tn)

    pr = []
    if len(sys.argv) > 4:
        pr = set()
        for fn in sys.argv[4].split():
            pr1 = set(open(fn).read().split())
            pr1 &= set(emb.columns)
            pr |= pr1
        pr = list(pr)
    pr = set(pr)

    assert len(set(tp) & set(tn)) == 0

    # Train the model
    print("\nTraining classifier...")
    # 
    extra_args = dict(test=0.0, C=100.0, penalty='l1', solver='liblinear', bgsize=25)
    trained_model, train_acc, test_acc = train_document_classifier(emb, tp, tn, random_state=None, **extra_args)
    print("NZ Coeffs:",sum(*[1*(xi>0) for xi in trained_model.coef_]))

    rows = []
    rows1 = []
    for pracc in emb.columns:
        intrain = "training" if (pracc in train_acc) else ""
        inpr = "predict" if (pracc in pr) else ""
        intp = "TP" if (pracc in tp) else ("TN" if (pracc in tn) else "")

        emb1 = emb[[pracc]].values.T
        probability = trained_model.predict_proba(emb1)[0][1]
        
        row = dict(probability=probability,pracc=pracc,group=intp,intp=(1 if intp == "TP" else 0),
                   intn=(1 if intp == "TN" else 0), training=(1 if intrain else 0))
        rows.append(row)

        if not inpr and (probability <= 0.8):
            continue

        rows1.append([pracc,round(probability,3),intp,intrain,inpr])
    
    for row in sorted(rows1,key=lambda l: -l[1]):
        print(*row)
    
    df = pd.DataFrame(rows).set_index('pracc')
    # print(df)
    df1 = df[df['group']!=""]
    df2 = df[(df['group']=="") & (df['probability']>0.001)]
    # print(df2)

    # print(df1[df1['probability']<0.3])

    # fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True)
    # , ax=axes[0]
    sns.histplot(df1,x='probability',binrange=(0,1),binwidth=0.05,hue='group')
    plt.show()
    # ax=axes[1], 
    sns.histplot(df2,x='probability',binrange=(0,1),binwidth=0.05,log_scale=(False, True))
    plt.show()
