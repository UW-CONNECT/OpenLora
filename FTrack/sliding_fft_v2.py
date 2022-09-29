import numpy as np

def sliding_fft_v2(samples, win_st, win_len, nfft):

    win_ed = win_st + win_len
    if (win_ed > samples.size):
        win_ed = samples.size
    
    target_samp = samples[win_st:win_ed]
    
    Y = np.fft.fft(target_samp, nfft, axis = 0)
    return Y
