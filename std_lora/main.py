#!/usr/bin/env python3

import numpy as np
import time
from std_lora.pkt_detection import pkt_detection
from std_lora.lora_demod import lora_demod

def main(raw_data, Fs, BW, SF, payload_num):
    
    # chirp variables
    N = int(2**SF)
    upsampling_factor = Fs//BW
    
    # generating LORA pkts
    if SF == 12:
        num_preamble = 7
    else:
        num_preamble = 8
    num_sync = 2
    preamble_sym = 1
    num_data_sym = payload_num
    num_DC = 2.25
    pkt_len = num_preamble + num_DC + num_data_sym + 2
    num_samples = pkt_len * N
    if raw_data.ndim == 1:
        x_1 = raw_data[:, np.newaxis]

    global_start = time.time()
    Preamble_ind = pkt_detection(x_1,N,upsampling_factor,num_preamble)
    demod_sym = lora_demod(x_1,N,upsampling_factor,num_preamble,num_sync,num_DC,num_data_sym,Preamble_ind,0)
    global_end = time.time()

    print(f'Demodulator: Std-LoRa; Time taken = {global_end - global_start} seconds')
    return demod_sym
if __name__ == '__main__':
	main()
