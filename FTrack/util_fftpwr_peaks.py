import numpy as np
from scipy.signal import find_peaks

def util_fftpwr_peaks(fpwr, min_peak_dist, pwr_threshold):

    # for cyclic peak search
    pad = 2*min_peak_dist
    sz = fpwr.shape
    fft_size = sz[0]
    fftpwr_cycle = np.concatenate([fpwr[fft_size-pad:fft_size], fpwr, fpwr[0:pad]])
    
    # all possible peaks
    #[maxv, maxl] = findpeaks(fftpwr_cycle, 'minpeakdistance', min_peak_dist)
    maxl, properties = find_peaks(fftpwr_cycle, height = 0, distance = min_peak_dist)
    maxv = properties["peak_heights"]
    # peak candidates
    [cpeak_locs, cpeak_pwr] = pwr_peaks(maxl, maxv, pwr_threshold)
    
    # filter out the peaks locate out of the range 
    cpk_num = cpeak_locs.size
    
    peak_locs = np.zeros(cpeak_locs.shape)
    peak_pwr = np.zeros(cpeak_pwr.shape)
    peak_idx = 0
    for c in range(cpk_num):
        loc = cpeak_locs[c] - pad
        
        if (loc > 0 and loc <= fft_size):
            peak_locs[peak_idx] = loc
            peak_pwr[peak_idx] = cpeak_pwr[c]
            peak_idx = peak_idx + 1
    
    peak_locs = peak_locs[0:peak_idx]
    peak_pwr = peak_pwr[0:peak_idx]
	
    return peak_locs, peak_pwr

def pwr_peaks(pk_candies, pk_pwr, PWR_THRESHOLD):

    pk_num = pk_candies.size
    pwr_diff = pk_pwr - np.concatenate(([pk_pwr[pk_num-1]], pk_pwr[0:pk_num-1]))
    
    peak_locs = np.zeros(pk_candies.shape)
    peak_pwr = np.zeros(pk_candies.shape)
    peak_idx = 0
    
    climb = 0  # indicating peak climbing, not reached yet 
    for p in range(pk_num-1):
        dpwr_p = pwr_diff[p]
        dpwr_next = pwr_diff[p+1]
        
        if (dpwr_p > PWR_THRESHOLD):
            climb = 1
        
        if ((p == 1 and dpwr_next < -PWR_THRESHOLD) or (p == pk_num - 1 and climb == 1) or (climb == 1 and dpwr_next <= 0)):
            peak_locs[peak_idx] = pk_candies[p]
            peak_pwr[peak_idx] = pk_pwr[p]
            peak_idx = peak_idx + 1
            climb = 0

    peak_locs = peak_locs[0:peak_idx]
    peak_pwr = peak_pwr[0:peak_idx]
    
    return peak_locs, peak_pwr
