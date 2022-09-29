import numpy as np

def preamb_edge_fitting(edges):

    # use polyfit() to determine the initial offset and chirp duration
    x = np.arange(edges.size)

    P = np.polyfit(x.transpose(), edges, 1)
    R = np.polyval(P, x.transpose()) - edges.transpose()
    # residual error
    err = sum(R.transpose()**2)
    
    res = np.array([P[1], P[0], err])
    return res
