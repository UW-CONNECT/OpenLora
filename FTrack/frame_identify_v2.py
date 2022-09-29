import numpy as np
import FTrack.config as config
from FTrack.frame_preamble_identify import frame_preamble_identify
from FTrack.preamb_cluster import preamb_cluster
from FTrack.frame_sync_words_search import frame_sync_words_search
from FTrack.moving_offset_fft import moving_offset_fft
from FTrack.ftrack_detect import ftrack_detect
from FTrack.ftrack_preamble_detect_v2 import ftrack_preamble_detect_v2
from FTrack.preamb_reconstruct import preamb_reconstruct
from FTrack.preamb_corr_detect_v2 import preamb_corr_detect_v2
from FTrack.preamb_edge_detect_v2 import preamb_edge_detect_v2
from FTrack.preamb_edge_fitting import preamb_edge_fitting

def frame_identify_v2(preambles, preamb_idxes, trk_user_map, raw_signals, ftrack_pwr, ftracks, chirp_len, fft_size, pwr_thresholds):

    # filter out false preambles by searching for sync words
    [preambs_sync, trk_user_map, sync_words] = frame_preamble_identify(preambles, trk_user_map, ftrack_pwr, ftracks, chirp_len, fft_size)
    
    sz = preambs_sync.shape
    if (sz[0] <= 0):
        preambs_dedup = np.array([])
        sync_words = np.array([])
        return preambs_dedup, sync_words, trk_user_map
    
    # extract symbol edges on the signal segements of preambles
    # search for the signal segments of preambles
    [pamb_segs, pamb_sums] = signal_segments(preambs_sync, chirp_len)  
    
    sz = pamb_segs.shape
    seg_num = sz[0]
    
    pamb_edges = np.zeros(preambs_sync.shape, int)
    pamb_trks = np.zeros(preambs_sync.shape, int)
    pamb_num = 0
    for s in range(seg_num):
        seg_st = pamb_segs[s, 0]
        seg_ed = pamb_segs[s, 1]
        if (seg_ed > raw_signals.size):
            seg_ed = raw_signals.size

        preamb_signal_seg = raw_signals[seg_st:seg_ed+1]
        
        # use the outside threshold for track detecting
        lcal_threshold = local_pwr_threshold(np.concatenate(([seg_st], [seg_ed])), pwr_thresholds)
        
        # extract symbol edges
        edges = edge_detect_coef_comp(preamb_signal_seg, fft_size, lcal_threshold)
        edges[:, 0] = edges[:, 0] + seg_st
        
        # deal with the situation when (Number of edges) ~= (# of preambles in the segment)
        sz = edges.shape
        edge_num = sz[0]  # Number of detected edges
        if (edge_num > 0):
            # number of preambles in the segment
            pnum_expect = int(pamb_sums[s])
            if (pnum_expect > edge_num):
                p_num = edge_num
            else:
                p_num = pnum_expect

            # index ranges of preambles in preambs_sync
            p_idx_st = pamb_sums[0:s].sum()
            p_idx_ed = p_idx_st + p_num
            
            
            pamb_edges[pamb_num:pamb_num+p_num,] = np.concatenate((preambs_sync[p_idx_st:p_idx_ed, 0][:,np.newaxis], edges[0:p_num, :]), axis = 1)
            pamb_trks[pamb_num:pamb_num+p_num, :] = preambs_sync[p_idx_st:p_idx_ed,]
            pamb_num = pamb_num + p_num

    # cluster duplicate preambles based on detected edges
    pamb_edges = pamb_edges[0:pamb_num,]
    pamb_trks = pamb_trks[0:pamb_num,]
    preambs_dedup, preamb_trk = preamb_cluster(pamb_edges, pamb_trks, ftrack_pwr)
     
    # produce output parameters  
    NONE_USER_ID = -256
    sz = preambs_dedup.shape
    dedup_num = sz[0]
    
    # compute the precise locations of sync words
    sync_words = np.zeros((dedup_num, 1), int)
    for d in range(dedup_num):
        trk_pre = preambs_dedup[d,]
        user_id = d + 1
        
        [sync_edge_idx, trk_user_map] = frame_sync_words_search(ftracks, ftrack_pwr, trk_pre, user_id, trk_user_map, chirp_len, fft_size)
        sync_words[d] = sync_edge_idx

    # update the track_user_map
    sz = preambles.shape
    pre_num = sz[0]
    
    for p in range(pre_num):
        p_trk = preambles[p,]
        p_freq = p_trk[0]
        p_id = preamb_idxes[p]
        
        user_id = NONE_USER_ID
        for d in range(dedup_num):
            de_trk_freq = preambs_dedup[d, 0]
            
            # to handle when two preambles have the same fft bin
            edge_offset = preambs_dedup[d, 1] - p_trk[1]
            chirp_len = preambs_dedup[d, 2]
            
            if (de_trk_freq == p_freq and edge_offset < 2*chirp_len):
                user_id = d + 1
                break
        trk_user_map[p_id] = user_id

    return preambs_dedup, sync_words, trk_user_map

