import numpy as np
import FTrack.config as config
from FTrack.util_track_deduplicate import util_track_deduplicate

def frame_sync_words_search(ftracks, ftrack_pwr, trk_pre, user_id, tu_map, chirp_len, fft_size):
# sync_edge_idx > 0 indicates valid sync words have been found

    pre_freq = trk_pre[0]
    pre_edge_0 = trk_pre[1]
    T = chirp_len

    fft_factor = config.TRK_FFT_factor
    SYNC_WORD_OFFSET = config.FRM_SYNC_WORD_FREQ
    OFFSET_TOLERANCE = config.TRK_CLUSTER_FREQ_TOLERANCE
    
    PREAMB_CHIRP_NUM_MIN = config.TRK_PREAMBLE_MIN
    PREAMB_CHIRP_NUM_MAX = config.TRK_PREAMBLE_MAX
    
    sync_freq_0 = (pre_freq + SYNC_WORD_OFFSET*fft_factor) % fft_size
    sync_freq_1 = (pre_freq + 2*SYNC_WORD_OFFSET*fft_factor) % fft_size
    if (sync_freq_0 == 0):
        sync_freq_0 = fft_size

    if (sync_freq_1 == 0):
        sync_freq_1 = fft_size
        
    sync_edge_idx = 0
    for edge_idx in np.arange(PREAMB_CHIRP_NUM_MIN, PREAMB_CHIRP_NUM_MAX + 1):
        edge0 = pre_edge_0 + T*edge_idx
        edge1 = edge0 + T
        
        st_pos = 0
        [candies0, st_pos] = tracks_on_edge(ftracks, st_pos, edge0, tu_map)
        [dedup_candies_0, tu_map] = track_deduplicate(ftracks, candies0, edge0, ftrack_pwr, tu_map, user_id, fft_size)
        track_id_0 = is_trk_contained(candies0, sync_freq_0, edge0, ftracks, OFFSET_TOLERANCE, T, fft_size, fft_factor)
        
        if (track_id_0 <= 0):
            continue
        
        st_pos = 0
        [candies1, st_pos] = tracks_on_edge(ftracks, st_pos, edge1, tu_map)
        [dedup_candies_1, tu_map] = track_deduplicate(ftracks, candies1, edge1, ftrack_pwr, tu_map, user_id, fft_size)
        track_id_1 = is_trk_contained(candies1, sync_freq_1, edge1, ftracks, OFFSET_TOLERANCE, T, fft_size, fft_factor)
     
        if (track_id_1 > 0):
            # sync words found
            tu_map[track_id_0] = user_id
            tu_map[track_id_1] = user_id
            
            sync_edge_idx = edge_idx
            break

    return sync_edge_idx, tu_map


def tracks_on_edge(ftracks, st_pos, edge_line, tu_map):

    sz = ftracks.shape
    track_num = sz[0]
    
    candies = np.zeros((track_num, 1), int)
    cand_num = 0
    for t in np.arange(st_pos, track_num):
        
        track = ftracks[t,]
        tr_st = track[1]
        tr_ed = track[2]
        
        if (edge_line >= tr_st and edge_line <= tr_ed):
            candies[cand_num] = t
            cand_num = cand_num + 1
        elif (edge_line < tr_st):
            break
            
    next_pos = t
    candies = candies[0:cand_num]
    
    return candies, next_pos

def track_deduplicate(ftracks, candies, edge_line, ftrack_pwr, tu_map, user_id, fft_size):

    trk_num = candies.size
    trk_candies = np.zeros((trk_num, 3), int)
    for t in range(trk_num):
        trk_id = candies[t]
        trk_candies[t,] = ftracks[trk_id,]
    
    [dedup_trks, dup_indicate_tbl] = util_track_deduplicate(trk_candies, ftrack_pwr, fft_size)

    # produce the results
    sz = dedup_trks.shape
    dedup_num = sz[0]
    dedup_candies = np.zeros((dedup_num, 1))
    de_idx = 0
    
    for t in range(trk_num):
        trk_id = candies[t]
        
        if (dup_indicate_tbl[t] < 0):
            tu_map[trk_id] = -user_id
        else: #(dup_indicate_tbl(t) == 0)
            dedup_candies[de_idx] = trk_id
            de_idx = de_idx + 1

    return dedup_candies, tu_map
    
def is_trk_contained(candies, trk_bin, edge_line, ftracks, TOLERANCE, chirp_len, fft_size, fft_factor):
# check is trk_bin contained in set candies
    
    c_num = candies.size
    
    trk_id = 0
    for c in range(c_num):
        t_idx = candies[c]
        track = ftracks[t_idx,]
        fft_bin = track[:, 0]
        
        fbin_offset = abs(fft_bin - trk_bin)
        if (fbin_offset > fft_size/2):
            fbin_offset = fft_size - fbin_offset 

        if (np.floor(fbin_offset/fft_factor) > TOLERANCE):
            continue
        
        res = track_edge_relation(track, edge_line, chirp_len)
        
        if (res > 0):
            trk_id = t_idx
            break

    return trk_id

def track_edge_relation(track, edge, chirp_len):

    SYNC_SCALE_FACTOR = config.SYNC_TRK_LEN_SCALE_FACTOR
    RANGE_THRESHOLD = config.TRK_SPAN_RATIO
    
    dn_chk_point = edge - chirp_len
    up_chk_point = edge + chirp_len
    
    trk_st = track[:, 1]
    trk_ed = track[:, 2]
    
    range_st = max(np.concatenate(([dn_chk_point], trk_st)))
    range_ed = min(np.concatenate(([up_chk_point], trk_ed)))
    
    range_ratio = (range_ed-range_st)/(up_chk_point - dn_chk_point)
    
    if (range_ratio > SYNC_SCALE_FACTOR*RANGE_THRESHOLD):
        res = 1
    else:
        res = 0
    
    return res
