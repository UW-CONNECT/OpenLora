import numpy as np
import math

def chirp_template_v2(num_symb, HW_offset):
# num_symb: # of samples in a chirp
    pi = math.pi

    up_chirp = np.zeros((2*num_symb, 1), complex)
    down_chirp = np.zeros((2*num_symb, 1), complex)

    phase = -pi + HW_offset
    accumulator = 0

    for i in range(2*num_symb):
        accumulator = accumulator + phase
        polar_radius = 1

        x = polar_radius*math.cos(accumulator)
        y = polar_radius*math.sin(accumulator)

        up_chirp[i] = complex(x, y)
        down_chirp[i] = complex(x, -y)

        phase = phase + 2*pi/num_symb

    return up_chirp, down_chirp
