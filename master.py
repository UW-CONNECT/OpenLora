#!usr/bin/env python3

import numpy as np
import config
import demod
import metrics

def main():
    Fs = config.RX_Sampl_Rate
    BW = config.LORA_BW
    SF = config.LORA_SF
    payload_num = config.Max_Payload_Num
    out_file = config.output_file
    # Load raw signal
    raw_data = np.fromfile(config.input_file, np.complex64)
    print(f'Data Samples: {raw_data.size/1e6} million; SF = {SF}; BW = {BW/1e3} kHz')

    # Demodulate symbols
    symbols = demod.std_lora(raw_data, Fs, BW, SF, payload_num)
    # Decode message and find error metrics
    if symbols != []:
       metrics.calculate(symbols, out_file, 'std_lora')
    else:
       print('No symbols found')

    symbols = demod.cic(raw_data, Fs, BW, SF, payload_num)
    if symbols != []:
        metrics.calculate(symbols, out_file, 'cic')
    else:
       print('No symbols found')

    # Find preamble with correlation
    import multiprocessing
    import math
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    temp_idx = []
    upsampling_factor = Fs//BW
    chunks = 20
    samp = math.floor(len(raw_data)/chunks)
    overlap = 8 * ((Fs * 2**SF) // BW)
    results = [pool.apply_async(demod.UC_location_corr, args=(np.array(raw_data[max(int(i*samp - overlap), 0):int((i+1)*samp)])[::int(upsampling_factor)], SF, BW, Fs, i, samp, overlap)) for i in range(chunks)]
    for r in results:
        ret = r.get()
        if len(ret) != 0:
            temp_idx.extend(ret)

    temp_idx = np.array(temp_idx)
    preamble_idx = []
    if len(temp_idx) != 0:
        preamble_idx.append(temp_idx[-1])
        for i in range(len(temp_idx)-2, -1,-1):
            if np.min(np.abs(temp_idx[i] - preamble_idx[:])) > 5*upsampling_factor*(2 ** SF):
                preamble_idx.append(temp_idx[i])
    preamble_idx.reverse()
    preamble_idx = np.array(preamble_idx)

    symbols = demod.colora(raw_data, Fs, BW, SF, payload_num, preamble_idx)
    if symbols != []:
        metrics.calculate(symbols, out_file, 'colora')
    else:
       print('No symbols found')

    symbols = demod.nscale(raw_data, Fs, BW, SF, payload_num, preamble_idx)
    if symbols != []:
       metrics.calculate(symbols, out_file, 'nscale')
    else:
      print('No symbols found')

    # symbols = demod.ftrack(raw_data, Fs, BW, SF, payload_num)#, preamble_idx)
    # if symbols != []:
    #     metrics.calculate(symbols, out_file, 'ftrack')
    # else:
    #     print('No symbols found')

if __name__ == '__main__':
    main()
