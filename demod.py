from NScale.main import main as nscale
from CoLoRa.main import main as colora
from FTrack.main import main as ftrack
from std_lora.main import main as std_lora
from CIC.main import main as cic
import math
import numpy as np
from scipy.signal import chirp

def ind_vals(arr, thresh, num_pts):
    out = []
    for i in range(num_pts):
        idx = np.argmax(arr)
        if arr[idx] < thresh:
            return out
        else:
            out.append(idx)
            arr[idx] = 0
    return out

def gen_normal(code_word, SF, BW, Fs, down=False):
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

# Find start of preambles with correlation
def UC_location_corr(Data, SF, BW, Fs, called_i, samp, overlap):
    N = 2**SF
    upsamp_factor = Fs//BW
    if SF == 12:
        num_preamble = 7
    else:
        num_preamble = 8
    upchirp_ind = []
    tmp_window = []
    DC = gen_normal(0, SF, BW, Fs, True)
    DC = DC.reshape((DC.size))
    DC = DC[::int(upsamp_factor)]
    DC_sum = sum(DC[0:N] * np.conj(DC[0:N]))
    for i in range(len(Data) - len(DC)):
        tmp_window.append(sum(Data[i:i+N] * DC[0:N]) /
            np.sqrt(sum(Data[i:i+N] * np.conj(Data[i:i+N])) *
            DC_sum))

    n_samp_array = []
    peak_ind_prev = []
    for i in range(math.floor(len(tmp_window)/N)):
        window = np.abs(tmp_window[i*N : (i+1)*N])
        peak_ind_curr = ind_vals(window, 0.2, 16)

        if len(peak_ind_prev) != 0 and len(peak_ind_curr) != 0:
            for j in range(len(peak_ind_curr)):
                for k in range(len(peak_ind_prev)):
                    if peak_ind_curr[j] == peak_ind_prev[k]:
                        n_samp_array.append(peak_ind_prev[k] + (i-1)*N)
        peak_ind_prev = peak_ind_curr

    for i in range(len(n_samp_array)):
        c = 0
        ind_arr = np.arange(0, (num_preamble-2)*N, N) + (n_samp_array[i] + N)

        for j in range(len(ind_arr)):
            c = c + np.sum(n_samp_array[:] == ind_arr[j])

        if c >= 6:
            upchirp_ind.append(n_samp_array[i])

    temp = []
    if len(upchirp_ind) != 0:
        temp.append(upchirp_ind[0])
        for i in range(1, len(upchirp_ind)):
            if (np.min(np.abs(upchirp_ind[i] - temp[:])) > 5):
                temp.append(upchirp_ind[i])
    if len(temp) != 0:
        return [int(idx * upsamp_factor + max(called_i*samp-overlap, 0)) for idx in temp]
    return temp
