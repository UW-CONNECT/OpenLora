#!/usr/bin/env python3

import NScale.config as config
import config as main_config
import numpy as np
import NScale.peak_funcs as pf

from NScale.classes import CSymbol, CPacket
from scipy.signal import chirp
from scipy.fft import fft

def detect(sig):
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    nsamp = Fs * 2**SF / BW
    MAX_PK_NUM = config.Max_Peak_Num

    symbols = []
    threshold = 0

    for i in range(0,MAX_PK_NUM):
        # dechirping and fft
        dn_chp = gen_normal(0, True)
        dn_chp = dn_chp.reshape((dn_chp.size))
        match_tone = np.multiply(sig, dn_chp)
        station_fout = fft(match_tone, int(nsamp*10))

        # applying non-stationary scaling down-chirp
        amp_lb = 1
        amp_ub = 1.2

        scal_func = np.linspace(amp_lb, amp_ub, int(nsamp))
        match_tone = np.multiply(sig, np.multiply(scal_func, dn_chp))
        non_station_fout = fft(match_tone, int(nsamp*10))
        non_station_fout = non_station_fout.reshape((non_station_fout.size))

        # peak information
        pk_height = -1
        pk_index = 0
        pk_phase = 0

        # Iterative compensate phase rotation
        align_win_len = station_fout.size / (Fs/BW)

        pending_phase = np.arange(0, 20)*2*np.pi/20

        for p in pending_phase:
            non_scal_targ = np.exp(1j * p) * station_fout[0:int(align_win_len)] +\
            station_fout[-int(align_win_len):]

            if np.max(np.absolute(non_scal_targ)) > pk_height:
                pk_index = np.argmax(np.absolute(non_scal_targ))
                pk_height = np.absolute(non_scal_targ)[pk_index]
                pk_phase = p

        # Threshold for peak detecting
        if i == 0:
            threshold = pk_height / 20
        else:
            if pk_height < threshold:
                break

        # Determin if peak is legitimate or duplicated
        repeat = False
        # Add 1 to pk_index because matlab is 1-indexed but python
        # is 0-indexed
        cbin = (1 - (pk_index+1)/align_win_len) * 2**SF
        rsym = 0

        for s in symbols:
            if np.absolute(s.fft_bin - cbin) < 2:
                rsym = s.fft_bin
                repeat = True
                break

        if repeat:
            break

        # Scaling factor of peaks: alpha
        non_scal_targ = np.exp(1j * pk_phase) * non_station_fout[0:int(align_win_len)] +\
        non_station_fout[-int(align_win_len):]

        alpha = np.absolute(non_scal_targ[pk_index]) / pk_height

        # Abnormal alpha
        if alpha < amp_lb or alpha > amp_ub:
            return

        freq = np.arange(0, align_win_len) * (BW / align_win_len)
        if alpha < (amp_lb + amp_ub) / 2:
            seg_len = (alpha - amp_lb) * 2 / (amp_ub - amp_lb) * nsamp
            amp = pk_height / seg_len
            dout, sym = refine(True, seg_len, amp, freq[pk_index], sig)
        else:
            seg_len = (amp_ub - alpha) * 2 / (amp_ub - amp_lb) * nsamp
            amp = pk_height / seg_len
            dout, sym = refine(False, seg_len, amp, freq[pk_index], sig)

        symbols.append(sym)
        sig = dout

    return symbols

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

    sym = CSymbol(near_prev, r_freq, r_ampl, r_length)

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

    for pid in range(0, len(pkts)):
        pkt = pkts[pid]

        if wid > pkt.start_win + (num_preamble+4) + max_payload:
            continue

        c = 0
        for i in range(len(pkts)):
            if i == pid:
                continue
            if pkt.start_win < pkts(i).start_win:
                c = c+1
        if c == len(pkts) - 1:
            if wid < pkt.start_win + (num_preamble+4):
                continue
        else:
            if wid < pkt.start_win + (num_preamble+4):
                continue

        lenset = np.zeros(len(syms))
        for i in range(0, len(syms)):
            if syms[i].ahead:
                if syms[i].length >= nsamp / 2:
                    lenset[i] = syms[i].length
            else:
                if syms[i].length >= nsamp / 2:
                    lenset[i] = nsamp - syms[i].length

        I, val = pf.nearest(lenset, pkt.to, np.inf)

        if verbose:
            print(f'PKT[{round(pkt.to)}]: ', end='')
            for l in lenset:
                print(f'{round(l)} ', end='')
            print('\n', end='')

        if I < 0:
            sym = CSymbol(True, 0, 1, 0)
            sym.belong(pid)
            dout.append(sym)
        else:
            sym = syms[I]
            del syms[I]
            sym.belong(pid)
            dout.append(sym)

    return dout
