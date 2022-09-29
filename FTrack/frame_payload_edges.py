import numpy as np
import FTrack.config as config

def frame_payload_edges(preambs, sync_words, payload_num, chirp_len):

    PREAMB_CHIRP_NUM = config.FRM_PREAMBLE
    HEADER_CHIRP_NUM = PREAMB_CHIRP_NUM + 4
    
    sz = preambs.shape
    frm_num = sz[0]
    
    sym_edges = np.zeros((payload_num, frm_num), int)
    header_edges = np.zeros((HEADER_CHIRP_NUM+1, frm_num))
    
    T = chirp_len
    for f in range(frm_num):
        edge_0 = preambs[f, 1]
        
        # payload symbol edges
        sync_idx = sync_words[f]
        if (sync_idx == 0):  # if sync workds cannot be found
            sync_idx = PREAMB_CHIRP_NUM
        
        a = np.arange(payload_num)
        sym_idx = a.transpose() + sync_idx + 4.25
        sym_edges[:, f] = edge_0 + sym_idx * T
        
        # header edges
        header_edge_0 = edge_0 - (PREAMB_CHIRP_NUM - sync_idx)*T
        header_idx = np.arange(HEADER_CHIRP_NUM + 1)
        header_edges[:, f] = header_edge_0 + header_idx.transpose() * T
        
    return header_edges, sym_edges
