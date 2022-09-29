import numpy as np

def ftrack_detect(fpwr, p_threshold, tracklen_threshold):

    fpwr_template = fpwr > p_threshold
    fpwr = fpwr * fpwr_template
    
    sz = fpwr.shape
    fbin_num = sz[0]
    tm_max = sz[1]
    
    res = np.zeros((fbin_num*tm_max, 3), int)
    track_num = 0
    for f in range(fbin_num):    # for each fft bin
        track_on = 0
        track_pos_st = -1
        
        for tm in range(tm_max):
            # detect the start pos of a ftrack
            if (fpwr[f, tm] > 0 and track_on == 0):
                track_on = 1
                track_pos_st = tm
            
            # detect the end of a ftrack
            if ((fpwr[f, tm] == 0 or tm >= tm_max-1) and track_on == 1):
                track_on = 0
                track_pos_ed = tm-1
                if (tm >= tm_max and fpwr[f, tm] > 0):
                    track_pos_ed = tm
                
                # track length filter, filter out short false track 
                track_len = track_pos_ed - track_pos_st + 1
                if (track_len > tracklen_threshold):
                    # to detect the position of the highest power on the ftrack                    
                    # add the detected ftrack into the result
                    res[track_num,] = np.concatenate(([f], [track_pos_st], [track_pos_ed]))
                    track_num = track_num + 1
    
    res = res[0:track_num, :]
	
    return res


# detect the position of the highest power on the ftrack
def max_pos(seg):

    max_s = max(seg)
    for i in range(seg.size):
        if (seg[i] >= max_s):
            offset = i-1
            return

    offset = -1
    return offset
