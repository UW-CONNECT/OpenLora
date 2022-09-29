#!/usr/bin/env python3

import sys
import CoLoRa.frame_funcs as ff
import argparse
import config as main_config
import CoLoRa.io_funcs as iof
import math
import multiprocessing
import numpy as np
import os
import CoLoRa.symb_funcs as sf
import time

from CoLoRa.classes import CWin, CPacket, CSymbol

# def ind_vals(arr, thresh, num_pts):
#     out = []
#     for i in range(num_pts):
#         idx = np.argmax(arr)
#         if arr[idx] < thresh:
#             return out
#         else:
#             out.append(idx)
#             arr[idx] = 0
#     return out

# Find start of preambles with correlation
# def UC_location_corr(Data, N, num_preamble, DC, called_i, upsamp_factor, samp, overlap):
#     upchirp_ind = []
#     tmp_window = []
#     DC_sum = sum(DC[0:N] * np.conj(DC[0:N]))
#     for i in range(len(Data) - len(DC)):
#         tmp_window.append(sum(Data[i:i+N] * DC[0:N]) /
#             np.sqrt(sum(Data[i:i+N] * np.conj(Data[i:i+N])) *
#             DC_sum))
#
#     n_samp_array = []
#     peak_ind_prev = []
#     for i in range(math.floor(len(tmp_window)/N)):
#         window = np.abs(tmp_window[i*N : (i+1)*N])
#         peak_ind_curr = ind_vals(window, 0.2, 16)
#
#         if len(peak_ind_prev) != 0 and len(peak_ind_curr) != 0:
#             for j in range(len(peak_ind_curr)):
#                 for k in range(len(peak_ind_prev)):
#                     if peak_ind_curr[j] == peak_ind_prev[k]:
#                         n_samp_array.append(peak_ind_prev[k] + (i-1)*N)
#         peak_ind_prev = peak_ind_curr
#
#     for i in range(len(n_samp_array)):
#         c = 0
#         ind_arr = np.arange(0, (num_preamble-2)*N, N) + (n_samp_array[i] + N)
#
#         for j in range(len(ind_arr)):
#             c = c + np.sum(n_samp_array[:] == ind_arr[j])
#
#         if c >= (num_preamble-2):
#             upchirp_ind.append(n_samp_array[i])
#
#     temp = []
#     if len(upchirp_ind) != 0:
#         temp.append(upchirp_ind[0])
#         for i in range(1, len(upchirp_ind)):
#             if (np.min(np.abs(upchirp_ind[i] - temp[:])) > 5):
#                 temp.append(upchirp_ind[i])
#     if len(temp) != 0:
#         return [int(idx * upsamp_factor + max(called_i*samp-overlap, 0)) for idx in temp]
#     return temp

