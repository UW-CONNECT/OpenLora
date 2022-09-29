import numpy as np
import FTrack.config as config

def ftrack_multi_grouping(ftracks, sym_edges, trk_map, edge_map, chirp_len, ftrk_pwr):

    # first round track-->edge mapping
    # get all non-assigned tracks
    sz = trk_map.shape
    trk_num = sz[0]
    non_tracks = np.zeros((trk_num, 1), int)
    non_trk_num = 0
    for t in range(trk_num):
        if (trk_map[t] == 0):
            non_tracks[non_trk_num] = t
            non_trk_num = non_trk_num + 1

    non_tracks = non_tracks[0:non_trk_num]
    
    # get all non-assigned edges
    sz = edge_map.shape
    edge_num = sz[0]
    user_num = sz[1]
    non_edges = np.zeros((user_num*edge_num, 3), int) # edge line, edge id, user id
    non_edge_num = 0
    for u in range(user_num):
        user_id = u + 1
        for e in range(edge_num):
            if (edge_map[e, user_id-1] == 0):
                non_edges[non_edge_num,] = np.concatenate(([sym_edges[e, user_id-1]], [e+1], [user_id]))
                non_edge_num = non_edge_num + 1

    non_edges = non_edges[0:non_edge_num,]
    
    # map a long ftrack to multiple edges
    [trk_map, edge_map] = track_edge_recheck(non_tracks, non_edges, ftracks, trk_map, edge_map, chirp_len, ftrk_pwr)

    # second round track-->edge mapping
    # get all long tracks for candidate
    span_ratio = config.TRK_SPAN_RATIO
    LONG_TRACK_LEN_THRESHOLD = 2*chirp_len*span_ratio
    sz = trk_map.shape
    trk_num = sz[0]
    non_tracks = np.zeros((trk_num, 1), int)
    non_trk_num = 0
    for t in range(trk_num):
        trk = ftracks[t,]
        trk_len = trk[2] - trk[1]
        if (trk_map[t] >= 0 and trk_len > LONG_TRACK_LEN_THRESHOLD): # difference with the first round
            non_tracks[non_trk_num] = t
            non_trk_num = non_trk_num + 1

    non_tracks = non_tracks[0:non_trk_num]
    
    # get all non-assigned edges
    sz = edge_map.shape
    edge_num = sz[0]
    user_num = sz[1]
    non_edges = np.zeros((user_num*edge_num, 3), int) # edge line, edge id, user id
    non_edge_num = 0
    for u in range(user_num):
        user_id = u + 1
        for e in range(edge_num):
            if (edge_map[e, user_id-1] == 0):
                non_edges[non_edge_num,] = np.concatenate(([sym_edges[e, user_id-1]], [e+1], [user_id]))
                non_edge_num = non_edge_num + 1

    non_edges = non_edges[0:non_edge_num,]
    
    # map a long ftrack to multiple edges
    [trk_map, edge_map] = track_edge_recheck(non_tracks, non_edges, ftracks, trk_map, edge_map, chirp_len, ftrk_pwr)
    
    return trk_map, edge_map

def track_edge_recheck(non_tracks, non_edges, ftracks, trk_map, edge_map, chirp_len, ftrk_pwr):

    sz = non_edges.shape
    non_edge_num = sz[0]
    
    # mapping medium-length ftracks to multiple edges   
    USE_POWER_METRIC = 0
    
    for e in range(non_edge_num):
        edge = non_edges[e,]
        edge_line = edge[0]
        
        edge_tracks = tracks_on_edge(non_tracks, edge_line, ftracks)
        
        sz = edge_tracks.shape
        etrk_num = sz[0]
        max_pwr = 0
        max_trk = np.zeros((1, 4))
        max_len = 0
        longest_trk = np.zeros((1, 4))
        for t in range(etrk_num):
            track = edge_tracks[t,]
            
            [res, span_ratio] = track_edge_relation(track, edge_line, chirp_len)

            if (res > 0):    # the track can be grouped to the edge
                if (USE_POWER_METRIC > 0):
                    trk_fbin = track[0]
                    trk_pwr = ftrk_pwr[trk_fbin, edge_line]
                    if (trk_pwr > max_pwr):
                        max_pwr = trk_pwr
                        max_trk = track
                else: # (USE_POWER_METRIC == 0)
                    trk_len = span_ratio
                    if (trk_len > max_len):
                        max_len = trk_len
                        longest_trk = track
        
        # produce the results of track-->edge mapping 
        if (USE_POWER_METRIC > 0):
            if (max_pwr > 0):
                edge_user = edge[2]
                edge_idx = edge[1]
                trk_idx = max_trk[3]

                trk_map[trk_idx] = edge_user
                edge_map[edge_idx-1, edge_user-1] = trk_idx
        else: # (USE_POWER_METRIC == 0):       
            if (max_len > 0):
                edge_user = edge[2]
                edge_idx = edge[1]
                trk_idx = longest_trk[3]

                trk_map[trk_idx] = edge_user
                edge_map[edge_idx-1, edge_user-1] = trk_idx
    return trk_map, edge_map

def tracks_on_edge(non_tracks, edge_line, ftracks):

    ntrk_num = non_tracks.size
    
    edge_tracks = np.zeros((ntrk_num, 4), int)   # [fftbin, pos_st, pos_ed, index in ftracks]
    etrk_num = 0
    
    for n in range(ntrk_num):
        trk_id = non_tracks[n]
        track = ftracks[trk_id,]
        
        trk_st = track[:, 1]
        trk_ed = track[:, 2]
        
        if (edge_line >= trk_st and edge_line <= trk_ed):
            edge_tracks[etrk_num,] = np.concatenate((track, trk_id[np.newaxis]), axis = 1)
            etrk_num = etrk_num + 1
    
    edge_tracks = edge_tracks[0:etrk_num,]
    
    return edge_tracks

def track_edge_relation(track, edge, chirp_len):

    RANGE_THRESHOLD = config.TRK_SPAN_RATIO
    dn_chk_point = edge - chirp_len
    up_chk_point = edge + chirp_len
    
    trk_st = track[1]
    trk_ed = track[2]
    
    range_st = np.max(np.concatenate(([dn_chk_point], [trk_st])))
    range_ed = np.min(np.concatenate(([up_chk_point], [trk_ed])))
    
    range_ratio = (range_ed-range_st)/(up_chk_point - dn_chk_point)
    
    if (range_ratio > RANGE_THRESHOLD):
        res = 1
    else:
        res = 0
    
    return res, range_ratio
