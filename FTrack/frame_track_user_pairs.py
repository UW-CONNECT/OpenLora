import numpy as np

def frame_track_user_pairs(ftracks, sym_edges, edge_trk_map):

    sz = edge_trk_map.shape
    payload_num = sz[0]
    user_num = sz[1]
    
    tu_pairs = np.zeros((payload_num*user_num, 4), int)
    idx = 0
    for u in range(user_num):
        for p in range(payload_num):
            trk_idx = edge_trk_map[p, u]
            if (trk_idx <= 0):
                continue
                
            fbin = ftracks[trk_idx, 0]
            edge = sym_edges[p, u]

            tu_pairs[idx,] = [fbin, u+1, edge, p+1]
            idx = idx + 1
    
    tu_pairs = tu_pairs[0:idx,]
    return tu_pairs
