import numpy as np
import FTrack.config as config
from FTrack.util_track_deduplicate import util_track_deduplicate

def ftrack_grouping_v2(ftracks, user_borders, track_user_map, edge_trk_map, chirp_len, ftrack_pwr):
    
    sorted_tracks = ftracks
    
    sz = sorted_tracks.shape
    track_num = sz[0]
    track_edge_map = np.zeros((track_num, 2), int)   # edge line position, edge index
    
    u_sz = user_borders.shape
    user_num = u_sz[1]
    
    for u in range(user_num):
        edges = user_borders[:, u]
        user_id = u + 1
        [track_user_map, track_edge_map] = ftracks_2_user(sorted_tracks, edges, track_user_map, track_edge_map, user_id, chirp_len, ftrack_pwr)
   
    for t in range(track_num): 
        user_id = track_user_map[t, 0]
        edge_idx = track_edge_map[t, 1]
        
        if (user_id <= 0):
            continue

        if (edge_idx > 0):
            edge_trk_map[edge_idx-1, user_id-1] = t

    return track_user_map, edge_trk_map


def ftracks_2_user(ftracks, edges, track_user_map, track_edge_map, user_id, chirp_len, ftrack_pwr):

    edge_num = edges.size
    ch_range = chirp_len
    
    fft_factor = config.TRK_FFT_factor
    fft_size = chirp_len*fft_factor
    
    for e in range(edge_num):
        edge_line = edges[e]

        ftrack_pos = 1
        [candies, ftrack_pos1] = tracks_on_edge(ftracks, ftrack_pos, edge_line, track_user_map)
        
        [dedup_candies, track_user_map] = track_deduplicate(ftracks, candies, edge_line, ftrack_pwr, track_user_map, user_id, fft_size)
        
        track_id = track_select(ftracks, dedup_candies, edge_line, ch_range, ftrack_pwr)
        
        if (track_id > 0):
            track_user_map[track_id] = user_id
            track_edge_map[track_id,] = np.concatenate(([edge_line], [e+1]))
            
    return track_user_map, track_edge_map

def tracks_on_edge(ftracks, st_pos, edge_line, tu_map):

    sz = ftracks.shape
    track_num = sz[0]
    
    candies = np.zeros((track_num, 1), int)
    cand_num = 0
    for t in np.arange(st_pos,track_num):
        if (tu_map[t] < 0):  # the ftrack belongs to a known user
            continue
        
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
    dedup_candies = np.zeros((dedup_num, 1), int)
    de_idx = 0
    for t in range(trk_num):
        trk_id = candies[t]
        
        if (dup_indicate_tbl[t] < 0):
            tu_map[trk_id] = -user_id
        else: #(dup_indicate_tbl(t) == 0)
            dedup_candies[de_idx] = trk_id
            de_idx = de_idx + 1

    return dedup_candies, tu_map

def track_select(ftracks, cand_indexes, edge_line, chirp_len, ftrk_pwr):

    cand_num = cand_indexes.size
    
    EDGE_RANGE = config.EDGE_ERROR_TOLERANCE
    
    dn_line = edge_line - (chirp_len+EDGE_RANGE)
    up_line = edge_line + (chirp_len+EDGE_RANGE)
    
    FACTOR = 100
    dist_min = 100000
    track_id = 0
    
    use_pwr_metric = (config.FTRK_GROUP_ALPHA < 1)
    for c in range(cand_num):
        t_index = cand_indexes[c]
        track = ftracks[t_index,]
        
        tr_st = int(track[:, 1])
        tr_ed = int(track[:, 2])
        
        if (dn_line < tr_st and up_line > tr_ed):
            
            # check the spaning ratio of the track
            res = track_edge_relation(track, edge_line, chirp_len)
            if (res <= 0):
                continue
            
            track_mid_pos = (tr_st+tr_ed)//2
            edge_dist = abs(edge_line - track_mid_pos)/(up_line - dn_line)
            
            # track power metric
            if (use_pwr_metric):
                pm = trkpwr_metric(track, ftrk_pwr, edge_line, chirp_len)
                metric = weighted_metric(edge_dist, pm)

                edge_dist = metric * FACTOR
            else:
                edge_dist = edge_dist * FACTOR
            
            if (edge_dist < dist_min):
                track_id = t_index
                dist_min = edge_dist

    return track_id

def track_edge_relation(track, edge, chirp_len):

    RANGE_THRESHOLD = config.TRK_SPAN_RATIO
    dn_chk_point = edge - chirp_len
    up_chk_point = edge + chirp_len
    
    trk_st = int(track[:, 1])
    trk_ed = int(track[:, 2])
    
    range_st = max([dn_chk_point, trk_st])
    range_ed = min([up_chk_point, trk_ed])
    
    range_ratio = (range_ed-range_st)/(up_chk_point - dn_chk_point)
    
    if (range_ratio > RANGE_THRESHOLD):
        res = 1
    else:
        res = 0

    return res

def weighted_metric(dist, pwr):

    alpha = config.FTRK_GROUP_ALPHA
    res = alpha*dist + (1-alpha)*pwr
    
    return res

def trkpwr_metric(track, ftrk_pwr, edge_line, chirp_len):

    pwr_range = chirp_len//8
    fbin = int(track[:, 0])
    
    chk_pt_dn = edge_line - pwr_range
    chk_pt_up = edge_line + pwr_range
    
    trk_st = int(track[:, 1])
    trk_ed = int(track[:, 2])
    
    chk_pt_dn = max(chk_pt_dn, trk_st)
    chk_pt_up = min(chk_pt_up, trk_ed)
    
    radius = 0
    pwr_dn = np.mean(ftrk_pwr[fbin, chk_pt_dn-radius:chk_pt_dn+radius+1])
    pwr_up = np.mean(ftrk_pwr[fbin, chk_pt_up-radius:chk_pt_up+radius+1])
    
    pwr_range = max(ftrk_pwr[fbin, chk_pt_dn:chk_pt_up])
    
    pm = abs(pwr_up - pwr_dn)/pwr_range
    
    return pm
