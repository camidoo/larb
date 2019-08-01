# -----------------------------------------------------------------------------
# Atlas/discord chatbot
# Copyright (c) 2019 - Patrick Fial
# -----------------------------------------------------------------------------
# dataset.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import numpy as np
import pandas as pd
import pickle
import os
import matplotlib.pyplot as plt
import random

from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split

from keras.utils.np_utils import to_categorical
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from sheets import SheetsCache

import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
tf.logging.set_verbosity(tf.logging.ERROR)

# -----------------------------------------------------------------------------
# class Dataset
# -----------------------------------------------------------------------------

class Dataset:

    # -------------------------------------------------------------------------
    # generate_data

    def generate_data(sheets:SheetsCache, data_dir, sources, resource_keys, grid_keys):
        i = 0
        dict = {}
        keys = sheets.get_keys()
        skipped_keys = ["kraken","anglerfish","animals","armflosser","birds","catfish","delfin","drache","drake","dolphin","fisch","fish","hai","gemeiner wal","monströser wal","sanfter wal",
                        "essbare pflanzen", "feuerelementar", "fire elemental", "giant ant", "giant bee", "giant crab", "gorgon", "gorgonen",
                        "hase", "affe", "giraffe", "elefant", "elephant", "rhino", "nashorn", "hydra", "kabeljau", "klapperschlange", "kobra", "cobra", "krähe", "crow", "kuh", "leatherwing", "lederschwinge",
                        "lion", "löwe", "manta ray", "mantarochen", "meerjungfrau", "monkey", "monsters", "nashorn", "ostrich", "papagei", "parrot", "pferd" "pig", "qualle", "rabbit", "razortooth",
                        "reptiles", "reptilien", "rhino", "riesenameise", "riesenbiene", "riesenkrabbe", "rock elemental", "schaf", "schildkröte", "schildhorn", "shieldhorn", "scorpion", "skorpion", 
                        "seagull", "seemöwe", "shark", "sheep", "speerfisch", "spinne", "squid", "tintenfisch", "steinelementar", "säbelzahn", "säugetiere", "thunfisch", "tuna", "tiere", "tiger", 
                        "turtle", "ungeheuer", "vulture", "vögel", "wirbellose", "wolf", "wolfsbarsch", "yeti", "zyklop", "invertebrates"]

        for filename, tag in sources:
            with open(data_dir + '/' + filename) as my_file:

                for line in my_file:
                    # if "#resource#" in line and "#grid#" in line:
                    #     replacement_grids = random.choices(grid_keys, k = 3) # int(len(grid_keys) / 2))
                    #     replacement_keys = [i for i in resource_keys if i not in skipped_keys]

                    #     for val in replacement_grids:
                    #         random_resource = random.choice(replacement_keys)

                    #         text = line[:-1].replace("#grid#", val).replace("#resource#", random_resource).lower()

                    #         n_keys = 0

                    #         for k in keys:
                    #             if k.lower() in text:
                    #                 n_keys += 1

                    #         if len(text) > 0:
                    #             dict[i] = { 'text': text, 'category': tag, 'n_resource_keys': n_keys, 'n_words': len(text.split()), 'length': len(text) }
                    #             i += 1

                    # elif "#resource#" in line:
                    #     replacement_keys = [i for i in resource_keys if i not in skipped_keys]
                    #     replacement_keys = random.choices(replacement_keys, k = 3) # int(len(replacement_keys) / 2))

                    #     for val in replacement_keys:
                    #         text = line[:-1].replace("#resource#", val).lower()

                    #         n_keys = 0

                    #         for k in keys:
                    #             if k.lower() in text:
                    #                 n_keys += 1

                    #         if len(text) > 0:
                    #             dict[i] = { 'text': text, 'category': tag, 'n_resource_keys': n_keys, 'n_words': len(text.split()), 'length': len(text) }
                    #             i += 1
                    # else:
                    text = line[:-1].lower()
                    n_keys = 0

                    for grid_key in grid_keys:
                        text = text.replace(grid_key.lower(), " ")

                    for resource_key in resource_keys:
                        text = text.replace(resource_key.lower(), " ")

                    for k in keys:
                        if k.lower() in text:
                            n_keys += 1

                    if len(text) > 0:
                        dict[i] = { 'text': text, 'category': tag, 'n_resource_keys': n_keys, 'n_words': len(text.split()), 'length': len(text) }
                        i += 1

        df = pd.DataFrame.from_dict(dict, "index")
        df.to_csv(data_dir + "/chat_dataset.csv")

    # -------------------------------------------------------------------------
    # ctor

    def __init__(self, cache_dir, csv_file = None, use_tokenizer = True, create_valid_set = True, num_words = 10000, maxlen = 130):
        self.create_valid_set = create_valid_set
        self.use_tokenizer = use_tokenizer
        self.num_classes = 2
        self.model_name = "chat_classification.h5"
        self.num_words = num_words
        self.maxlen = maxlen
        self.tokenizer_file = cache_dir + '/chat_classification.tokenizer'
        self.df = None

        if csv_file is not None:
            try:
                self.df = shuffle(pd.read_csv(csv_file, dtype = { "text": str, "category": str, "n_resource_keys": np.int8, "n_words": np.int8, "length": np.int8 }))
            except Exception as e:
                print("Failed to open {} ({})".format(csv_file, e))
                return

        # load previously generated tokenizer, or create new one

        if os.path.isfile(self.tokenizer_file):
            with open(self.tokenizer_file, "rb") as f:
                self.tokenizer = pickle.load(f)
        else:
            self.tokenizer = Tokenizer(num_words = self.num_words, filters = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n', lower = True)
            self.tokenizer.fit_on_texts(self.df['text'].values)

            with open(self.tokenizer_file, 'wb') as f:
                pickle.dump(self.tokenizer, f, pickle.HIGHEST_PROTOCOL)

            self.word_index = self.tokenizer.word_index

        if self.df is not None:
            # create onehot-vectors for classification in deep learning network

            if self.use_tokenizer:
                self.df['label'] = 0
                self.df.loc[self.df['category'] == 'chat', 'label'] = 0
                self.df.loc[self.df['category'] == 'find_resource', 'label'] = 1

                self.Y = to_categorical(self.df['label'], num_classes = 2)
            else:
                self.Y = self.df['category'].values

            # use tokenizer to prepare/normalize text input

            self.X = self.prepare_array(self.df['text'].values)

            # create/split into train/test/validation sets.

            self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(self.X, self.Y, test_size = 0.25)
            self.x_train, self.x_valid, self.y_train, self.y_valid = train_test_split(self.x_train, self.y_train, test_size = 0.2)

    def get_input_shape(self):
        if self.df is None:
            return (130,)

        return (self.x_train.shape[1], )

    def get_input_dim(self):
        return self.num_words

    def get_num_classes(self):
        return self.num_classes

    def get_model_filename(self):
        return self.model_name        

    def get_classes(self):
        return ["chat", "find_resource"]

    def prepare_array(self, texts):
        if self.use_tokenizer:
            sequences = self.tokenizer.texts_to_sequences(texts)
            return pad_sequences(sequences, maxlen = self.maxlen)

        return texts

    def hist(self, columns = None):
        if columns is not None:
            self.df.hist(column = columns, bins = 100)
        else:
            self.df.hist(bins = 100)

        plt.show()

    def hist_text(self, column):
        pd.Series(self.df[column]).value_counts().plot('bar')
        plt.show()