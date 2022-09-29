#!/usr/bin/env/ python3

import sys
#import argparse
import FTrack.config as config
import config as main_config
import math
#import multiprocessing
import numpy as np
import os
import time
from FTrack.moving_offset_fft import moving_offset_fft
from FTrack.ftrack_fftpwr_preprocess import ftrack_fftpwr_preprocess
from FTrack.ftrack_detect import ftrack_detect
from FTrack.ftrack_preamble_detect_v2 import ftrack_preamble_detect_v2
from FTrack.frame_identify_v2 import frame_identify_v2
from FTrack.frame_payload_edges import frame_payload_edges
from FTrack.ftrack_grouping_v2 import ftrack_grouping_v2
from FTrack.ftrack_multi_grouping import ftrack_multi_grouping
from FTrack.frame_track_user_pairs import frame_track_user_pairs
from FTrack.ftrack_2_symbol import ftrack_2_symbol
from FTrack.pkt_split import pkt_split

def main(raw_data, Fs, BW, SF, payload_num):#, pkts):
    # LoRa modulation & sampling parameters
    global_start = time.time()
    upsampling_factor = int(Fs/BW)
    num_symb = 2**SF    # chirp length, i.e., number of symbols a chirp can carry

    # LoRa frame structure parameters for generating border template
    PREAMBLE = config.FRM_PREAMBLE + config.FRM_SYNC     # preamble and two sync words
    #PAYLOAD = config.FRM_PAYLOAD
    PAYLOAD = payload_num


    if SF == 12:
        num_preamble = 7
    else:
        num_preamble = 8
    num_sync = 2
    num_DC = 2.25
    num_data_sym = main_config.Max_Payload_Num
    pkt_len = num_preamble + num_sync + num_DC + num_data_sym
    num_samples = pkt_len * num_symb

    # Parameters for signal display
    ST_LORA = int(0)                # start pos of LoRa signal samples
    ED_LORA = int(raw_data.size)                # end pos of LoRa signal samples
    SPECTRO_LEN = ED_LORA  # max length of LoRa spectrum

    if raw_data.ndim == 1:
        x_1 = raw_data[:, np.newaxis]

    RSSI_threshold = 1e-3
    pkts = x_1 > RSSI_threshold
    pnts = pkts[:, 0].nonzero()
    pnts = np.array(pnts).transpose()
    pkt_bndrs = []
    for i in range(len(pnts)-1):
        if(pnts[i+1] - pnts[i] > 2e3):
            pkt_bndrs = np.concatenate((pkt_bndrs, pnts[i] + (num_symb*50), pnts[i+1] - (num_symb*50)))

    pkt_bndrs = np.concatenate((max(pnts[0] - (num_symb*10), np.array([0])), pkt_bndrs, min(pnts[-1] + (num_symb*10), np.array([x_1.shape[0] - 1]))))
    pkts = pkt_bndrs.reshape(-1, 2)
    syms = []

    #pkts = pkt_split(pkts, 10*num_samples*upsampling_factor, 2.5*upsampling_factor*num_symb)

    for p in range(pkts.shape[0]):
        # locating signal samples of a LoRa frame
        seg_st = int(pkts[p, 0])
        #seg_st = int(pkts[p]) - int(10*num_symb)
        seg_ed = int(pkts[p, 1])
        #seg_ed = int(pkts[p]) + int((pkt_len + 1) * num_symb)
        # choosing a segment of lora frame
        seg_id = 0
        seg_len = seg_ed - seg_st
        sig_st = seg_st + seg_len*seg_id
        sig_ed = sig_st + seg_len - 1
        if (sig_ed > seg_ed):
            sig_ed = seg_ed

        # identify target samples
        target_signal = x_1[sig_st:sig_ed]
        #collided_signals = target_signal
        collided_signals = target_signal#[0:][::upsampling_factor]

        # processing section
        # main logic for parallel decoding

        # moving offset for border detection
        fft_factor = config.TRK_FFT_factor
        nfft = num_symb*fft_factor
        mvfft_pwr = moving_offset_fft(collided_signals, num_symb, nfft)

        # automatic threshold detect
        [fpwr, local_thresholds] = ftrack_fftpwr_preprocess(mvfft_pwr)

        # ftrack detecting
        pwr_threshold = config.TRK_PWR_THRESHOLD
        trklen_threshold = config.TRK_LEN_THRESHOLD
        ftrack_pwr = mvfft_pwr
        # detect freq. tracks
        ftracks = ftrack_detect(fpwr, 0, trklen_threshold)
        # sort ftracks in time domain
        #ftracks_tm = sortrows(ftracks, [2 3 1]);
        ftracks_tm = ftracks[ftracks[:,1].argsort(),]

        sz = ftracks_tm.shape
        trk_num = sz[0]
        # track-->user map, 0: not being processed, >0: user id, <0: duplicated
        # track of a user
        trk_user_map = np.zeros((trk_num, 1), int)

        # detect preambles and chirp borders from long freq. tracks
        preamb_chirp_num = config.TRK_PREAMBLE_MIN
        [preambles, preamb_idx] = ftrack_preamble_detect_v2(ftracks_tm, num_symb, preamb_chirp_num)

        # filter out false preambles & search for symbol edges on real preambles
        [preambs_sync, sync_words, trk_user_map] = frame_identify_v2(preambles, preamb_idx, trk_user_map, collided_signals, ftrack_pwr, ftracks_tm, num_symb, nfft, local_thresholds)

        # Number of valid frames
        sz = preambs_sync.shape
        frame_num = sz[0]

        if (frame_num <= 0):
            #print('no valid frame been detected!')
            continue

        if ((ftracks_tm[preamb_idx[-1,0],1]*upsampling_factor + ((num_DC + num_data_sym)*num_symb*upsampling_factor)) > len(target_signal)):
            #  if a data portion of a packet is split then account for the length difference
            ex_samp = int((ftracks_tm[preamb_idx[-1,0],1]*upsampling_factor + ((num_DC + num_data_sym)*num_symb*upsampling_factor)) - len(target_signal))
            target_signal = x_1[seg_st : sig_ed + ex_samp]
            target_signal = target_signal[0:int(np.floor(target_signal.shape[0]/upsampling_factor)*upsampling_factor)]
            collided_signals = target_signal[1:][::upsampling_factor]

        # edges of payload symbols in the frames
        [header_edges, payload_edges] = frame_payload_edges(preambs_sync, sync_words, PAYLOAD, num_symb)

        # payload edge demodulating indication map
        edge_trk_map = np.zeros((PAYLOAD, frame_num), int)
        [trk_user_map, edge_trk_map] = ftrack_grouping_v2(ftracks_tm, payload_edges, trk_user_map, edge_trk_map, num_symb, ftrack_pwr)

        [trk_user_map, edge_trk_map] = ftrack_multi_grouping(ftracks_tm, payload_edges, trk_user_map, edge_trk_map, num_symb, ftrack_pwr)

        track_user_pairs = frame_track_user_pairs(ftracks_tm, payload_edges, edge_trk_map)

        # symbol demodulate
        payloads = ftrack_2_symbol(track_user_pairs, preambs_sync, num_symb, fft_factor)

        num_packets = np.unique(payloads[:, 0])
        for i in num_packets:
            if syms == []:
                syms = payloads[payloads[:, 0] == i, 1]
                if len(syms) < payload_num:
                    syms = np.concatenate((syms, np.array([-1]).repeat(payload_num-len(syms))))
                #print(f'Packet {i}: {payloads[payloads[:, 0] == i, 1]}')
            else:
                new_syms = payloads[payloads[:, 0] == i, 1]
                if len(new_syms) < payload_num:
                    new_syms = np.concatenate((new_syms, np.array([-1]).repeat(payload_num-len(new_syms))))
                syms = np.vstack((syms, new_syms))

    global_end = time.time()
    print(f'Demodulator: FTrack; Time taken = {global_end - global_start} seconds')
    return syms

if __name__ == '__main__':
    main()
