#!/usr/bin/env python3

import config as main_config

class CPacket:
    def __init__(self, window, offset_f, offset_t, fft_bin=0):
        self.start_win = window
        self.cfo = offset_f
        self.to = offset_t
        self.fft_bin = fft_bin

    def show(self):
        print(f'\t[packet] start from window{self.start_win}, '
              f'cfo = {self.cfo:.2f}, to = {self.to:.2f}')

class CPeak:
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF
    
    def __init__(self, height, freq, sf):
        self.height = height
        self.freq = freq
        self.fft_bin = round((CPeak.BW - freq)/CPeak.BW * 2**CPeak.SF)

    def __eq__(self, other):
        if isinstance(other, CPeak):
            return abs(self.fft_bin - other.fft_bin) < 2

        return False

    def show(self):
        print(f'\t[peak] frequency = {self.freq:.2f}, '
              f'height = {self.height:.2f}, value = {self.fft_bin:.2f}')

class CSymbol:
    Fs = main_config.RX_Sampl_Rate
    BW = main_config.LORA_BW
    SF = main_config.LORA_SF

    nsamp = Fs * 2**SF / BW

    def __init__(self, freq, amp, length, peak_ratio):
        self.peak_ratio = peak_ratio
        self.freq = freq
        self.fft_bin = (CSymbol.BW - freq)/CSymbol.BW * 2**CSymbol.SF
        self.length = length
        self.amp = amp
        self.chirp_n = CSymbol.nsamp # But why tho
        self.pkt_id = 0

    def __eq__(self, other):
        if isinstance(other, CSymbol):
            return abs(self.bin - other.bin) < 2

        return False

    def show(self):
        print(f'\t[peak] frequency = {self.freq:.2f}, '
              f'value = {self.fft_bin:.1f}, symbol amplitude = {self.amp:.2f},'
              f' length = {round(self.length)}, ratio = {self.peak_ratio}, '
              f'belong = {self.pkt_id}\n')

    def write_file(self, filename, wid, belong, value):
        with open(filename, 'a') as f:
            s = f'\n{wid},{self.fft_bin:.1f},{self.peak_ratio},{self.amp*100:.2f},{belong},{value}'
            f.write(s)

    def belong(self, pkt_id):
        self.pkt_id = pkt_id

class CWin:
    def __init__(self, ident=0):
        self.ident = ident
        self.symset = []

    def addPeak(self, sym):
        self.symset.append(sym)

    def rmSymbol(self, sym):
        try:
            self.symset.remove(sym)
            return True
        except ValueError:
            return False

    def show(self):
        print(f'Symbol Set {self.ident} ({len(self.symset)} items):')
        for sym in self.symset:
            sym.show()
