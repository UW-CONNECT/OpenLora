import numpy as np
from FTrack.util_track_cluster import util_track_cluster

def util_track_deduplicate(track_set, ftrack_pwr, fft_size):

    sz = track_set.shape
    trk_num = sz[0]
    
    [clusters, trk_cluster_tbl] = util_track_cluster(track_set, fft_size)
    
    sz = clusters.shape
    cl_num = sz[0]
    
    cluster_major_tracks = np.zeros((cl_num, 2), int)    # [track_id (i.e., index), track_pwr]
    for t in range(trk_num):
        trk = track_set[t,]
        trk_pwr = sum(ftrack_pwr[trk[0], trk[1]:trk[2]])
        
        cl_id = trk_cluster_tbl[t]
        if (cl_id < 0 or cl_id > cl_num-1):
            continue

        cl_maxpwr = cluster_major_tracks[cl_id, 1]
        if (trk_pwr > cl_maxpwr):    # track with the max power represent the whole cluster
            cluster_major_tracks[cl_id,] = np.concatenate(([t], [trk_pwr]))

    
    # produce output results
    dedup_tracks = np.zeros((cl_num, 3), int)
    dup_indicate_tbl = -1 * np.ones((trk_num, 1), int)
    
    for cl in range(cl_num):
        trk_id = cluster_major_tracks[cl, 0]
        
        dup_indicate_tbl[trk_id] = 0               # trk_id is not a duplicate track
        dedup_tracks[cl,] = track_set[trk_id,] # deduplicated track info
    
    return dedup_tracks, dup_indicate_tbl
