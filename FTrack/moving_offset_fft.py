import numpy as np
import math
from FTrack.chirp_template import chirp_template

def moving_offset_fft(signals, chirp_len, nfft):

    [up_chirp, down_chirp] = chirp_template(chirp_len)
    dn_chirp = down_chirp[0:chirp_len]
    
    sig_len = signals.size
    num_offsets = sig_len - (chirp_len-1)
    
    pwr = np.zeros((nfft, num_offsets))
    for offset in range(num_offsets):
        
        freq_pwr = dechirp_fft(signals, offset, dn_chirp, nfft)
        
        sig_pos = offset
        pwr[:, sig_pos] = freq_pwr.ravel()

    return pwr
    
def dechirp_fft(signals, offset, dn_chirp, nfft):

    chirp_len = dn_chirp.size
    target = np.zeros(dn_chirp.shape, complex)
    
    sig_st = offset
    sig_ed = offset + chirp_len
    if (sig_ed > signals.size):
        sig_ed = signals.size
        
    target[0:sig_ed-sig_st] = signals[sig_st:sig_ed]
    
    # dechirp
    de = target * dn_chirp
       
    # FFT on the first chirp len
    win_st = 0
    win_len = chirp_len
    
    fft_res = sliding_fft_v2(de, win_st, win_len, nfft)
    
    mag = abs(fft_res)
    
    # remove offset (freq. shift introduced by moving offset)
    # map fft bins to initial freq.
    freq_shift = (offset+chirp_len) % chirp_len
    fft_factor = nfft / chirp_len
    bin_shift = freq_shift * fft_factor
    
    freq_pwr = np.zeros(mag.shape)
    for fbin in range(nfft):
        idx = int((nfft + fbin - bin_shift) % nfft)
        #if (idx == 0):
            #idx = nfft
        
        freq_pwr[idx] = mag[fbin]

    return freq_pwr
    
def sliding_fft_v2(samples, win_st, win_len, nfft):

    win_ed = win_st+win_len-1
    if (win_ed > samples.size):
        win_ed = samples.size
    
    target_samp = samples[win_st:win_ed+1]
    
    Y = np.fft.fft(target_samp.transpose(), nfft)
    
    return Y.transpose()
