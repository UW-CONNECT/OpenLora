import math
import numpy as np

def chirp_template(num_symb):

    pi = math.pi
    up_chirp = np.zeros((2*num_symb, 1), complex)
    down_chirp = np.zeros((2*num_symb, 1), complex)
    phase = -pi
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
