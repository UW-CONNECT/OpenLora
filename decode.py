import numpy as np
import math as mt

# selectbits concat zeros (from 4-bit to 8-bit)
#
#   in:  data            symbol sequence
#        indices         vector = [1 2 3 4 5]
#
#  out:  r               symbols 
def selectbits(data,indices):
    r = 0 
    for ctr in range(len(indices)):
        if((int(data) & int(1<<indices[ctr])) > 0):
            r = r + (1<<ctr) # shift to left
        else:
            r = r + 0 
    #end for loop
    return r

# rotl 
#
#   in:  bits            bit sequence
#        counts          
#        size
#
#  out:  y               rotated symbols
def rotl(bits,count,size):
    len_mask = (1<<size) - 1 
    count = count%size 

    bits = int(bits) & int(len_mask) 

    #again could have similar issues as above, depends on size of count and size
    y = ( ( (bits<<count) & len_mask) | mt.floor((bits>> (size - count)))) 
    return y
############################################

# LoRa_decode_shuffle swap payload packet
#
#   in:  symbols       symbol vector           
#
#  out:  symbols_swp   unswapped symbols
def LoRa_decode_swap(symbols):

    symbols_swp = np.zeros((1,len(symbols))) 
    symbols_swp = symbols_swp[0]
    
    for ctr in range(len(symbols)):
        symbols_swp[ctr] = (((int(symbols[ctr]) & 15 )<<4) | ((int(symbols[ctr])&240)>>4))  # swap first half of 8-bit sequencne with other half 
    #end for loop

    return symbols_swp 
############################################



