import numpy as np
import FTrack.config as config
from FTrack.util_fftpwr_peaks import util_fftpwr_peaks

def ftrack_fftpwr_preprocess(fft_pwr):

    sz = fft_pwr.shape
    bin_num = sz[0]
    col_num = sz[1]
    fpwr = np.zeros(sz)
    
    # load parameters from the configuration file
    min_peak_dist = config.AUTO_PEAK_DIST
    pwr_diff_threshold = config.AUTO_NOISE_FLOOR
    
    FBIN_WIN = config.AUTO_FBIN_WIN
    TIME_WIN = config.AUTO_TIME_WIN
    
    fft_pwr_cycle = np.concatenate([fft_pwr[bin_num-FBIN_WIN:bin_num,], fft_pwr, fft_pwr[0:FBIN_WIN,]])
    
    binw_num = int(np.ceil(bin_num/FBIN_WIN))
    tmw_num = int(np.ceil(col_num/TIME_WIN))
    pwr_thresholds = np.zeros((binw_num, tmw_num))
    tm_idx = 0
    for col in np.arange(0, col_num, TIME_WIN):
        col_st = col
        col_ed = col + TIME_WIN
        if (col_ed > col_num):
            col_ed = col_num

        bw_idx = 0
        for fbin in np.arange(0, bin_num, FBIN_WIN):
            bin_st = fbin
            bin_ed = fbin + FBIN_WIN
            if (bin_ed > bin_num):
                bin_ed = bin_num
            
            bincyc_st = (bin_st + FBIN_WIN) - FBIN_WIN
            bincyc_ed = (bin_ed + FBIN_WIN) + FBIN_WIN
            
            # get data in the target sub cell
            pwr_subcell = fft_pwr_cycle[bincyc_st:bincyc_ed, col_st:col_ed]
            
            # extract freq tracks in the local cell by adopting adaptive threshold
            [pwr_trks, local_threshold] = util_fftpwr_2D_filter(pwr_subcell, min_peak_dist, pwr_diff_threshold)
            
            # produce the results
            fpwr[bin_st:bin_ed, col_st:col_ed] = pwr_trks[FBIN_WIN:2*FBIN_WIN,]

            pwr_thresholds[bw_idx, tm_idx] = local_threshold
            bw_idx = bw_idx + 1

        tm_idx = tm_idx + 1

    return fpwr, pwr_thresholds

def util_fftpwr_2D_filter(fpwr, min_peak_dist, pwr_diff_threshold):

    sz = fpwr.shape
    col_num = sz[1]
    
    # load parameter from the configuration file
    PEAK_SAMPLE_STEP = config.AUTO_PEAK_SAMPLE_STEP
    HIGH_PEAK_RATIO = config.AUTO_HIGH_PEAK_RATIO
    PEAK_PWR_RATIO = config.AUTO_PEAK_PWR_RATIO
    NOISE_FLOOR = config.AUTO_NOISE_FLOOR
    #size = np.empty(619, int)
    count = 0
    # peak power statistics
    peaks_pwr_set = []
    for col in np.arange(0, col_num, PEAK_SAMPLE_STEP):
        pwr_c = fpwr[:, col]
        [peak_locs, peak_pwr] = util_fftpwr_peaks(pwr_c, min_peak_dist, pwr_diff_threshold)
        
        if (peak_pwr.size > 0):
            #size[count] = peak_pwr.size
            #count  = count + 1
            peaks_pwr_set = np.concatenate((peaks_pwr_set, peak_pwr))

    # automatically compute the threshold
    peaks_pwr_set = np.sort(peaks_pwr_set)
    pk_sampls = peaks_pwr_set.size
    pk_idx = int(np.floor(pk_sampls*(1-HIGH_PEAK_RATIO)))
    if (pk_idx < 1):
        pk_idx = 1
    
    # Adaptive/automatic threshold compute
    if (pk_sampls <= 0):
        pwr_threshold = NOISE_FLOOR
    else:
        # threshold compute
        ref_pwr = np.mean(peaks_pwr_set[pk_idx-1:])
        pwr_threshold = ref_pwr * PEAK_PWR_RATIO

    if (pwr_threshold < NOISE_FLOOR):
        pwr_threshold = NOISE_FLOOR

    template = (fpwr > pwr_threshold)
    
    trk_pwr = template * fpwr
    
    return trk_pwr, pwr_threshold
