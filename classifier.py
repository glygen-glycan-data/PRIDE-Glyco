#!.venv/bin/python

import random

import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import shuffle

def train_document_classifier(embeddings, seeds, neg_seeds, bgsize=1.0, C=1.0, random_state=None):
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

    # 1. Split the original seed set: 80% for training, 20% for testing
    pos_train_accs, pos_test_accs = train_test_split(
        seeds, 
        test_size=0.20, 
        random_state=random_state
    )
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
    pos_test = embeddings[pos_test_accs].values.T
    
    # Extract the exact number of negative examples needed for testing and training
    neg_test = emb[seltestbg].values.T
    neg_train =  emb[seltrainbg].values.T
    
    # 3. Assemble the training and testing datasets
    # Combine positive (1) and negative (0) features
    X_train = np.vstack([pos_train, neg_train])
    y_train = np.concatenate([np.ones(num_train_samples), np.zeros(num_bg_train_samples)])
    
    X_test = np.vstack([pos_test, neg_test])
    y_test = np.concatenate([np.ones(num_test_samples), np.zeros(num_bg_test_samples)])
    
    # 4. Shuffle the datasets so labels are randomized (not all 1s followed by all 0s)
    X_train, y_train = shuffle(X_train, y_train, random_state=random_state)
    X_test, y_test = shuffle(X_test, y_test, random_state=random_state)
    
    print(f"Training data shape: {X_train.shape} (Positives: {num_train_samples}, Negatives: {num_bg_train_samples})")
    print(f"Testing data shape: {X_test.shape} (Positives: {num_test_samples}, Negatives: {num_bg_test_samples})")
    
    # 5. Initialize and train the Logistic Regression model
    model = LogisticRegression(random_state=random_state, penalty='l1', solver='liblinear', C=C, max_iter=1000)
    model.fit(X_train, y_train)
    
    # 6. Evaluate the model on the withheld test set
    y_pred = model.predict(X_test)
    
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    # target_names let us interpret the 1s and 0s easily in the terminal
    print(classification_report(y_test, y_pred, target_names=["Background (0)", "Seed-like (1)"]))
    
    return model, train_accessions, test_accessions

if __name__ == "__main__":

    import pandas as pd
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
        tn = set(open(sys.argv[3]).read().split())
        tn &= set(emb.columns)
        tn = list(tn)

    assert len(set(tp) & set(tn)) == 0

    # Train the model
    print("\nTraining classifier...")
    trained_model, train_acc, test_acc = train_document_classifier(emb, tp, tn, bgsize=25, C=10.0, random_state=None)
    
    for pracc in emb.columns:
        intrain = "training" if (pracc in train_acc) else ""
        intp = "TP" if (pracc in tp) else ("TN" if (pracc in tn) else "")

        emb1 = emb[[pracc]].values.T
        prediction = trained_model.predict(emb1)
        probability = trained_model.predict_proba(emb1)[0][1]
        if probability <= 0.8 or intp:
            continue

        print(pracc,round(prediction[0],3),round(probability,3),intp,intrain)
