#!usr/bin/env python3

import lora_decode_pyth as decode

def main():
    #symbols = [36, 8, 0, 112, 220, 192,  68, 212, 156,  48,  27,  10,  51, 194, 182, 243, 179,  96, 136, 165, 121, 0,  66, 233,  24,  65,  76,  36, 224, 138, 222, 193, 119, 215,  35,  54, 250, 6, 162, 183,  64,  61,  50]
    symbols = [933, 13, 993, 497, 3777, 1021, 945, 709, 999, 3213, 1487, 2898, 3210, 2139, 4018, 2887, 33, 3149, 3293, 1285, 682, 3310, 2224]

    message = decode.lora_decoder(symbols, 12)
    print(message)
    for bits in message:
        print(chr(int(bits)), end='')

if __name__ == '__main__':
    main()
