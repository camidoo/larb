# -----------------------------------------------------------------------------
# Atlas/discord chatbot
# Copyright (c) 2019 - Patrick Fial
# -----------------------------------------------------------------------------
# main.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score

import os
import numpy as np
import pickle

from rnn import RNN

# -----------------------------------------------------------------------------
# class ChatClassifier
# -----------------------------------------------------------------------------

class ChatClassifier:

    # -------------------------------------------------------------------------
    # class ChatClassifier

    def __init__(self, model_save_dir, model_type = "RNN", variant = 4, dataset = None, do_train = False):
        self.variant = variant
        self.model_type = model_type
        self.dataset = dataset
        self.model = None

        self.model_save_path_dnn = model_save_dir + "/rnn_" + dataset.get_model_filename()
        self.model_save_path_sgd = model_save_dir + "/chat_classifier.pkl"

        if not os.path.exists(model_save_dir):
            os.makedirs(model_save_dir)
        
        if not os.path.exists(self.model_save_path_dnn) or do_train:
            self.train_model()
        else:
            self.load_model()

    # -------------------------------------------------------------------------
    # save_model

    def save_model(self):
        self.model1.save_weights()

        try:
            with open(self.model_save_path_sgd, 'wb') as fid:
                pickle.dump(self.model2, fid)
        except Exception as e:
            self.log.error("Failed to save model '{}' ({})".format(self.model_save_path_sgd, e))

    # -------------------------------------------------------------------------
    # load_model

    def load_model(self):
        self.model1 = RNN(0.0008, self.dataset, self.model_save_path_dnn, variant = self.variant)
        self.model1.load_weights()

        try:
            with open(self.model_save_path_sgd, 'rb') as fid:
                self.model2 = pickle.load(fid)
        except Exception as e:
            self.log.error("Failed to open model '{}' ({})".format(self.mode_save_path, e))

    # -------------------------------------------------------------------------
    # train_model

    def train_model(self):
        self.model1 = RNN(0.0008, self.dataset, self.model_save_path_dnn, variant = self.variant)
        self.model1.train(5, 32, self.dataset)
            
        self.model2 = Pipeline([('tfidf', TfidfVectorizer()), ('sgd', SGDClassifier())])
        self.model2.fit(self.dataset.x, self.dataset.y)
        self.save_model()

    # -------------------------------------------------------------------------
    # classify

    def classify(self, sentences):
        res = []

        for sent in sentences:
            res1= self.model1.predict([sent], self.dataset)[0]
            res2= self.model2.predict([sent])[0]

            if res1[0] != res and res1[1] < 0.85:
                res.append(res2)
            else:
                res.append(res1[0])

        return res

