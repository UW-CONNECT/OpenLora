#!/usr/bin/env python3

import config as main_config
import CoLoRa.config as config
import csv
import numpy as np
import CoLoRa.peak_funcs as pf
import CoLoRa.symb_funcs as sf

from CoLoRa.classes import CWin, CSymbol
from scipy.fft import fft

def spectrum(data, window=512, overlap=256, nfft=2048,
                   Fs=main_config.RX_Sampl_Rate):
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    if Fs <= BW*2:
        window = 64
        overlap = 60
        nfft = 2048

def detect(winset, num_preamble, verbose=False):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF
    nsamp = Fs * 2**SF / BW

    start = []
    value = []

    state_dict = {}
    pending_keys = {}

    for i in range(0, len(winset)):
        if verbose:
            print(f'window({i})')

        state_keys = list(state_dict)
        update_keys = {}
        for k in state_keys:
            update_keys[k] = 0

        if verbose:
            print(f'Keys:', end='')
            for k in state_keys:
                print(f' {round(k)}', end='')
            print(f'\n', end='')


        symbset = winset[i].symset
        if verbose:
            print(f'symbs:', end='')
            for k in symbset:
                print(f' {round(k.fft_bin)}', end='')
            print('\n', end='')

        for sym in symbset:
            # Detect consecutive preambles
            I, key = pf.nearest(np.array(state_keys), sym.fft_bin, 2)
            if I < 0:
                state_dict[sym.fft_bin] = 1
            else:
                # Guaranteed to exist
                state_dict[key] += 1
                update_keys[key] = 1
                if state_dict[key] >= 5:
                    if verbose:
                        print(f"Set pending key for key {key}")
                    pending_keys[key] = 10

            # Detect the first sync word (8)
            I, key = pf.nearest(np.array(state_keys), np.mod(sym.fft_bin + config.SW1, 2**SF), 2)
            if I >= 0 and key in pending_keys:
                if verbose:
                    print(f'SYNC-1: {round(key)}')
                pending_keys[key] = 10
                state_dict[key] += 1
                update_keys[key] = 1

            # Detect the second sync word (16)
            I, key = pf.nearest(np.array(state_keys), np.mod(sym.fft_bin + config.SW2, 2**SF), 2)

            # Short-circuits if second condition isn't true so never
            # have missing key exception
            if I >= 0 and key in pending_keys and pending_keys[key] > 5:
                if verbose:
                    print(f'SYNC-2: {round(key)}\t Frame Detected')
                start.append(i-(num_preamble+1))
                value.append(key)
                del pending_keys[key]
                update_keys[key] = 0

        for key in state_keys:
            if key in pending_keys and pending_keys[key] > 0:
                if update_keys[key] == 0:
                    pending_keys[key] -= 1
                    update_keys[key] = 1

            if update_keys[key] == 0:
                del state_dict[key]
                if verbose:
                    print(f'\tRemove {key:.2f} from table')

    return start, value

def cal_offset(upsig, downsig):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF
    nsamp = Fs * 2**SF / BW

    # input signal has been roughly synchronized
    dn_chp = sf.gen_normal(0, True)
    dn_chp = dn_chp.reshape((dn_chp.size))
    match_tone = np.multiply(upsig, dn_chp)
    nfft = match_tone.size*320
    fout = fft(match_tone, nfft)
    upz = sf.freq_alias(fout)

    num_bins = upz.size
    freq_idx = np.arange(0, num_bins, dtype = float) * BW/num_bins

    # Peaks in the range of...
    reta_rang = round(2e3/BW * num_bins)
    upz[reta_rang:-reta_rang] = 0

    idx = np.argmax(np.abs(upz))
    upf = freq_idx[idx]

    # Peak frequency of down chirp
    up_chp = sf.gen_normal(0, False)
    up_chp = up_chp.reshape((up_chp.size))
    match_tone = np.multiply(downsig, up_chp)
    fout = fft(match_tone, nfft)
    dnz = sf.freq_alias(fout)

    num_bins = dnz.size
    freq_idx = np.arange(0, num_bins, dtype = float) * BW/num_bins

    reta_rang = round(2e3/BW * num_bins)
    dnz[reta_rang:-reta_rang] = 0

    idx = np.argmax(np.abs(dnz))
    dnf = freq_idx[idx]

    if dnf > 2e3:
        dnf = dnf - BW
    if upf > 2e3:
        upf = upf - BW
    cfo = (upf + dnf) / 2

    sto = (dnf - cfo) / BW * (2**SF/BW)

    return cfo, sto

def show(outfile, verbose=False):
    max_payload = main_config.Max_Payload_Num
    value = []
    symb = []
    frame_num = 0
    with open(outfile, 'r') as f:
        freader = csv.reader(f)

        frame_num = int(next(freader)[0])

        # Skip header
        next(freader)

        value = [[] for i in range(frame_num)]
        symb = [[] for i in range(frame_num)]
        for line in freader:
            # Maybe there's a better way than hard-coding
            idx = int(line[4])
            value[idx].append(int(line[5]))
            symb[idx].append(float(line[2]))
    pckt_array = []
    for loop in range(0, frame_num):
        var = value[loop]
        length = symb[loop]

        ST = [1,0]
        ED = [len(length), 0]

        for loop2 in range(len(length)):
            if length[loop2] > 0 and ST[1] == 0:
                ST[0] = loop2
                ST[1] = 1

            if length[len(length) - loop2 - 1] > 0 and ED[1] == 0:
                ED[0] = len(length) - loop2
                ED[1] = 1

        ED = min(ED[0], ST[0]+max_payload)
        tmp = var[ST[0]:ED]
        #if verbose:
            #print(f'Packet: ', end='')
            #for blah in tmp:
                #print(f'{blah}, ', end='')
            #print('END')
        pckt_array.append(tmp)
    return pckt_array
