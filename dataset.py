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

# -----------------------------------------------------------------------------
# class Dataset
# -----------------------------------------------------------------------------

class Dataset:

    # -------------------------------------------------------------------------
    # ctor

    def __init__(self, data_dir, sources):
        x = []
        y = []

        self.data_dir = data_dir

        for filename, tag, replace_dict in sources:
            with open(self.data_dir + '/' + filename) as my_file:
                if replace_dict is None:
                    for line in my_file:
                        x.append(line[:-1])
                        y.append(tag)
                else:
                    for line in my_file:
                        for key in replace_dict:
                            for val in replace_dict[key]:
                                x.append(line[:-1].replace(key, val))
                                y.append(tag)
                                x.append(line[:-1].replace(key, val.lower()))
                                y.append(tag)

        self.x = np.array(x)
        self.y = np.array(y)