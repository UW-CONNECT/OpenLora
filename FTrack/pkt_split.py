import numpy as np

def pkt_split(pkt_bndrs, max_window_length, window_overlap):
    # Function to split large active session windows in a binary fashion.
    # Each active session that is larger than the max_window_length will be
    # continually divided until it meets this cutoff. Split up sessions
    # will be overlapping (# of overlap samples = window_overlap) the
    # adjacent chunks in order to detect the packets that are sliced in the
    # middle
    # Note: max_window_length is expected to be larger than window_overlap,
    # undefined bahavior will occur otherwise.

    i = 0
    while i < len(pkt_bndrs):
        if(abs(pkt_bndrs[i, 1] - pkt_bndrs[i, 0]) > max_window_length):  # need to split window in half
            length = abs(pkt_bndrs[i, 1] - pkt_bndrs[i, 0]) // 2               # get bisected length
            win1_end = int(np.ceil(pkt_bndrs[i, 0] + length + (window_overlap // 2)))        # add overlap to each half
            win2_start = int(np.floor(pkt_bndrs[i, 1] - length - (window_overlap // 2)))
            if i > 0:
                pkt_bndrs = np.concatenate((pkt_bndrs[0:i,:], np.array([pkt_bndrs[i,0], win1_end])[np.newaxis,:], np.array([win2_start, pkt_bndrs[i,1]])[np.newaxis,:], pkt_bndrs[i+1:,:])) # bisect the window
            else:
                pkt_bndrs = np.concatenate((np.array([pkt_bndrs[i,0], win1_end])[np.newaxis,:], np.array([win2_start, pkt_bndrs[i,1]])[np.newaxis,:], pkt_bndrs[i+1:,:]))
            i = i - 1  # see if the first bisected half is within the max window length
        i = i + 1
    return np.array(pkt_bndrs)
