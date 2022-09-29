import numpy as np

def ftrack_2_symbol(track_user_pairs, preambles, num_symb, fft_factor):

    sz = track_user_pairs.shape
    num = sz[0]
    
    payloads = np.zeros((num, 3), int)
    
    for tu in range(num):
        tu_pair = track_user_pairs[tu,]
        freq_bin = tu_pair[0]
        user_id = tu_pair[1]
        chirp_id = tu_pair[3]
        
        if (user_id <= 0):
            continue
        
        freq_0 = preambles[user_id-1, 0]
        
        # demodulating alogrithm
        freq_bin = np.floor(freq_bin/fft_factor)
        freq_0 = np.floor(freq_0/fft_factor)
        freq_diff = (num_symb + freq_bin - freq_0) % (num_symb)
        symbol = (freq_diff + 0.25*num_symb) % (num_symb)
        payloads[tu,] = [user_id, symbol, chirp_id]
    
    # transform to standard format
    symbols = symbol_format(payloads)
    return symbols

def symbol_format(payloads):

    sz = payloads.shape
    payld_num = sz[0]
    
    user_num = np.max(payloads[:, 0])
    chirp_num = np.max(payloads[:, 2])
    
    symbol_user_tbl = -1*np.ones((chirp_num, user_num))
    for p in range(payld_num):
        sym_data = payloads[p,]
        
        u_id = sym_data[0]
        symb = sym_data[1]
        chp_id = sym_data[2]
        
        if (u_id <= 0 or chp_id <= 0):
            continue
            
        symbol_user_tbl[chp_id-1, u_id-1] = symb
    
    symbs_f = np.zeros((chirp_num*user_num, 2), int)
    for u in range(user_num):
        u_st = (u)*chirp_num
        u_ed = (u+1)*chirp_num
        
        symbs_f[u_st:u_ed,] = np.concatenate(((u+1)*np.ones((chirp_num, 1)), symbol_user_tbl[:, u][np.newaxis].transpose()), axis = 1)
        
    return symbs_f