# LoRa_decode_white dewhitening of payload packet
#
#   in:  symbols       whitened symbols
#        CR            code rate
#        DE            data rate optimization flag
#
#  out:  symbols_white  dewhitened symbols
def LoRa_decode_white(symbols,CR,DE):

    if(DE == 0):
        if((CR > 2) and (CR <= 4)):
            white_sequence = [255,255,45,255,120,255,225,255,0,255,210,45,85, \
            120,75,225,102,0,30,210,255,85,45,75,120,102,225,30,210,255, \
            135,45,204,120,170,225,180,210,153,135,225,204,0,170,0,180,0, \
            153,0,225,210,0,85,0,153,0,225,0,210,210,135,85,30,153,45,225, \
            120,210,225,135,210,30,85,45,153,120,51,225,85,210,75,85,102, \
            153,30,51,45,85,120,75,225,102,0,30,0,45,0,120,210,225,135,0, \
            204,0,120,0,51,210,85,135,153,204,51,120,85,51,153,85,51,153, \
            135,51,204,85,170,153,102,51,30,135,45,204,120,170,51,102,85, \
            30,153,45,225,120,0,51,0,85,210,153,85,225,75,0,180,0,75,210, \
            102,85,204,75,170,180,102,75,204,102,170,204,180,170,75,102, \
            102,204,204,170,120,180,51,75,85,102,75,204,102,120,204,51, \
            120,85,225,75,0,102,210,204,135,120,30,225,255,0,255,210,45, \
            135,170,30,102,255,204,255,170,45,102,170,30,102,255,204,45, \
            170,170,102,180,30,75,255,102,45,30,170,45,180,170,75,180,102, \
            153,30,225,45,210,170,85,180,153,153,225,225,0,210,210,85,135, \
            153,204,225,170,0,102,210,204,135,120,204,225,170,210,102,135, \
            204,30,120,255,225,45,210,120,135,51,30,135,255,30,45,45,120, \
            120,51,51,135,135,30,204,45,120,120,225,51,210,135,85,204,75, \
            120,102,225,204,210,170,85,180,75,153,102,51,204,85,170,153, \
            180,225,153,210,51,85,85,75,153,180,225,153,210,51,85,85,75, \
            75,180,180,153,75,51,180,85,153,75,51,180,135,75,30,180,45, \
            153,170,51,102,199,30,30,45,45,170,170,102,102,204,30,120, \
            45,51,170,135,102,30,204,255,120,45,51,170,135,102,30,30,255, \
            255,45,255,170,255,102,45,30,170,255,180,255,153,255,51,45,135, \
            170,204,180,120,153,51,51,135,135,204,204,170,120,180,51,75,135, \
            180,204,153,170,225,180,210,75,135,180,204,153,120,225,225,210,0, \
            135,0,204,210,120,135,225,30,0,45,0,170,210,180,135,75,30,180, \
            45,75,170,180,180,75,75,102,180,30,75,255,180,255,75,45,102,120, \
            30,51,255,85,255,75,45,180,120,153,51,225,85,0,75,210,180,85,153, \
            153,225,51,0,135,210,30,85,255,153,255,51,255,135,255,30,0,0,0,0, \
            135,225,170,204] 
        elif((CR > 0) and (CR <= 2)):
                white_sequence = [255,255,45,255,120,255,48,46,0,46,18,60,20,40,10, \
            48,54,0,30,18,46,20,60,10,40,54,48,30,18,46,6,60,12,40,58,48,36, \
            18,24,6,48,12,0,58,0,36,0,24,0,48,18,0,20,0,24,0,48,0,18,18,6,20, \
            30,24,60,48,40,18,48,6,18,30,20,60,24,40,34,48,20,18,10,20,54,24, \
            30,34,60,20,40,10,48,54,0,30,0,60,0,40,18,48,6,0,12,0,40,0,34,18, \
            20,6,24,12,34,40,20,34,24,20,34,24,6,34,12,20,58,24,54,34,30,6,60, \
            12,40,58,34,54,20,30,24,60,48,40,0,34,0,20,18,24,20,48,10,0,36,0, \
            10,18,54,20,12,10,58,36,54,10,12,54,58,12,36,58,10,54,54,12,12,58, \
            40,36,34,10,20,54,10,12,54,40,12,34,40,20,48,10,0,54,18,12,6,40,30, \
            48,46,0,46,18,60,6,58,30,54,46,12,46,58,60,54,58,30,54,46,12,60,58, \
            58,54,36,30,10,46,54,60,30,58,60,36,58,10,36,54,24,30,48,60,18,58, \
            20,36,24,24,48,48,0,18,18,20,6,24,12,48,58,0,54,18,12,6,40,12,48, \
            58,18,54,6,12,30,40,46,48,60,18,40,6,34,30,6,46,30,60,60,40,40,34, \
            34,6,6,30,12,60,40,40,48,34,18,6,20,12,10,40,54,48,12,18,58,20,36, \
            10,24,54,34,12,20,58,24,36,48,24,18,34,20,20,10,24,36,48,24,18,34, \
            20,20,10,10,36,36,24,10,34,36,20,24,10,34,36,6,10,30,36,60,24,58, \
            34,54,6,30,30,60,60,58,58,54,54,12,30,40,60,34,58,6,54,30,12,46, \
            40,60,34,58,6,54,30,30,46,46,60,46,58,46,54,60,30,58,46,36,46,24, \
            46,34,60,6,58,12,36,40,24,34,34,6,6,12,12,58,40,36,34,10,6,36,12, \
            24,58,48,36,18,10,6,36,12,24,40,48,48,18,0,6,0,12,18,40,6,48,30,0, \
            60,0,58,18,36,6,10,30,36,60,10,58,36,36,10,10,54,36,30,10,46,36,46, \
            10,60,54,40,30,34,46,20,46,10,60,36,40,24,34,48,20,0,10,18,36,20,24, \
            24,48,34,0,6,18,30,20,46,24,46,34,46,6,46,30,0,0,0,0,36,6] 
    

    N = min([len(symbols), len(white_sequence)])  # LoRa symbol length
    symbols_white = np.bitwise_xor(np.uint64(symbols[0:N]),np.uint64(white_sequence[0:N])) 
    return symbols_white

##############################################################################

# LoRa_decode_gray degray LoRa payload
#
#   in:  symbols       symbols with graying
#
#  out:  symbols_gray  degrayed symbols
# works with hellow world exmaple now
def LoRa_decode_gray(symbols): 
    symbols_gray = np.bitwise_xor(np.uint64(symbols),np.uint64(np.floor(np.right_shift(np.uint64(symbols),np.uint64(1)))))
    return symbols_gray 
##############################################################################

