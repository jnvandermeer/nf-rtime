# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 11:40:17 2018

@author: thomasD
"""

import numpy as np
import peakutils
from collections import deque
import itertools
#import matplotlib.pyplot as plt
#from peakutils.plot import plot as pplot

def eye_peaks(x):
    
    min_w = 200
    max_w = 800

    peaks = peakutils.indexes(np.asarray(x), thres=0.6, min_dist=np.mean(np.array([min_w, max_w]))*2)
    eye_peaks.length = len(peaks)
    #plt.figure(); pplot(np.arange(0,len(x)), x, peaks)
    #baseline = np.mean(deque(itertools.islice(x, 0, 2000)))
    baseline = np.mean(x)
    print(peaks)
    
    if len(peaks) > 0:
        for a in range(peaks[0], peaks[0]+1000):
            if x[a] < baseline:
                ind = a
                break
        
        avg_wdw = ind-peaks[0]
        eye_peaks.min_wdw = int(round(avg_wdw*0.9))
        eye_peaks.max_wdw = int(round(avg_wdw*1.5))