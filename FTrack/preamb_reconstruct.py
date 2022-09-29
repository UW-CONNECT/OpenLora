import numpy as np
import FTrack.config as config
from FTrack.chirp_template import chirp_template
from FTrack.sliding_fft_v2 import sliding_fft_v2

def preamb_reconstruct(signals, chirp_len, nfft, reserve_bin, init_offset):

    [up_chirp, down_chirp] = chirp_template(chirp_len)
    dn_chirp = down_chirp[0:chirp_len]
    
    sig_len = signals.size
    num_offsets = sig_len - (chirp_len-1)
    # reduce the search range
    SEARCH_RANGE = (config.EDGE_SEARCH_RANGE)*chirp_len
    end_offset = init_offset + SEARCH_RANGE
    if (end_offset > num_offsets):
        end_offset = num_offsets
    
    # search for the starting point of the preamble
    coef_val = np.zeros((num_offsets, 1))
    max_corr = -10
    max_pos = 0
    first_pos = 0 
    
    coef_threshold = config.EDGE_CORRELATION_THRESHOLD
    coef_diff_min = 0.05
    
    for offset in np.arange(init_offset, end_offset+1):
        
        fft_res = dechirp_fft(signals, offset, dn_chirp, nfft, reserve_bin)
        
        ifft_res = np.fft.ifft(fft_res, axis = 0)
        target_sig = ifft_res[:] * up_chirp[0:chirp_len]
        
        R = np.corrcoef(target_sig, up_chirp[0:chirp_len], rowvar = False)
        
        # TODO: add abs() for real trace processing
        R = abs(R)
        
        pos_st = offset
        coef_val[pos_st] = R[0,1]
        if (R[0,1] - max_corr >= coef_diff_min):
            max_corr = R[0,1]
            max_pos = pos_st
        
        if (first_pos == 0 and R[0,1] > coef_threshold):
            first_pos = pos_st

    
    if (first_pos == 0):
        first_pos = max_pos
        if (max_pos == 0):
            first_pos = 1
    
    preamble_base = np.zeros((sig_len, 1), complex)
    for offset in np.arange(first_pos,end_offset+1,chirp_len):
        
        fft_res = dechirp_fft(signals, offset, dn_chirp, nfft, reserve_bin)
        
        ifft_res = np.fft.ifft(fft_res, axis = 0)
        target_sig = ifft_res[:]
        
        pos_st = offset
        pos_ed = pos_st+chirp_len
        preamble_base[pos_st:pos_ed] = preamble_base[pos_st:pos_ed] + target_sig
    
    # reconstruct the preamble signals
    preamble = np.zeros(preamble_base.shape, complex)
    for pos_st in np.arange(first_pos, end_offset+1, chirp_len):
        pos_ed = pos_st + chirp_len
        preamble[pos_st:pos_ed] = preamble_base[pos_st:pos_ed] * up_chirp[0:chirp_len]

    return preamble

def dechirp_fft(signals, offset, dn_chirp, nfft, reserve_bin):

    chirp_len = dn_chirp.size
    
    sig_st = offset
    sig_ed = 1+offset + chirp_len-1
    if (sig_ed > signals.size):
        sig_ed = signals.size

    target = signals[sig_st:sig_ed]
    
    # dechirp
    de = target * dn_chirp
    
    # FFT on the first chirp len
    win_st = 0
    win_len = chirp_len
    
    fft_res = sliding_fft_v2(de, win_st, win_len, nfft)
    
    # remove offset (freq. shift introduced by moving offset)
    # map fft bins to initial freq.
    freq_shift = (offset+chirp_len) % chirp_len
    fft_factor = nfft / chirp_len
    bin_shift = freq_shift * fft_factor
    
    for fbin in range(nfft):
        idx = (nfft + fbin - bin_shift) % nfft
        if (idx == 0):
            idx = nfft
        
        # filter out all bins other than the preamble
        if(idx != reserve_bin):
            fft_res[fbin] = 0

    return fft_res
