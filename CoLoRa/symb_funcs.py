#!/usr/bin/env python3

import config as main_config
import CoLoRa.config as config
import numpy as np
import CoLoRa.peak_funcs as pf

from CoLoRa.classes import CSymbol, CPacket, CPeak
from scipy.signal import chirp
from scipy.fft import fft

def peak_detect(sig, sig_pre, sig_follow):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    nsamp = int(Fs * 2**SF / BW)
    MAX_PK_NUM = config.Max_Peak_Num

    peaks = []
    threshold = 0

    for i in range(0,MAX_PK_NUM):
        # dechirping and fft
        dn_chp = gen_normal(0, True)
        dn_chp = dn_chp.reshape((dn_chp.size))
        match_tone = np.multiply(sig, dn_chp)
        station_fout = fft(match_tone, int(nsamp*10))

        # peak information
        pk_height = -1
        pk_index = 0
        pk_phase = 0

        # Iterative compensate phase rotation
        align_win_len = int(station_fout.size / (Fs/BW))

        pending_phase = np.arange(0, 20)*2*np.pi/20

        for p in pending_phase:
            targ = np.exp(1j * p) * station_fout[0:align_win_len] +\
            station_fout[-align_win_len:]

            if np.max(np.absolute(targ)) > pk_height:
                pk_index = np.argmax(np.absolute(targ))
                pk_height = np.absolute(targ)[pk_index]
                pk_phase = p
                targ_rec = targ

        # Threshold for peak detecting
        if i == 0:
            threshold = pk_height / 20
        else:
            if pk_height < threshold:
                break

        # Determine if peak is legitimate or duplicated
        repeat = False
        # Add 1 to pk_index because matlab is 1-indexed but python
        # is 0-indexed
        cbin = (1 - (pk_index+1)/align_win_len) * 2**SF
        rsym = 0

        for pk in peaks:
            if np.absolute(pk.fft_bin - cbin) < 2:
                rsym = pk.fft_bin
                repeat = True
                break

        if repeat:
            break
        
        # Peak refining for iterative cancellation
        # SL or SR
        dn_chp = np.kron(np.ones((1, 2)), gen_normal(0,True))
        yL = np.concatenate((sig_pre, sig))
        match_toneL = np.multiply(yL, dn_chp)
        foutL = fft(match_toneL, np.size(yL)*10)
        align_win_len = int(foutL.shape[1] / (Fs/BW))
        targL = np.exp(1j*pk_phase) * foutL[:, 0:align_win_len] + foutL[:, -align_win_len:]
        
        mindex = pk_index * 2
        
        yR = np.concatenate((sig, sig_follow))
        match_toneR = np.multiply(yR, dn_chp)
        foutR = fft(match_toneR, np.size(yR)*10)
        align_win_len = int(foutR.shape[1] / (Fs/BW))
        targR = np.exp(1j*pk_phase) * foutR[:, 0:align_win_len] + foutR[:, -align_win_len:]
        
        binw = int(np.ceil(np.size(targL) / 2**SF))
        srg = mindex + np.arange(-binw*5, binw*5 + 1)
        srg = srg[srg >= 1]
        srg = srg[srg < np.size(targL)]
        
        if np.max(abs(targL[:, srg])) > np.max(abs(targR[:, srg])):
            seg_loc = 1    # adjacent to the previous window
        else:
            seg_loc = 2    # adjacent to the latter window
        
        # Amplitude
        subl = nsamp // 8
        if(seg_loc == 1):
            tmp = np.concatenate((match_tone[0:subl], np.zeros((nsamp-subl))))
        else:
            tmp = np.concatenate((np.zeros((nsamp-subl)), match_tone[-subl:]))

        mfout = fft(tmp, nsamp*10)
        align_win_len = int(mfout.shape[0] / (Fs/BW))
        mtarg = np.exp(1j*pk_phase) * mfout[0:align_win_len] + mfout[-align_win_len:]
        binw = int(np.ceil(np.size(mtarg) / 2**SF))
        srg = pk_index + np.arange(-binw*10, binw*10 + 1)
        srg = srg[srg >= 1]
        srg = srg[srg < np.size(mtarg)]
        amp = max(abs(mtarg[srg])) / nsamp * 8
        
        # Duration
        seg_len = min(np.floor(pk_height / amp), nsamp)
        amp = pk_height / seg_len
        freq = np.arange(0, align_win_len + 1) * (BW / align_win_len)
        if seg_loc == 1:
            [dout, sym] = refine(True, seg_len, amp, freq[pk_index], sig)
        else:
            [dout, sym] = refine(False, seg_len, amp, freq[pk_index], sig)

        peak = CPeak(sym.amp*sym.length, sym.freq, SF)
        peaks.append(peak)
        org_sig = sig
        sig = dout

    return peaks

def gen_normal(code_word, down=False, Fs=main_config.RX_Sampl_Rate):
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    org_Fs = Fs
    if Fs < BW:
        Fs = BW

    nsamp = Fs * 2**SF / BW

    T = np.arange(0, int(nsamp)) * 1/Fs

    f0 = -BW/2
    f1 = BW/2

    chirpI = chirp(T, f0, 2**SF/BW, f1, 'linear', 90)
    chirpI.reshape((chirpI.size))
    chirpQ = chirp(T, f0, 2**SF/BW, f1, 'linear', 0)
    chirpQ.reshape((chirpQ.size))

    baseline = chirpI + 1j * chirpQ

    if down:
        baseline = np.conjugate(baseline)

    baseline = np.tile(baseline, 2)

    offset = round((2**SF - code_word) / 2**SF * nsamp)
    symb = baseline[offset:int(offset+nsamp)]

    if org_Fs != Fs:
        overSamp = int(Fs/org_Fs)
        symb = symb[0::overSamp]

    return symb