# LoRa_decode_interleave deinterleaves payload packet
#
#   in:  symbols       interleaved symbols
#        ppm
#        rdd
#
#  out:  symbols_interleaved  deinterleaved symbols
# might have to deal with stupid matlab indexing to 1
def LoRa_decode_interleave(symbols, ppm, rdd): 

    #have to do weird apending stuff with symbols_interleaved 
    symbols_interleaved = [] 
    sym_idx_ext = 0 

    for block_idx in range(int(np.floor(len(symbols)/(4+rdd)))):
        
        sym_int = np.zeros((1,ppm)) 
        sym_int = sym_int[0]
        
        for sym_idx in range(4 + rdd):
            
            #rotl passed basic matlab testing
            sym_rot = rotl(symbols[sym_idx_ext],sym_idx,ppm) 
            mask = (1<<ppm-1) 
            
            #minus 1 because of matlab index by 1 problem
            ctr = ppm - 1

            while mask > 0:
                #annoying issues where I'll probs have to extend mask to be the same szie as sym_rot
                sym_int[ctr] = sym_int[ctr] +  (int((sym_rot & mask) > 0 ) << int(sym_idx))

                #could have issues on line below
                mask = mt.floor(mask>>1) 
                ctr = ctr - 1 
            #end while loop
            sym_idx_ext = sym_idx_ext + 1 
        #end foo loop

        #might have to do some appending stuff
        symbols_interleaved = np.hstack((symbols_interleaved, sym_int))
    #end for loop
    return symbols_interleaved 
    
##############################################################################


# LoRa_decode_shuffle unshuffles payload packet
#
#   in:  symbols       symbol vector
#        N             
#
#  out:  symbols_shuf  unshuffled symbols
def LoRa_decode_shuffle(symbols, N): 

    pattern = [5, 0, 1, 2, 4, 3, 6, 7] 
    symbols_shuf = np.zeros((1,N)) 
    symbols_shuf = symbols_shuf[0]
    
    for ctr in range(N) :
        for Ctr in range(len(pattern)):
            symbols_shuf[ctr] = symbols_shuf[ctr] + ( int(( int(symbols[ctr]) &  (1 <<pattern[Ctr])) >0)  << Ctr) 
        #end for loop
    #end for loop
    return symbols_shuf
##############################################################################

# LoRa_decode_hamming LoRa payload hamming decode (4,4 + CR)
#
#   in:  symbols       symbols with hamming
#        CR            Code Rate
#
#  out:  deocded      Fully decoded payload symbols
def LoRa_decode_hamming(symbols, CR): 

    # detection and correction
    if ( (CR>2) and (CR<= 4) ):

        n = mt.ceil(len(symbols)*4/(4 + 4)) 
        H = [0,0,0,0,0,0,3,3,0,0,5,5,14,14,7,7,0,0,9,9,2,2,7,7,4,4,7,7,7,7, \
            7,7,0,0,9,9,14,14,11,11,14,14,13,13,14,14,14,14,9,9,9,9,10,10,9, \
            9,12,12,9,9,14,14,7,7,0,0,5,5,2,2,11,11,5,5,5,5,6,6,5,5,2,2,1,1, \
            2,2,2,2,12,12,5,5,2,2,7,7,8,8,11,11,11,11,11,11,12,12,5,5,14,14, \
            11,11,12,12,9,9,2,2,11,11,12,12,12,12,12,12,15,15,0,0,3,3,3,3,3, \
            3,4,4,13,13,6,6,3,3,4,4,1,1,10,10,3,3,4,4,4,4,4,4,7,7,8,8,13,13, \
            10,10,3,3,13,13,13,13,14,14,13,13,10,10,9,9,10,10,10,10,4,4,13, \
            13,10,10,15,15,8,8,1,1,6,6,3,3,6,6,5,5,6,6,6,6,1,1,1,1,2,2,1,1, \
            4,4,1,1,6,6,15,15,8,8,8,8,8,8,11,11,8,8,13,13,6,6,15,15,8,8,1,1, \
            10,10,15,15,12,12,15,15,15,15,15,15] 

        deocded = np.zeros((1,n)) 
        deocded = deocded[0]
        
        #weird matlab indexing probs could be busted here...
        for ctr in range(n):
            #r0 = bitand(symbols[2*ctr+1],hex2dec("FF")) 
            r0 = int(symbols[2*ctr]) & 255

            if(2*ctr+2 > len(symbols)): 
                for x in range(len(symbols), (2*ctr+2)):
                    symbols =np.hstack((symbols, 0))
                    #symbols[(2*ctr+2)-1] = 0 

            #r1 = bitand(symbols(2*ctr+2),hex2dec("FF")) 
            r1 = int(symbols[(2*ctr+2)-1]) & 255 

            #again probably some werid matlab indexing crap
            s0 = H[r0] 
            s1 = H[r1] 

            deocded[ctr] = (s0<<4) | s1 
        #end loop 
        
    # detection TODO check when CR is in this range for python implementation
    elif( (CR > 0) and (CR <= 2) ):
        indices = [1, 2, 3, 5] 
        leng = len(symbols)
        deocded = [];
        Ctr = 0 
        for ctr in range(0, leng, 2):
            if(ctr+1 < leng):
                #s1 = bitand(selectbits(symbols(ctr+1),indices),hex2dec("FF")) 
                s1 = (selectbits(symbols[ctr+1],indices) & 255) 
            else:
                s1 = 0 
            
            s0 = (selectbits(symbols[ctr],indices) & 255) 
            deocded = np.hstack((deocded, ((s0<<4) | s1) ))
            Ctr = Ctr + 1 
        #end of for loope
    return deocded    

