import config as main_config

def param_configs(id):
        # LoRa PHY transmitting parameters
    LORA_SF = main_config.LORA_SF #8#12;            # LoRa spreading factor
    LORA_BW = main_config.LORA_BW #250e3#125e3;        # LoRa bandwidth
    
    # Receiving device parameters
    Fs = main_config.RX_Sampl_Rate #2e6#125e3*8;  # recerver's sampling rate
    if LORA_SF == 12:
        num_preamble = 7
    else:
        num_preamble = 8
    num_sync = 2
    num_DC = 2.25
    num_data_sym = main_config.Max_Payload_Num
    
    DC_corr_threshold = 0.2        # Value to be calibrated based on Correlation plot's noise floor
    DC_corr_pnts_threshold = 40
    
    UC_corr_threshold = 0.1        # Value to be calibrated based on Correlation plot's noise floor
    UC_corr_pnts_threshold = 40
    SYNC1 = 8
    SYNC2 = 16
    
    switcher = {
        1: LORA_SF,
        2: LORA_BW,
        3: Fs,
        4: num_preamble,
        5: num_sync,
        6: num_DC,
        7: num_data_sym,
        8: DC_corr_threshold,
        9: DC_corr_pnts_threshold,
        10: UC_corr_threshold,
        11: UC_corr_pnts_threshold,
        12: SYNC1,
        13: SYNC2
    }
    
    return switcher[id]
