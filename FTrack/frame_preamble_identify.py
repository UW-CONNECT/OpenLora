import numpy as np
import FTrack.config as config
from FTrack.util_track_deduplicate import util_track_deduplicate
from FTrack.frame_sync_words_search import frame_sync_words_search

def frame_preamble_identify(preambles, trk_user_map, ftrack_pwr, ftracks, chirp_len, fft_size):

    NONE_USER_ID = -256
    
    # group preamble in clusters and remove duplicate ones
    preamb_candies, preamb_candies_tbl = util_track_deduplicate(preambles, ftrack_pwr, fft_size)
    
    # sort preambles in time order
    #pre_candies_sorted = sortrows(preamb_candies, [2 3 1])
    pre_candies_sorted = preamb_candies[preamb_candies[:,1].argsort(),]
    
    # search sync words and remove false preambles
    sz = pre_candies_sorted.shape
    candi_num = sz[0]
    
    preambs_sync = np.zeros(sz, int)           # true preambles with correct sync words
    sync_locs = np.zeros((candi_num, 1))
    sync_num = 0
    
    pre_edges = preamb_chirp_edge_estimate(pre_candies_sorted, chirp_len)
    for p in range(candi_num):
        [sync_edge_idx, trk_user_map] = frame_sync_words_search(ftracks, ftrack_pwr, pre_edges[p,], NONE_USER_ID, trk_user_map, chirp_len, fft_size)
        
        if (sync_edge_idx > 0):
            preambs_sync[sync_num,] = pre_candies_sorted[p,]
            sync_locs[sync_num] = sync_edge_idx
            sync_num = sync_num + 1
    
    preambs_sync = preambs_sync[0:sync_num,]
    sync_words = sync_locs[0:sync_num]
	
    return preambs_sync, trk_user_map, sync_words

def preamb_chirp_edge_estimate(pre_trks, chirp_len):

    # offset between real edge and the starting pos of track 
    TRK_SPAN_RATIO = config.TRK_SPAN_RATIO
    edge_offset = TRK_SPAN_RATIO*chirp_len 
    
    sz = pre_trks.shape
    pre_num = sz[0]
    
    pre_edges = np.zeros((pre_num, 2))
    pre_edges[:, 0] = pre_trks[:, 0]
    pre_edges[:, 1] = pre_trks[:, 1] + edge_offset
    
    return pre_edges
