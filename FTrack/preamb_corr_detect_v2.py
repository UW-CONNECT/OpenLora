import numpy as np
from FTrack.chirp_template_v2 import chirp_template_v2

def preamb_corr_detect_v2(preamble, num_symb):

    [up_chirp, down_chirp] = chirp_template_v2(num_symb, 0)

    target_len = num_symb
    tgt_st = 0
    tgt_ed = tgt_st + target_len
    target = up_chirp[tgt_st:tgt_ed] # the target pattern to detect

    pos_num = preamble.size - target_len + 1
    coef_val = np.zeros((pos_num, 1))
    for pos_st in range(pos_num):
        pos_ed = pos_st + target_len
        seg = preamble[pos_st:pos_ed]
        
        R = np.corrcoef(seg, target, rowvar = False)
        coef_val[pos_st] = abs(R[0,1])

    return coef_val