def refine(near_prev, seg_length, seg_ampl, peak_freq, org_sig):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    nsamp = Fs * 2**SF / BW

    min_residual = np.Inf
    dout = org_sig

    # Iteratively searching initial phase
    rphase_1 = 0
    rphase_2 = 0

    pending_phase = np.arange(0, 20)*2*np.pi/20

    for p in pending_phase:
        sig = seg_ampl * gen_phase(2**SF * (1 - peak_freq/BW), p, rphase_2)
        if near_prev:
            sig[round(seg_length):] = 0
        else:
            sig[0: -round(seg_length)] = 0

        e_residual = np.sum(np.power(np.absolute(org_sig - sig), 2))
        if e_residual < min_residual:
            rphase_1 = p
            min_residual = e_residual
            dout = org_sig - sig

    for p in pending_phase:
        sig = seg_ampl * gen_phase(2**SF * (1 - peak_freq/BW), rphase_1, p)
        if near_prev:
            sig[round(seg_length):] = 0
        else:
            sig[:-round(seg_length)] = 0

        e_residual = np.sum(np.power(np.absolute(org_sig - sig), 2))
        if e_residual < min_residual:
            rphase_2 = p
            min_residual = e_residual
            dout = org_sig - sig

    r_freq = peak_freq
    r_ampl = seg_ampl
    r_length = seg_length

    tmp = seg_ampl * (np.arange(0, int((1.1-0.9)/0.01)+1)*0.01 + 0.9)
    for i in tmp:
        sig = i * gen_phase(2**SF * (1 - r_freq/BW), rphase_1, rphase_2)
        if near_prev:
            sig[round(seg_length):] = 0
        else:
            sig[:-round(seg_length)] = 0

        e_residual = np.sum(np.absolute(org_sig - sig))
        if e_residual < min_residual:
            r_ampl = i
            min_residual = e_residual
            dout = org_sig - sig

    tmp = np.linspace(seg_length - 50, seg_length + 50, int(100/5) + 1)
    for i in tmp:
        if i < 0 or i > nsamp:
            continue
        sig = r_ampl * gen_phase(2**SF * (1 - r_freq/BW), rphase_1, rphase_2)
        if near_prev:
            sig[round(i):] = 0
        else:
            sig[:-round(i)] = 0

        e_residual = np.sum(np.absolute(org_sig - sig))
        if e_residual < min_residual:
            min_residual = e_residual
            dout = org_sig - sig
            r_length = i

    sym = CSymbol(r_freq, r_ampl, r_length, np.inf)

    return dout, sym

def gen_phase(k, phase1, phase2, is_down = False):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    nsamp = Fs * 2**SF / BW
    tsamp = np.arange(int(nsamp)) / Fs

    if is_down:
        f0 = BW/2
        f1 = -BW/2
    else:
        f0 = -BW/2
        f1 = BW/2

    chirpI = chirp(tsamp, f0, nsamp/Fs, f1, 'linear', 90)
    chirpQ = chirp(tsamp, f0, nsamp/Fs, f1, 'linear', 0)
    baseline = chirpI + 1j * chirpQ

    baseline = np.concatenate((np.multiply(baseline, np.exp(1j * phase1)),
                np.multiply(baseline, np.exp(1j * phase2))))

    offset = round((2**SF - k) / 2**SF * nsamp)
    return baseline[offset:int(offset+nsamp)]

def freq_alias(datain):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW

    nfft = datain.size
    target_nfft = round(BW/Fs*nfft)

    slice1 = datain[:target_nfft]
    slice2 = datain[-target_nfft:]
    ret_arr = np.add(np.abs(slice1), np.abs(slice2))

    return ret_arr

def group(syms, pkts, wid, num_preamble, verbose=False):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF
    nsamp = Fs * 2**SF / BW
    max_payload = main_config.Max_Payload_Num

    dout = []

    for pid in range(len(pkts)):
        pkt = pkts[pid]

        if wid > pkt.start_win + 12 + max_payload:
            continue

        c = 0
        for i in range(len(pkts)):
            if i == pid:
                continue
            if pkt.start_win < pkts(i).start_win:
                c = c+1
        if c == len(pkts) - 1:
            if wid < pkt.start_win + (num_preamble+5):
                continue
        else:
            if wid < pkt.start_win + (num_preamble+6):
                continue

        pkt_ratio = pkt.to / (nsamp - pkt.to)
        ratio_set = np.zeros(len(syms))
        
        for i in range(len(syms)):
            ratio_set[i] = syms[i].peak_ratio;

        I, val = pf.nearest(ratio_set, pkt_ratio, 1)

        if verbose:
            print(f'PKT[{round(pkt.to)}]: ', end='')
            for l in len(ratio_set):
                print(f'{round(ratio_set[l])} ', end='')
            print('\n', end='')

        if I < 0:
            sym = CSymbol(0, 1, 0, np.inf)
            sym.belong(pid)
            dout.append(sym)
        else:
            sym = syms[I]
            del syms[I]
            sym.belong(pid)
            dout.append(sym)

    return dout
    

def pair(pk, pre_set):
    # Pair a peak of the same frequency

    # LoRa modulation & sampling parameters
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF
    nsamp = Fs * 2**SF / BW
   
    idx_array = np.zeros((len(pre_set.symset)))
    for i in range(idx_array.shape[0]):
        idx_array[i] = pre_set.symset[i].fft_bin

    I, val = pf.nearest(idx_array, pk.fft_bin, 3)
    if I < 0:
        pk_ratio = np.inf
    else:
        pk_ratio = pk.height / pre_set.symset[I].height
        
    return pk_ratio
