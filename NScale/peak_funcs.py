#!/usr/bin/env python3

import numpy as np

# Returns idx, value
def nearest(arr, target, threshold):
    if arr.size == 0 or np.isnan(target):
        return -1, -1

    min_idx = np.argmin(np.abs(arr-target))

    if np.absolute(arr[min_idx] - target) > threshold:
        return -1, -1

    return min_idx, arr[min_idx]
