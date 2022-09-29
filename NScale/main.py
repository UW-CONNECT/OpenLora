#!/usr/bin/env python3

import sys
import NScale.frame_funcs as ff
import argparse
import NScale.config as config
import NScale.io_funcs as iof
import math
import multiprocessing
import numpy as np
import os
import NScale.symb_funcs as sf
import time

from NScale.classes import CWin, CPacket

def main(raw_data, Fs, BW, SF, payload_num, preamble_ind):
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true', help='Print stuff')

    args = parser.parse_args()
    global_start = time.time()
    nsamp = Fs * 2**SF / BW


    ## Section 1: Find preambles
    upsampling_factor = Fs / BW
    N = 2**SF

    if SF == 12:
        num_preamble = 7
    else:
        num_preamble = 8
    num_sync = 2
    preamble_sym = 1
    num_data_sym = payload_num
    num_DC = 2.25
    pkt_len = num_preamble + num_DC + num_data_sym + num_sync
    num_samples = pkt_len * nsamp

    DC = sf.gen_normal(0, True, Fs)
    DC = DC.reshape((DC.size))

    # chunks = 100
    # overlap = num_preamble * nsamp
    # samp = math.floor(len(raw_data)/chunks)
    # preamble_ind = []
    # preamble = []

    # pool = multiprocessing.Pool(multiprocessing.cpu_count())
    #
    # results = [pool.apply_async(UC_location_corr, args=(np.array(raw_data[max(int(i*samp - overlap), 0):int((i+1)*samp)])[::int(upsampling_factor)], N, num_preamble, DC[::int(upsampling_factor)], i, upsampling_factor, samp, overlap)) for i in range(chunks)]
    #
    # for r in results:
    #     ret = r.get()
    #     if len(ret) != 0:
    #         preamble_ind.extend(ret)
    # for i in range(chunks):
    #      mdata = np.array(raw_data[max(int(i*samp - overlap), 0):int((i+1)*samp)])[::int(upsampling_factor)]
    #      preamble = UC_location_corr(mdata, N, num_preamble, DC[::int(upsampling_factor)], i, upsampling_factor, samp, overlap)
    #      if preamble != []:
    #          if preamble_ind == []:
    #              preamble_ind = np.array(preamble)
    #          else:
    #              preamble_ind = np.concatenate((preamble_ind, np.array(preamble)))

    symbols = []
    # Run NScale for each detected preamble

    for indice in preamble_ind:
        
        #mdata = raw_data[(indice - int(nsamp)) : indice + int((pkt_len + 1) * nsamp)]
        mdata = raw_data[(indice - int(nsamp)) : indice + int((pkt_len + 1) * nsamp)]
    # Start

        ## Section 2: Detect symbol in-window distribution
        num_wins = math.ceil(len(mdata) / nsamp)
        windows = [CWin(i) for i in range(num_wins)]

        # Pad mdata
        pad = np.zeros(int(nsamp*num_wins - len(mdata)), np.complex64)
        mdata = np.append(mdata,pad)
        #symbs = [mdata[int(i*nsamp):int(i*nsamp+nsamp)] for i in range(num_wins)]
        #results = [pool.apply_async(sf.detect, args=(symbs[i], )) for i in range(num_wins)]
        #res = [r.get() for r in results]

        #for i in range(num_wins):
         #   for s in res[i]:
          #      windows[i].addSymbol(s)
           # if args.verbose:
            #    windows[i].show()

        for i in range(num_wins):
            symb = mdata[int(i*nsamp):int(i*nsamp+nsamp)]
            syms = sf.detect(symb)
            for s in syms:
                windows[i].addSymbol(s)

        ## Section 3: Detect LoRa frames by sync words
        start_win, bin_value = ff.detect(windows, num_preamble, args.verbose)

        if not start_win:
            #print('ERROR: No packet is found!!!\n')
            continue

        start_win = [1] #[start_win[0]]
        bin_value = [bin_value[0]]

        #if start_win[0] > 10 or start_win < 0:
            #continue

        ## Section 4: Detect STO and CFO for each frame
        packet_set = [CPacket(0, 0, 0)] * len(start_win)

        #results = [pool.apply_async(ff.cal_offset, args=(mdata[(start_win[i]+2+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) : (start_win[i]+2+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) + int(nsamp)], mdata[(start_win[i]+9+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) : (start_win[i]+9+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) + int(nsamp)])) for i in range(len(start_win))]

        #res = [r.get() for r in results]

        for i in range(len(start_win)):
            if args.verbose == True:
                print(f'y({start_win[i]}),value({bin_value[i]:.1f})')

            offset = round(bin_value[i] / 2**SF * nsamp)
            upsig = mdata[(start_win[i]+2+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) : (start_win[i]+2+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) + int(nsamp)]
            downsig = mdata[(start_win[i]+9+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) : (start_win[i]+9+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) + int(nsamp)]
            cfo,sto = ff.cal_offset(upsig, downsig)

            sto = np.remainder(np.round(sto*Fs+offset+.25*nsamp), nsamp)
            packet_set[i] = CPacket(start_win[i], cfo, sto)

        ## Section 5: Group each symbol to corresponding TX node
        if os.path.exists('output') == False:
            os.mkdir('output')
            
        outfile = 'output/result.csv'
        if os.path.exists(outfile):
            os.remove(outfile)

        iof.write_text(outfile, f'{len(packet_set)}\n')
        iof.write_text(outfile, f'window,bin,offset,len,amplitude,belong,value')

        #results = [pool.apply_async(sf.group, args=(w.symset, packet_set, w.ident, args.verbose)) for w in windows]

        #symsets = [r.get() for r in results]

        for w in windows:
            if args.verbose == True:
                print(f'Window({windows[i].ident})')

            symset = sf.group(w.symset, packet_set, w.ident, num_preamble)

            for s in symset:
                if args.verbose == True:
                    s.show()

                sto = nsamp - packet_set[s.pkt_id].to
                cfo = 2**SF * packet_set[s.pkt_id].cfo / BW

                value = np.mod(2**SF - s.fft_bin - sto/nsamp*2**SF - cfo, 2**SF)

                if args.verbose == True:
                    print(f'\t\t     value = {round(value)}')
                s.write_file(outfile, windows[i].ident, s.pkt_id, round(value))

        pckts = ff.show(outfile, True)

        end_time = time.time()

        if symbols == []:
            symbols = np.array(pckts)
        else:
            symbols = np.vstack((symbols, np.array(pckts)))

    global_end = time.time()
    print(f'Demodulator: NScale; Time taken = {global_end - global_start} seconds')
    return symbols
if __name__ == '__main__':
    main()
