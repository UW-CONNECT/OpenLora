import numpy as np

def preamb_edge_detect_v2(corr, threshold):

    templt = (corr > threshold)
    corr = corr * templt
    
    edges = np.zeros(corr.shape)
    edge_num = 0    
    for i in range(corr.size):
        if (corr[i] > 0):
            edges[edge_num] = i
            edge_num = edge_num + 1
    
    edges = edges[0:edge_num]
	
    return edges
