import numpy as np
import config as main_config
# LoRa PHY transmitting parameters
LORA_SF = main_config.LORA_SF         # LoRa spreading factor
#LORA_BW = 250e3        # LoRa bandwidth

# Receiving device parameters
#RX_Sampl_Rate = 1*1e6  # recerver's sampling rate

# LoRa frame parameters
FRM_PREAMBLE = 8       # number of chirps in preamble
FRM_SYNC = 2           # number of up chirps for sync words
FRM_SFD = 2.25         # number of down chirps in SFD
#FRM_PAYLOAD = 40       # number of payload symbols in the frame
FRM_SYNC_WORD_FREQ = 8 # frequency offset of the SYNC words

# freq track detecting configurations
TRK_FFT_factor = 1         # scale factor for FFT window size

TRK_PWR_THRESHOLD = 0      # (!!not use) threshold of FFT power for freq track detecting
TRK_SPAN_RATIO = 0.6       # threshold of track spanning ratio in ftrack detecting range
TRK_LEN_THRESHOLD = np.floor(2*TRK_SPAN_RATIO*(int(2)**LORA_SF))
                            # threshold of freq. track length
SYNC_TRK_LEN_SCALE_FACTOR = 0.7
                            # scale factor of sync word tracks, in
                            # relative to TRK_SPAN_RATIO
                            
TRK_PREAMBLE_MIN = 6       # minimum number of chirps for preamble detection
TRK_PREAMBLE_MAX = 10      # maximum number of chirps for preamble detection

# freq track duplication detecting
TRK_CLUSTER_FREQ_TOLERANCE = 2     # the tolerance of fft bin width for freq track clusters 
TRK_CLUSTER_EDGE_TOLERANCE = 4     # the tolerance of symbol edge offset
TRK_CLUSTER_OVERLAP_RATIO = 0.6    # threshold of track overlapping for duplication detecting

# preamble edge detecting
EDGE_CORRELATION_THRESHOLD = 0.8   # threshold of correlation coefficient for edge detecting
EDGE_SEARCH_RANGE = 2              # ranges (in number of chirps) for edge searching  
EDGE_ERROR_TOLERANCE = -1 * np.floor(0.01*(int(2)**LORA_SF))
                                    # the max tolerable error on edge detecting

# frame header (sync words) identifying
COLLIDE_HEADER_MODE = 1            # enable recovery from header sync words collision (1) or not (0)

# ftrack classifying/grouping
FTRK_GROUP_ALPHA = 0.8             # weight of track len (in relative to track power) for ftrack_grouping

# !!automatic threshold detection
AUTO_FBIN_WIN = 2**(LORA_SF-0)      # fft_bin window for adaptive threshold detecting
AUTO_TIME_WIN = 40 * 2**LORA_SF     # time window for threshold detecting
AUTO_PEAK_SAMPLE_STEP = 2**(LORA_SF-4)          
                                    # peak power sampling steps, 
                                    # 2**4 samples every chirp len

AUTO_HIGH_PEAK_RATIO = 0.7         # ratio of higher peaks for power threshold detecting
AUTO_PEAK_PWR_RATIO = 0.3          # ratio of power in the target peak

AUTO_PEAK_DIST = 3                # min distance between peaks for peak auto detecting
AUTO_NOISE_FLOOR = 1.0             # noise floor power

# coarse locations of preamble in a signal segment
PREAMBLE_ENDING_LOC = 0 #30 * 2**LORA_SF   # the position after which preamble cannot appear 
                                        # at most 20 symbols
                                        # when = 0, do not use this
                                        # parameter
