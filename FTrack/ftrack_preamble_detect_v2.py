import numpy as np
import FTrack.config as config

def ftrack_preamble_detect_v2(ftracks, chirp_len, preamble_num):

    sz = ftracks.shape
    track_num = sz[0]  # Number of tracks
    
    # select out all long tracks
    longtrack_threshold = chirp_len * (preamble_num+1)
    pamb_endingloc = config.PREAMBLE_ENDING_LOC
    
    long_tracks = np.zeros(sz, int)
    longtrack_num = 0
    trk_ids = np.zeros((track_num, 1), int)
    
    for t in range(track_num):
        track = ftracks[t,]
        
        # preamble location filter
        if (pamb_endingloc > 0 and track(2) > pamb_endingloc):
            continue
        
        track_len = track[2] - track[1] + 1
        if (track_len >= longtrack_threshold):
            long_tracks[longtrack_num,] = track[:]
            trk_ids[longtrack_num] = t
            longtrack_num = longtrack_num + 1

    long_tracks = long_tracks[0:longtrack_num, :]
    
    trk_ids = trk_ids[0:longtrack_num]
    preambles = long_tracks[:, 0:3]

    return preambles, trk_ids
