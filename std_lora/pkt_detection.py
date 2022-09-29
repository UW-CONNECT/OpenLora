import numpy as np
from std_lora.sym_to_data_ang import sym_to_data_ang

def pkt_detection(Rx_Buffer,N,upsampling_factor,num_preamble):

    UC = sym_to_data_ang([1],N)
    DC = UC.conj()
    DC_fft = np.fft.fft(DC, axis = 0)
    DC_sig = np.concatenate([DC_fft[0:N//2], np.zeros(((upsampling_factor-1)*N, 1)), DC_fft[N//2 :N]])
    DC_upsamp = np.fft.ifft(DC_sig, axis = 0)
    
    # Preamble Detection
    temp_wind_fft = np.array([])
    ind_buff = np.array([])
    count = 0
    Pream_ind = np.array([], int)
    
    loop = Rx_Buffer.size//(upsampling_factor*N)
    
    for i in range(loop):
        temp_wind_fft = abs(np.fft.fft(Rx_Buffer[(i*upsampling_factor*N) : ((i+1)*upsampling_factor*N)] * DC_upsamp, axis = 0))
        temp_wind_fft_idx = np.concatenate([np.arange(0, N//2), np.arange(N//2 + (upsampling_factor-1)*N, (upsampling_factor)*N)])
        temp_wind_fft = temp_wind_fft[temp_wind_fft_idx]
        b = np.argmax(temp_wind_fft)
        if(len(ind_buff) >= num_preamble):
            ind_buff = ind_buff[-(num_preamble-1):]
            ind_buff = np.append(ind_buff, b)
        else:
            ind_buff = np.append(ind_buff, b)

        if(sum(abs(np.diff(ind_buff))) <= (num_preamble + 2) and ind_buff.size >= num_preamble):
            #print('found a preamble')
            count = count + 1
            Pream_ind = np.append(Pream_ind, (i - (num_preamble-1))*(upsampling_factor*N))
    
    #print('Found ', count, ' Preambles')
    
    # Fine Synchronization
    temp_wind_fft = np.array([])
    amp_arr = np.array([])
    ind_arr = np.array([])
    
    #shift2 = np.arange(-2*upsampling_factor, 2*upsampling_factor + 1, dtype = int)
    shifts = np.arange(upsampling_factor * -N/2, upsampling_factor * N/2, dtype = int)
    
    for i in range(Pream_ind.shape[0]):
        ind_arr = np.array([])
        amp_arr = np.array([])
        temp_ind = np.array([])
        temp_shift = np.array([])
        temp_amp = np.array([])
    
        for j in shifts:
            if(Pream_ind[i] + j < 0):
                amp_arr = np.append(amp_arr, -1)
                ind_arr = np.append(ind_arr, -1)
                continue

            temp_wind_fft = abs(np.fft.fft(Rx_Buffer[(Pream_ind[i] + j) : (Pream_ind[i] + j + upsampling_factor*N)] * DC_upsamp, upsampling_factor*N, axis = 0))
            temp_wind_fft = temp_wind_fft[np.concatenate([np.arange(0,N//2), np.arange(N//2 + (upsampling_factor-1)*N, upsampling_factor*N)])]
            a = max(temp_wind_fft)
            b = temp_wind_fft.argmax()
            amp_arr = np.append(amp_arr, a)
            ind_arr = np.append(ind_arr, b)

        nz_arr = (ind_arr == 0)
        nz_arr = nz_arr.nonzero()
        if(len(nz_arr[0]) != 0):
            temp_ind = nz_arr
            temp_shift = shifts[temp_ind]
            temp_amp = amp_arr[temp_ind]
            c = temp_amp.argmax()
            Pream_ind[i] = Pream_ind[i] + temp_shift[c]
    
    # SYNC WORD DETECTION
    temp_wind_fft = np.array([])
    count = 0
    Preamble_ind = np.array([], int)
    for i in range(Pream_ind.shape[0]):
        if((Pream_ind[i] + 9*(upsampling_factor*N) - 1 > Rx_Buffer.size) or (Pream_ind[i] + 10*(upsampling_factor*N) - 1 > Rx_Buffer.size)):
            continue

        x_1 = Rx_Buffer[(Pream_ind[i] + num_preamble*upsampling_factor*N) : (Pream_ind[i] + (num_preamble+1)*upsampling_factor*N)]
        x_2 = Rx_Buffer[(Pream_ind[i] + (num_preamble+1)*upsampling_factor*N): (Pream_ind[i] + (num_preamble+2)*upsampling_factor*N)]
        sync_wind1 = abs(np.fft.fft(x_1 * DC_upsamp, axis = 0))
        sync_wind2 = abs(np.fft.fft(x_2 * DC_upsamp, axis = 0))
        sync_wind1 = sync_wind1[np.concatenate([np.arange(0,N//2), np.arange(N//2 + (upsampling_factor-1)*N, upsampling_factor*N)])]
        sync_wind2 = sync_wind2[np.concatenate([np.arange(0,N//2), np.arange(N//2 + (upsampling_factor-1)*N, upsampling_factor*N)])]
    
        s1 = sync_wind1.argmax()
        s2 = sync_wind2.argmax()
        if(s1 == 8 and s2 == 16):
            #print('Confirmed Packet')
            count = count + 1
            Preamble_ind = np.append(Preamble_ind, Pream_ind[i])
    
    # count
    #print('Matched ', count, ' SYNC Words')
    
    return Preamble_ind
    