def main(raw_data, Fs, BW, SF, payload_num, preamble_ind):
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true', help='Print stuff')

    args = parser.parse_args()
    global_start = time.time()
    nsamp = Fs * 2**SF // BW
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
    #
    #
    # for i in range(chunks):
    #      mdata = np.array(raw_data[max(int(i*samp - overlap), 0):int((i+1)*samp)])[::int(upsampling_factor)]
    #      preamble = UC_location_corr(mdata, N, num_preamble, DC[::int(upsampling_factor)], i, upsampling_factor, samp, overlap)
    #      if preamble != []:
    #          if preamble_ind == []:
    #              preamble_ind = np.array(preamble)
    #          else:
    #              preamble_ind = np.concatenate((preamble_ind, np.array(preamble)))

    demod_symbols = []
    # Run CoLoRa for each detected preamble

    for indice in preamble_ind:
        
        mdata = raw_data[(indice - int(nsamp/2)): indice + int((pkt_len + 1) * nsamp)]

    # Start

        num_wins = math.ceil(len(mdata) / nsamp)
        windows = [CWin(i) for i in range(num_wins)]

        # Pad mdata
        pad = np.zeros(int(nsamp*num_wins - len(mdata)), np.complex64)
        mdata = np.append(mdata,pad)
        
        for i in range(num_wins):
            #windows[i] = CWin(i)
            symb = mdata[int(i*nsamp):int(i*nsamp+nsamp)]
            
            if(i == 0):
                symb_pre = np.zeros((nsamp))
            else:
                symb_pre = mdata[int((i-1)*nsamp):int(i*nsamp)]
                
            if(i == num_wins-1):
                symb_follow = np.zeros((nsamp))
            else:
                symb_follow = mdata[int((i+1)*nsamp):int((i+2)*nsamp)]
                
            pks = sf.peak_detect(symb, symb_pre, symb_follow)
            for pk in pks:
                windows[i].addPeak(pk)

        ## Calculate peak ratios for each peak
        symbols = [CWin(i) for i in range(num_wins)]
        for pk in windows[0].symset:
            symbols[0] = CWin(0)
            symbols[0].addPeak(CSymbol(pk.freq, pk.height, nsamp, np.inf))

        for i in np.arange(1, num_wins):
            symbols[i] = CWin(i)
            for pk in windows[i].symset:
                pk_ratio = sf.pair(pk, windows[i-1])
                symbols[i].addPeak(CSymbol(pk.freq, pk.height, nsamp, pk_ratio))

        ## Detect LoRa frames by sync words
        start_win, bin_value = ff.detect(symbols, num_preamble, args.verbose)

        if not start_win:
            #print('ERROR: No packet is found!!!\n')
            continue

        start_win = [0] # The window selection ensures this
        bin_value = [bin_value[0]]

        ## Detect STO and CFO for each frame
        packet_set = [CPacket(0, 0, 0)] * len(start_win)

        for i in range(len(start_win)):
            if args.verbose == True:
                print(f'y({start_win[i]}),value({bin_value[i]:.1f})')

            offset = round(bin_value[i] / 2**SF * nsamp)

            upsig = mdata[(start_win[i]+2+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) : (start_win[i]+2+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) + int(nsamp)]
            downsig = mdata[(start_win[i]+9+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) : (start_win[i]+9+1)*int(nsamp) + round(bin_value[i] / 2**SF * nsamp) + int(nsamp)]
            cfo,sto = ff.cal_offset(upsig, downsig)

            sto = np.remainder(np.round(sto*Fs+offset+.25*nsamp), nsamp)
            packet_set[i] = CPacket(start_win[i],cfo, sto)

        ## Group each symbol to corresponding TX node
        if os.path.exists('output') == False:
            os.mkdir('output')
            
        outfile = 'output/result.csv'
        if os.path.exists(outfile):
            os.remove(outfile)

        iof.write_text(outfile, f'{len(packet_set)}\n')
        iof.write_text(outfile, f'window,bin,offset,len,amplitude,belong,value')

        code_array = np.zeros((len(packet_set), num_data_sym*2))
        for w in symbols:
            symset = sf.group(w.symset, packet_set, w.ident, num_preamble, args.verbose)

            if args.verbose == True:
                print(f'Window({windows[i].ident})')

            for s in symset:
                if args.verbose == True:
                    s.show()

                sto = nsamp - packet_set[s.pkt_id].to
                cfo = 2**SF * packet_set[s.pkt_id].cfo / BW

                value = np.mod(2**SF - s.fft_bin - sto/nsamp*2**SF - cfo, 2**SF)
                code_array[s.pkt_id, w.ident-10] = round(value)

                if args.verbose == True:
                    print(f'\t\t     value = {round(value)}')
                s.write_file(outfile, w.ident, s.pkt_id, round(value))

        pckts = ff.show(outfile, True)

        end_time = time.time()

        if demod_symbols == []:
            demod_symbols = np.array(pckts)
        else:
            demod_symbols = np.vstack((demod_symbols, np.array(pckts)))

    global_end = time.time()

    print(f'Demodulator: CoLoRa; Time taken = {global_end - global_start} seconds')
    return demod_symbols
if __name__ == '__main__':
    main()
