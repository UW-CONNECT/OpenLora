import numpy as np

def active_sess_split(windows, max_window_length, window_overlap):
    # Function to split large active session windows in a binary fashion.
    # Each active session that is larger than the max_window_length will be
    # continually divided until it meets this cutoff. Split up sessions
    # will be overlapping (# of overlap samples = window_overlap) the
    # adjacent chunks in order to detect the packets that are sliced in the
    # middle
    # Note: max_window_length is expected to be larger than window_overlap,
    # undefined bahavior will occur otherwise.

    i = 0
    while i < len(windows):
        if(abs(windows[i, 1] - windows[i, 0]) > max_window_length):  # need to split window in half
            length = abs(windows[i, 1] - windows[i, 0]) // 2               # get bisected length
            win1_end = int(np.ceil(windows[i, 0] + length + (window_overlap // 2)))        # add overlap to each half
            win2_start = int(np.floor(windows[i, 1] - length - (window_overlap // 2)))
            if i > 0:
                windows = np.concatenate((windows[0:i,:], np.array([windows[i,0], win1_end])[np.newaxis,:], np.array([win2_start, windows[i,1]])[np.newaxis,:], windows[i+1:,:])) # bisect the window
                #windows[i+1, 0] = win2_start
            else:
                windows = np.concatenate((np.array([windows[i,0], win1_end])[np.newaxis,:], np.array([win2_start, windows[i,1]])[np.newaxis,:], windows[i+1:,:]))
                #windows[i+1, 0] = win2_start
            i = i - 1  # see if the first bisected half is within the max window length
        i = i + 1
    return np.array(windows)