def edge_detect_coef_comp(preamb_signal_seg, num_symb, pwr_threshold):

    # parameter configuration
    FTRACK_LEN_MIN = config.TRK_LEN_THRESHOLD
    PREAMB_CHIRPS_MIN = config.TRK_PREAMBLE_MIN
    
    # determine the fft_bin of the preamble within the signal segment
    nfft = num_symb
    pamb_pwr = moving_offset_fft(preamb_signal_seg, num_symb, nfft)

    
    # ftrack detecting
    p_threshold = pwr_threshold
    trklen_threshold = FTRACK_LEN_MIN
    # detect freq. tracks
    pamb_tracks = ftrack_detect(pamb_pwr, p_threshold, trklen_threshold)
    
    # sort tracks in time order
    #ptracks_tm = sortrows(pamb_tracks, [2 3 1]) 
    ptracks_tm = pamb_tracks[pamb_tracks[:,1].argsort(),]
    
    sz = ptracks_tm.shape
    trk_num = sz[0]

    # detect preambles and chirp borders from long freq. tracks
    preamble_num_min = PREAMB_CHIRPS_MIN
    seg_preambs, seg_ids = ftrack_preamble_detect_v2(ptracks_tm, num_symb, preamble_num_min)

    # preamble deduplicate and sync words search
    tu_map = np.zeros((trk_num, 1))
    preambs_sync, trk_user_map, sync_words = frame_preamble_identify(seg_preambs, tu_map, pamb_pwr, ptracks_tm, num_symb, nfft)

    sz = preambs_sync.shape
    pamb_num = sz[0]
    
    edges = np.zeros((pamb_num, 2))
    if (pamb_num <= 0):
        return
    
    # preambs_sync has been sorted
    for p in range(pamb_num):
        pamb_trk = preambs_sync[p,]
        edge = edges_at_preamble(preamb_signal_seg, pamb_trk, num_symb, nfft)
        
        edges[p,] = edge[0:2].transpose()
        
    return edges

def edges_at_preamble(preamb_signal_seg, pamb_trk, num_symb, nfft):

    # filter out signals not belonging to the preamble
    # reconstruct the signal of the preamble
    pamb_bin = pamb_trk[0]
    pamb_offset = pamb_trk[1]
    ifft_preamble = preamb_reconstruct(preamb_signal_seg, num_symb, nfft, pamb_bin, pamb_offset)
    
    # detect chirp borders on the preamble
    coef_val = preamb_corr_detect_v2(ifft_preamble, num_symb)
    
    # detect chirp edges
    corr_threshold = config.EDGE_CORRELATION_THRESHOLD
    real_edges = preamb_edge_detect_v2(coef_val, corr_threshold)

    # when the number of detected edges exceeds the expected number of edges in a preamble
    expected_edges = config.FRM_PREAMBLE
    edge_num = real_edges.size
    if (edge_num > expected_edges):
        pos_st = edge_num-expected_edges+1
        real_edges = real_edges[pos_st:]
    
    # determine edge positions using the fitting method
    if (edge_num > 0):
        edge = preamb_edge_fitting(real_edges)
    else:
        edge = np.array([0, 0, 0])
        
    return edge

def local_pwr_threshold(thresh_range, thresholds):

    TM_WIN = config.AUTO_TIME_WIN
    mid_point = (thresh_range[0] + thresh_range[1])/2
    
    win_id = int(np.floor(mid_point/TM_WIN))
    
    sz = thresholds.shape
    win_num = sz[1]
    
    if (win_id > win_num):
        win_id = win_num
    
    pwr = np.mean(thresholds[:, win_id])
    
    return pwr

def signal_segments(preambs_sorted, chirp_len):

    sz = preambs_sorted.shape
    pamb_num = sz[0]
    if (pamb_num <= 0):
        return
    
    pamb_segs = np.zeros((pamb_num, 2), int)     #[tm_st, tm_ed]
    pamb_sums = np.zeros((pamb_num, 1), int)     # Number of preambles in each segment
    seg_num = 1
    
    pamb_segs[0,] = preambs_sorted[0, 1:3]
    pamb_sums[0] = 1
    for p in np.arange(1, pamb_num):
        trk = preambs_sorted[p,]
        trk_st = trk[1]
        trk_ed = trk[2]
        
        seg_ed = pamb_segs[seg_num-1, 1]
        if (trk_st <= seg_ed):
            # expand the current segment
            if (trk_ed > seg_ed):
                pamb_segs[seg_num-1, 1] = trk_ed
        else:
            # a new segment
            seg_num = seg_num + 1
            pamb_segs[seg_num-1,] = trk[1:3]
        
        # count the number of preambles in the segment
        pamb_sums[seg_num-1] = pamb_sums[seg_num-1] + 1
    
    pamb_segs = pamb_segs[0:seg_num,]
    pamb_sums = pamb_sums[0:seg_num]
    
    # to include potential sync words of the preambles
    sync_sig_len = 5*chirp_len
    pamb_segs[:, 1] = pamb_segs[:, 1] + sync_sig_len
    
    return pamb_segs, pamb_sums