# LoRa_Decode_Full decodes full payload packet
#
#   in:  symbols_message         LoRa payload symbol vector
#        SF                      spreading factor  
#
#  out:  message_full          message symbols vector (decoded)
#        CR_pld                code rate of payload
#        pld_length            length of payload
#        CRC_pld               payload cyclic rate code flag
## Decode Header
def lora_decoder(symbols_message, SF):
    rdd_hdr         = 4 
    ppm_hdr         = SF - 2 
    symbols_hdr     = np.mod(np.round(np.divide(symbols_message[0:8],4)), 2**ppm_hdr)

    # Graying MATLAB hello world example pssed
    symbols_hdr_gry = LoRa_decode_gray(symbols_hdr) 

    # Interleaving MATLAB hellow world example passed
    symbols_hdr_int = LoRa_decode_interleave(symbols_hdr_gry,ppm_hdr,rdd_hdr)

    # Shuffle MATLAB hellow world example passed
    symbols_hdr_shf = LoRa_decode_shuffle(symbols_hdr_int,ppm_hdr) 

    # Hamming MATLAB hellow world example passed
    symbols_hdr_fec = LoRa_decode_hamming(symbols_hdr_shf[0:5],rdd_hdr) 

    ## Extract info from Header
    CR_pld          = mt.floor((int(symbols_hdr_fec[1])>>5)) 
    
    if((CR_pld > 4) or (CR_pld < 1)):
        return

    CRC_pld         = (mt.floor((int(symbols_hdr_fec[1])>>4)) % 2) 
    pld_length      = symbols_hdr_fec[0] + CRC_pld*2 

    ## Decode Payload
    rdd_pld         = CR_pld 
    ppm_pld         = SF 
    symbols_pld     = symbols_message[8:len(symbols_message)]

    # Graying MATLAB hello world example passed
    symbols_pld_gry = LoRa_decode_gray(symbols_pld) 

    # Interleaving, MATLAB hello world example passed
    symbols_pld_int = LoRa_decode_interleave(symbols_pld_gry,ppm_pld,rdd_pld) 

    # Shuffle MATLAB hello world example passed
    symbols_pld_shf = LoRa_decode_shuffle(symbols_pld_int, len(symbols_pld_int)) 

    # Add part of header MATLAB hello world example passed
    symbols_pld_hdr = np.hstack(( int(SF>7)*symbols_hdr_shf[((len(symbols_hdr_shf) - SF + 8)-1):len(symbols_hdr_shf)], symbols_pld_shf)) 

    # White MATLAB hello world example passed
    symbols_pld_wht = LoRa_decode_white(symbols_pld_hdr,rdd_pld,0) 

    # Hamming MATLAB hello world example passed
    symbols_pld_fec = LoRa_decode_hamming(symbols_pld_wht,rdd_pld) 

    # Swaping MATLAB hello world example passed
    symbols_pld_fin = LoRa_decode_swap(symbols_pld_fec) 

    ## Final Message
    #message_full    = np.hstack((symbols_hdr_fec, symbols_pld_fin))
    message_full    = symbols_pld_fin
    return message_full
