# Small module for loading and splitting byte blocks.
# Viviane - 9.12.2013
# must be python3 compatible

import numpy as np
import os


def loadInts(finame, starts=0, ends=0):
    if not os.path.isfile(finame):
        print("(FA) File '%s' does not exist." % (finame))
        return np.array([], dtype=np.uint32)

    f = open(finame, 'rb')

    if (starts or ends):
        from os import SEEK_SET
        f.seek(starts, SEEK_SET)  # seek
        X = np.fromfile(f, dtype=np.uint8, count=(ends - starts))
    else:
        X = np.fromfile(f, dtype=np.uint32)

    f.close()

    return X


def load(finame, starts=0, ends=0):
    if not os.path.isfile(finame):
        return np.array([], dtype=np.uint32)

    f = open(finame, 'rb')

    if (starts or ends):
        from os import SEEK_SET
        f.seek(starts, SEEK_SET)  # seek
        X = np.fromfile(f, dtype=np.uint8, count=(ends - starts))
    else:
        X = np.fromfile(f, dtype=np.uint8)

    f.close()

    return X


def splitblocks(block, blocksize):
    howMany = block.shape[0] / blocksize
    block = block[:(howMany * blocksize)]
    blocks = block.reshape(howMany, blocksize)
    return blocks


# Absolute
def sortPerFrequencies(block, start=0, last=0):
    if not last:
        start = 0
        last = 255

    freqrange = (last - start) + 1
    freqs = np.zeros(freqrange, dtype=np.float32)

    # sort per frequency
    for i in range(0, freqrange):
        freqs[i] = block[block == (start + i)].shape[0]

    return freqs


# Normalized [0...1] or as percentage
def sortPerFrequencies_Normalized(block, start=0, last=0):
    if not last:
        start = 0
        last = 255

    size = block.shape[0]
    if not size:
        return np.zeros((0))

    freqrange = (last - start) + 1
    freqs = np.zeros(freqrange, dtype=np.float32)

    # sort per frequency
    for i in range(0, freqrange):
        freqs[i] = block[block == (start + i)].shape[0]

    freqs /= size

    return freqs


def toDigital(B):
    # get start and end indices
    MatrixA = np.zeros((B.size + 2))
    MatrixA[1:-1] = B
    D = (MatrixA[1:] - MatrixA[:-1])  # Shortcut to produce a Difference Array. (1)
    D = np.nonzero(D)[0]  # Shortcut to produce a Difference Array. (2)
    # Merges -1 and +1 to 1. Nonzero()[0] returns the indices.

    try:
        R = D.reshape(D.size // 2, 2)
    except ValueError:
        print("Programming error: Matrix D has size %d." % (D.size))
        del D
        del MatrixA
        return np.zeros((0))

    del D
    del MatrixA

    return R


def Analog(R, Matrixspacesize, operator='+', B=None):
    '''
    Sorted R regions when multiplying.
    :return:
    '''
    if B is None:
        B = np.zeros(Matrixspacesize)

    if operator == '*':
        R.sort(key=lambda tup: tup[0])

    R = np.asarray(R)
    R = R.reshape(R.size // 2, 2)

    for i in range(R.shape[0]):
        if operator == '+':
            B[R[i][0]:R[i][1]] = 1
        elif operator == '-':
            B[R[i][0]:R[i][1]] = 0
        elif operator == '*':
            B[R[i][0]:R[i][1]] *= 1
            if i > 0:
                B[R[i - 1][1]:R[i][0]] = 0

    if operator == '*':
        B[0:R[0][0]] = 0
        B[R[i][1]:Matrixspacesize] = 0

    return B


def getSelectionMask(X, ymin, ymax):
    boolarr = (X >= ymin)
    boolarr = np.logical_and(boolarr, (X <= ymax))

    if not (type(boolarr) == np.ndarray):
        boolarr = np.asarray(boolarr)

    return boolarr  # may return zero.sized array!
