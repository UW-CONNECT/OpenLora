import numpy as np
from std_lora.sym_to_data_ang import sym_to_data_ang

def lora_demod(Rx_Buffer,N,upsampling_factor,num_preamble,num_sync,num_DC,num_data_sym,Preamble_ind,whole_file):

    ser = np.array([])
    demod_sym = np.array([], int, ndmin = 2)
    UC = sym_to_data_ang([1],N)
    DC = UC.conj()
    DC_fft = np.fft.fft(DC, axis = 0)
    DC_sig = np.concatenate([DC_fft[0:N//2], np.zeros(((upsampling_factor-1)*N, 1)), DC_fft[N//2 :N]])
    DC_upsamp = np.fft.ifft(DC_sig, axis = 0)
    
    Data_frame_st = Preamble_ind + int((num_preamble+num_sync+num_DC)*N*upsampling_factor)
    
    for j in range(Preamble_ind.shape[0]):
        #demod = np.array([], int)
        demod = np.empty((1, num_data_sym), int)
        for i in range(num_data_sym):
            if(Data_frame_st[j] + (i+1)*upsampling_factor*N - 1 > Rx_Buffer.size):
                demod[:, i] = -1
                continue
            
            temp_fft = abs(np.fft.fft(Rx_Buffer[(Data_frame_st[j] + (i)*upsampling_factor*N): (Data_frame_st[j] + (i+1)*upsampling_factor*N)] * DC_upsamp, axis = 0))
            temp_fft = temp_fft[np.concatenate([np.arange(0,N//2), np.arange(N//2 + (upsampling_factor-1)*N, upsampling_factor*N)])]
            
            b = temp_fft.argmax()
            #demod = np.append(demod, b)
            demod[:, i] = b
            
        #demod_sym = np.append(demod_sym, demod, axis = 0)
        if(j == 0):
           demod_sym = demod
        else:
            demod_sym = np.vstack((demod_sym, demod))
    
    #if(whole_file):
        #demod_sym = (demod_sym[4:,] - 2) % N
    #else:
    demod_sym = (demod_sym) % N
    
    #sym = kron(np.ones(demod_sym.shape[0],1), sym)
    
    return demod_sym

