import numpy as np
import csv
import config
from decode import lora_decoder as decoder
import openpyxl as op
from os.path import exists

def remove_beacons(symbols):
    num_beacon_sym = 15
    del_list = []
    part_beacons = np.array([[109,9,193,13,53,197,1,113,120,211,140,4,2,222,48],\
                            [109,9,253,13,57,193,1,13,100,49,37,11,52,188,185],\
                            [109, 265, 833, 45, 245, 781, 1009, 57, 158, 12, 798, 960, 401, 794, 953],\
                            [913, 9, 1021, 13, 197, 769, 13, 57, 281, 461, 1015, 558, 964, 789, 76],\
                            [2157,  757, 3261,   45, 1013, 3149, 4045,  245, 1496, 3330, 2503, 1440,  675, 3271, 2792],\
                            [913,    9, 3073,  497,  825, 3073,   49,  249, 3002, 2957, 1667, 2997, 3151, 3270, 2792]])

    for i in range(symbols.shape[0]):
        if(any(np.sum(abs(symbols[i, 0:num_beacon_sym] - part_beacons), axis=1) < 500)):
            del_list.append(i)
    symbols = np.delete(symbols, del_list, 0)
    return symbols

def calculate(symbols, results_file, algo):

    SF = config.LORA_SF
    BW = config.LORA_BW
    true_sym = np.array(config.true_sym)
    true_msg = np.array(config.true_msg)
    num_packets = config.Packets_Num

    symbols = remove_beacons(symbols)

    correctSymbols = np.sum(np.tile(true_sym, (symbols.shape[0], 1)) == symbols)
    totalSymbols = len(true_sym) * num_packets
    SER_overall = 1 - (correctSymbols/totalSymbols)

    if symbols.shape[0] < num_packets:
        PDR = symbols.shape[0]/num_packets
    else:
        PDR = 1

    detectedSymbols = PDR * totalSymbols
    SER_detected = 1 - (correctSymbols/detectedSymbols)

    symbols = np.mod(symbols-1, 2**SF) # LoRa decoder expects symbols in [0,2**SF-1] range

    incorrectBits = 0
    correctPackets = 0
    for i in range(symbols.shape[0]):
        message = decoder(symbols[i], SF)
        if message is not None:
            message = message.astype(int)
            if message.size < true_msg.size:
                continue
            else:
                decoded_msg = message[0:true_msg.size]
                if np.array_equal(decoded_msg, true_msg):
                    correctPackets += 1
                else:
                    for byte_num in range(true_msg.size):
                        XOR = decoded_msg[byte_num] ^ true_msg[byte_num]
                        while (XOR):
                            XOR = XOR & (XOR - 1)
                            incorrectBits += 1
            # if message.size != true_msg.size:
            #     continue
            # else:
            #     correctBits += np.sum(true_msg == message)
            #     if np.sum(true_msg != message) == 0:
            #         correctPackets += 1
        else:
            continue

    PRR_overall = correctPackets / num_packets
    PRR_detected = correctPackets / (num_packets * PDR)

    totalBits = true_msg.size * num_packets * 8
    BER_detected = incorrectBits / (totalBits * PDR)
    incorrectBits += int((1 - PDR) * totalBits)
    BER_overall = incorrectBits / totalBits


    T = config.Packet_Time
    Tput = (correctPackets * len(true_msg) * 8) / T

    print(f'SER_overall = {SER_overall}; SER_detected = {SER_detected}; PDR = {PDR}; PRR_overall = {PRR_overall}; \
    PRR_detected = {PRR_detected}; BER_overall = {BER_overall}; BER_detected = {BER_detected}; Tput = {Tput} bits/s')

    # Save result in file
    if exists(results_file):
        wb = op.load_workbook(results_file)
        ws = wb.worksheets[0]
    else:
        wb = op.Workbook()
        ws = wb.worksheets[0]
        head = ['Name', 'SER_overall', 'SER_detected', 'PDR', 'PRR_overall', 'PRR_detected', 'BER_overall', 'BER_detected', 'Tput']
        ws.append(head)
    var = [f'SF{SF}_{BW}_{algo}', SER_overall, SER_detected, PDR, PRR_overall, PRR_detected, BER_overall, BER_detected, Tput]
    # Select First Worksheet
    ws.append(var)
    wb.save(results_file)

