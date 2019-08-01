# -----------------------------------------------------------------------------
# Atlas/discord chatbot
# Copyright (c) 2019 - Patrick Fial
# -----------------------------------------------------------------------------
# rnn.py
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from keras.layers import * 
from keras.activations import * 
from keras.models import * 
from keras.optimizers import * 
from keras.initializers import * 
from keras.callbacks import *

from dataset import Dataset

# -----------------------------------------------------------------------------
# class RNN - Recurrent Neural Network
# -----------------------------------------------------------------------------

class RNN:

    # -------------------------------------------------------------------------
    # ctor

    def __init__(self, learning_rate, dataset:Dataset, model_path, variant):
        self.model_path = model_path
        self.verbose = 1

        input_tensor = model_stack = Input(dataset.get_input_shape())

        if variant == 1:
            model_stack = Embedding(input_dim = dataset.get_input_dim(), output_dim = 128, input_length = dataset.get_input_shape()[0])(model_stack)
            model_stack = SpatialDropout1D(0.7)(model_stack)
            model_stack = LSTM(64, dropout=0.7, recurrent_dropout=0.7)(model_stack)
            model_stack = Dense(dataset.get_num_classes(), activation='softmax')(model_stack)
        elif variant == 2:
            model_stack = Embedding(input_dim = dataset.get_input_dim(), output_dim = 128, input_length = dataset.get_input_shape()[0])(model_stack)
            model_stack = LSTM(256)(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = BatchNormalization()(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = Dense(512, activation='relu')(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = BatchNormalization()(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = Dense(dataset.get_num_classes(), activation='softmax')(model_stack)
        elif variant == 3:
            model_stack = Embedding(input_dim = dataset.get_input_dim(), output_dim = 128, input_length = dataset.get_input_shape()[0])(model_stack)
            model_stack = Bidirectional(GRU(128))(model_stack)
            model_stack = Dense(64, activation='relu')(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = Dense(64, activation='relu')(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = BatchNormalization()(model_stack)
            model_stack = Dense(dataset.get_num_classes(), activation='softmax')(model_stack)
        elif variant == 4:
            model_stack = Embedding(input_dim = dataset.get_input_dim(), output_dim = 256, input_length = dataset.get_input_shape()[0])(model_stack)
            model_stack = Conv1D(1024, 3, padding='valid', strides = 1, activation='relu')(model_stack)
            model_stack = GlobalMaxPooling1D()(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = BatchNormalization()(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = Dense(1024, activation='relu')(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = BatchNormalization()(model_stack)
            model_stack = Dropout(0.5)(model_stack)
            model_stack = Dense(dataset.get_num_classes(), activation='softmax')(model_stack)               

        self.model = Model(inputs = [input_tensor], outputs = [model_stack])
        self.model.compile(loss = "binary_crossentropy", optimizer = Adam(lr = learning_rate), metrics = ["accuracy"])

    # -------------------------------------------------------------------------
    # train

    def train(self, epochs, batch_size, dataset:Dataset):
        self.model.summary()

        callbacks = []

        callbacks.append(ReduceLROnPlateau(monitor = "val_loss", factor = 0.95, verbose = self.verbose, patience = 1))
        callbacks.append(EarlyStopping(monitor='val_loss', patience = 5, min_delta = 0.01, restore_best_weights = True, verbose = self.verbose))

        validation = None

        if dataset.x_valid is not None and dataset.y_valid is not None:
            validation = [dataset.x_valid, dataset.y_valid]
        else:
            validation = [dataset.x_test, dataset.y_test]

        self.model.fit(
            x = dataset.x_train,
            y = dataset.y_train,
            batch_size = batch_size,
            verbose = self.verbose,
            epochs = epochs,
            validation_data = validation,
            callbacks = callbacks)

        score = self.model.evaluate(dataset.x_test, dataset.y_test, verbose = self.verbose)

        print("Model score: {}".format(score))

    # -------------------------------------------------------------------------
    # predict

    def predict(self, texts, dataset:Dataset):
        res = []

        for text in texts:
            prepared = dataset.prepare_array([text])
            pred = self.model.predict(prepared)

            cls = dataset.get_classes()[np.argmax(pred)]
            acc = pred[0][dataset.get_classes().index(cls)]

            res.append((cls, acc))

        return res

    # -------------------------------------------------------------------------
    # load_weights

    def load_weights(self):
        self.model.load_weights(self.model_path)

    # -------------------------------------------------------------------------
    # save_weights

    def save_weights(self):
        self.model.save_weights(self.model_path)
