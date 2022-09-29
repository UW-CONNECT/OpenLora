import numpy as np
import math

def sym_to_data_ang(symbol,N):

    data = np.zeros((len(symbol) * N, 1), complex)
    accumulator = 0
    pi = math.pi

    #for j in symbol:
    j = 1
    phase = -pi+ (j-1)*(2 * pi/N)
    temp = np.zeros((N, 1), complex)
    for i in range(N):
    
        accumulator = accumulator + phase
        polar_radius = 1
        
        x = polar_radius * math.cos(accumulator)
        y = polar_radius * math.sin(accumulator)
        temp[i] = complex(x, y)
        
        phase = phase + (2 * pi/N)
        
    data = temp
    
    return data


