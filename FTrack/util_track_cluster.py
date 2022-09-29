import numpy as np
import FTrack.config as config

def util_track_cluster(tracks, fft_size):

    sz = tracks.shape
    trk_num = sz[0]
    
    # sort tracks based on fbin
    #[tracks_sorted, trk_indexes] = sortrows(tracks, [1 2 -3])
    trk_indexes = tracks[:,0].argsort()
    tracks_sorted = tracks[trk_indexes,]
    
    clusters = np.zeros((trk_num, 4), int)   # [lower fbin, upper fbin, tm_st, tm_ed] for each cluster
    clst_num = 0
    
    trk_cluster_tbl = np.zeros((trk_num, 1), int)
    for t in range(trk_num):
        trk = tracks_sorted[t,]
        origin_trk_id = trk_indexes[t]
        
        # check if trk belongs to an existing cluster
        exist = 0
        for c in range(clst_num):
            cluster = clusters[c,]
            
            [rel, cluster_new] = track_cluster_relation(trk, cluster, fft_size)
            if (rel >= 0):
                exist = 1
                trk_cluster_tbl[origin_trk_id] = c # record which cluster trk belongs to
                
                if (rel == 0):   # near the cluster border
                    # expand the cluster, update the cluster
                    clusters[c,] = cluster_new
                break
        
        if (exist <= 0): # trk not belong to any existing clusters
            # create a new cluster
            clusters[clst_num,] = np.concatenate(([trk[0]], trk))
            trk_cluster_tbl[origin_trk_id] = clst_num # record which cluster trk belongs to
            clst_num = clst_num + 1
    
    clusters = clusters[0:clst_num,]
    
    return clusters, trk_cluster_tbl

def track_cluster_relation(trk, cluster, fft_size):
# rel: in cluster (1), out but near cluster borders (0), out and far away
# from cluster (-1)
    
    FBIN_TOLERANCE = config.TRK_CLUSTER_FREQ_TOLERANCE
    OVERLAP_RATIO = config.TRK_CLUSTER_OVERLAP_RATIO
    
    # track: [fbin, tm_st, tm_ed]
    # cluster: [lower fbin, upper fbin, tm_st, tm_ed]
        
    # compare track and cluster in time domain
    union_trk = np.concatenate(([min(trk[1], cluster[2])], [max(trk[2], cluster[3])]))
    intersec_trk = np.concatenate(([max(trk[1], cluster[2])], [min(trk[2], cluster[3])]))
    
    union_len = union_trk[1] - union_trk[0] + 1
    intersec_len = intersec_trk[1] - intersec_trk[0] + 1   # < 0 when not intersect
    
    trk_len = trk[2] - trk[1] + 1
    cluster_len = cluster[3] - cluster[2] + 1
    
    overlap_ratio = intersec_len / union_len
    overlap1_ratio = intersec_len / trk_len
    overlap2_ratio = intersec_len / cluster_len
    
    if (overlap_ratio > OVERLAP_RATIO or overlap1_ratio > OVERLAP_RATIO or overlap2_ratio > OVERLAP_RATIO):
        overlap_in_time = 1
    else:
        overlap_in_time = 0
    
    if (overlap_in_time <= 0):
        rel = -1
        cluster_new = cluster
        return rel, cluster_new
    
    # compare track and cluster in freq domain
    fbin_trk = trk[0]
    cfbin_lw = cluster[0]
    cfbin_up = cluster[1]
    if (cfbin_up < cfbin_lw):
        cfbin_up = cfbin_up + fft_size
        
        if (fbin_trk < cfbin_up):
            fbin_trk = fbin_trk + fft_size
    
    if (fbin_trk >= cfbin_lw and fbin_trk <= cfbin_up):
        rel = 1
        cluster_new = np.concatenate((cluster[0:1], union_trk))
        return
    
    # compute the distance between trk and the cluster borders
    dist_lw = abs(trk[0] - cluster[0])
    dist_up = abs(trk[0] - cluster[1])
    if (dist_lw > fft_size/2):
        dist_lw = fft_size - dist_lw

    if (dist_up > fft_size/2):
        dist_up = fft_size - dist_up

    if (dist_lw <= FBIN_TOLERANCE or dist_up <= FBIN_TOLERANCE):
        rel = 0
        
        if (dist_lw <= FBIN_TOLERANCE and dist_up > FBIN_TOLERANCE):
            cluster_new = np.concatenate(([trk[0]], [cluster[1]], union_trk))
        else:
            cluster_new = np.concatenate(([cluster[0]], [trk[0]], union_trk))

    else:
        rel = -1
        cluster_new = cluster

    return rel, cluster_new
