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

# -----------------------------------------------------------------------------
# class ChatClassifier
# -----------------------------------------------------------------------------

class ChatClassifier:

    # -------------------------------------------------------------------------
    # class ChatClassifier

    def __init__(self, model_save_dir, dataset = None, do_train = False):
        self.dataset = dataset
        self.model_save_path = model_save_dir + "/chat_classifier.pkl"
        self.model = None

        if not os.path.exists(model_save_dir):
            os.makedirs(model_save_dir)
        
        if not os.path.exists(self.model_save_path) or do_train:
            self.train_model()
        else:
            self.load_model()

    # -------------------------------------------------------------------------
    # save_model

    def save_model(self):
        try:
            with open(self.model_save_path, 'wb') as fid:
                pickle.dump(self.model, fid)
        except Exception as e:
            self.log.error("Failed to save model '{}' ({})".format(self.mode_save_path, e))

    # -------------------------------------------------------------------------
    # load_model

    def load_model(self):
        try:
            with open(self.model_save_path, 'rb') as fid:
                self.model = pickle.load(fid)
        except Exception as e:
            self.log.error("Failed to open model '{}' ({})".format(self.mode_save_path, e))

    # -------------------------------------------------------------------------
    # train_model

    def train_model(self):
        print("Training model ....")
        
        self.model = Pipeline([('tfidf', TfidfVectorizer()), ('sgd', SGDClassifier())])

        self.model.fit(self.dataset.x, self.dataset.y)
        self.save_model()

    # -------------------------------------------------------------------------
    # classify_model

    def classify_model(self):
        numFolds = 4
        kf = KFold(numFolds, shuffle=True)

        models = [LogisticRegression, SGDClassifier, SGDClassifier]
        params = [{}, {"loss": "log", "penalty": "l2", 'n_iter':1000}, {}]

        for param, model in zip(params, models):
            total = 0
            
            for train_indices, test_indices in kf.split(x):
                train_x = x[train_indices]
                train_y = y[train_indices]
                test_x = x[test_indices]
                test_y = y[test_indices]

                reg = model(**param)
                pipe = Pipeline([('tfidf', TfidfVectorizer()), ('reg', reg)])

                pipe.fit(train_x, train_y)
                predictions = pipe.predict(test_x)
                total += accuracy_score(test_y, predictions)
            accuracy = total / numFolds
            print("Accuracy score of {0}: {1}".format(model.__name__, accuracy))

    # -------------------------------------------------------------------------
    # is_resource_query

    def is_resource_query(self, sentences):
        return [res == "find_resource" for res in  self.model.predict(sentences)]

    # -------------------------------------------------------------------------
    # classify

    def classify(self, sentences):
        return self.model.predict(sentences)
