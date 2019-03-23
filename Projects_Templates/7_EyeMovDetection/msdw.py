# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 11:38:17 2018

@author: thomasD
"""

import numpy as np

def MSDW(data, min_windowwidth, max_windowwidth):
    nRow = len(data)
    v_data = np.zeros((nRow,))
    MSDW.msdw = np.zeros((nRow,))
    acc_v = np.zeros((nRow,))
    
    MSDW.windowSize4msdw = np.zeros((nRow,))
    
    for i in np.arange(1,nRow):
        v_data[i] = data[i]-data[i-1]
        acc_v[i] = acc_v[i-1]+v_data[i]
        
        if i==2:
            continue
        
        max_abs_window_acc_v, sign_change_counter, prev_sign = 0, 0, 0 
        sign = v_data[i]
        bBiggerDataFound, bSmallerDataFound = 0, 0
        
        for j in np.arange(0, max_windowwidth-1):
            if i-j > 0:
                sign = v_data[i-j]
            else:
                break
        
        if i-j-1 > 0:
            if sign*prev_sign < 0:
                sign_change_counter += 1
                
            if v_data[i] < v_data[i-j]:
                bBiggerDataFound=1
            elif v_data[i] > v_data[i-j]:
                bSmallerDataFound = 1
                
            if bBiggerDataFound*bSmallerDataFound == 1:
                break
            
            abs_win_acc_v = abs(acc_v[i]-acc_v[i-j-1])
            
            if (j >= min_windowwidth and abs_win_acc_v > max_abs_window_acc_v and sign_change_counter%2 == 0 and v_data[i]*v_data[i-j] >= 0):
                max_abs_window_acc_v = abs_win_acc_v
                MSDW.windowSize4msdw[i] = j+1
                
            if sign != 0:
                prev_sign = sign
                
        if MSDW.windowSize4msdw[i] == 0:
            MSDW.windowSize4msdw[i] = min_windowwidth
            
        if i-MSDW.windowSize4msdw[i]-1 > 0:
            MSDW.msdw[i] = acc_v[i]-acc_v[i-int(MSDW.windowSize4msdw[i])]
            
    for xx in range(1000):
        if MSDW.msdw[xx] != 0:
            break
        
    return MSDW.msdw, MSDW.windowSize4msdw, xx