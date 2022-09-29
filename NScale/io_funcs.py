#!/usr/bin/env python3

import numpy as np

def read_iq(filename, samples=-1):
    dat = np.fromfile(filename, np.complex64)
    return dat

# This function is basically unnecessary
def write_text(filename, textToWrite):
    with open(filename, 'a') as f:
        f.write(textToWrite)
