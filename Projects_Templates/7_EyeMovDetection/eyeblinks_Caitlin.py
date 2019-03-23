# -*- coding: utf-8 -*-
"""
Created on Thu Oct 11 13:14:05 2018

@author: thomasD
"""

import numpy as np
import matplotlib.pyplot as plt
import mne
import math
import time
import pickle
import glob
import peakutils
from peakutils.plot import plot as pplot

def MSDW(data, min_windowwidth, max_windowwidth):
    nRow = data.shape[0]
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
        
    return MSDW.msdw, MSDW.windowSize4msdw


   
    



#%% Detection of Artefact Range


def AR(data, min_windowwidth, max_windowwidth, threshold, min_th_abs_ratio, msdw, windowSize4msdw):
    nRow = data.shape[0]
    range_counter=0
    AR.range_ = np.zeros((nRow, 2))
    
    indexes_localMin = np.zeros((math.ceil(nRow/2), 1))
    indexes_localMax = np.zeros((math.ceil(nRow/2), 1))
    nLocalMin, nLocalMax = 0, 0
    LRValues_Spike = np.zeros((math.ceil(nRow/2), 2))
    LRWidths_Spike = np.zeros((math.ceil(nRow/2), 2))
    bAccept = np.zeros((math.ceil(nRow/2), 1))
    
    bTmpUp, bTmpDown, tmp_max_id, tmp_min_id, bMinFound = 0, 0, 0, 0, 0
    
    for i in np.arange(2,nRow):
        if (msdw[i-1] > msdw[i-2] and msdw[i-1] == msdw[i]):
            tmp_max_id = i-1
            bTmpUp=1
            bTmpDown=0
        elif (msdw[i-1] < msdw[i-2] and msdw[i-1] == msdw[i]):
            tmp_min_id = i-1
            bTmpDown, bTmpUp = 1, 0
        elif msdw[i-1] == msdw[i-2]:
            if msdw[i-1] > msdw[i]:
                if bTmpUp == 1:
                    nLocalMax += 1
                    indexes_localMax[nLocalMax] = round((i-1+tmp_max_id)/2)
                bTmpUp, bTmpDown = 0, 0
            elif msdw[i-1] < msdw[i]:
                if bTmpDown == 1:
                    nLocalMin += 1
                    indexes_localMin[nLocalMin] = round((i-1+tmp_min_id)/2)
                    bMinFound=1
                bTmpUp, bTmpDown = 0, 0
        elif(msdw[i-1] > msdw[i-2] and msdw[i-1] > msdw[i]):
            nLocalMax += 1
            indexes_localMax[nLocalMax] = i-1
        elif(msdw[i-1] < msdw[i-2] and msdw[i-1] < msdw[i]):
            nLocalMin += 1
            indexes_localMin[nLocalMin] = i-1
            bMinFound = 1
            
        if (bMinFound == 1 and nLocalMax > 0):
            id_min = int(indexes_localMin[nLocalMin])
            sum_ = msdw[int(indexes_localMax[nLocalMax])] - msdw[id_min]
            tmp_max_sum = sum_
            
            curmax_pos = int(indexes_localMax[nLocalMax])
            r_start=-1
            
            LRValues_Spike[nLocalMin,:] = np.array([msdw[int(indexes_localMax[nLocalMax])], msdw[id_min]])
            LRWidths_Spike[nLocalMin,:] = np.array([windowSize4msdw[curmax_pos], indexes_localMax[nLocalMax]-id_min-indexes_localMax[nLocalMax]])
            
            bAccept[nLocalMin] = isCriteriaSatisfied(sum_, threshold, min_th_abs_ratio, msdw[curmax_pos], msdw[id_min])
            
            if bAccept[nLocalMin] == 1:
                r_start = curmax_pos-windowSize4msdw[curmax_pos]
                if (range_counter > 0 and r_start <= AR.range_[range_counter, 1]):
                    r_start = AR.range_[range_counter, 1]
                    
            for k in np.arange(0, nLocalMax):
                if (nLocalMax-1-k <= 0 or indexes_localMin[nLocalMin]-indexes_localMax[nLocalMax-1-k] > max_windowwidth):
                    break
                
                curmax_pos = int(indexes_localMax[nLocalMax-1-k])
                prevmax_pos = int(indexes_localMax[nLocalMax-k])
                sum_ = sum_ + msdw[curmax_pos] - msdw[prevmax_pos]
                
                r_start_tmp = curmax_pos - windowSize4msdw[curmax_pos]
                
                tmp_check_result = isCriteriaSatisfied(sum_, threshold, min_th_abs_ratio, msdw[curmax_pos], msdw[id_min])
                if (sum_ > tmp_max_sum and (range_counter == 0 or r_start_tmp > AR.range_[range_counter, 0] or r_start_tmp <= AR.range_[range_counter, 0]) and tmp_check_result == 1):
                    tmp_max_sum = sum_
                    if (range_counter == 0 or r_start_tmp >= AR.range_[range_counter, 1]):
                        r_start = r_start_tmp
                        
                    while (range_counter > 0 and r_start_tmp <= AR.range_[range_counter, 0]):
                        range_counter -= 1
                        if (range_counter > 0 and r_start_tmp < AR.range_[range_counter, 1]):
                            r_start = AR.range_[range_counter, 1]
                        else:
                            r_start = r_start_tmp
                            
                    bAccept[nLocalMin] = tmp_check_result
                    LRValues_Spike[nLocalMin,:] = np.array([msdw[int(indexes_localMax[nLocalMax-1-k])], msdw[id_min]])
                    LRWidths_Spike[nLocalMin,:] = np.array([windowSize4msdw[curmax_pos], indexes_localMax[nLocalMax-1-k]-id_min-indexes_localMax[nLocalMax-1-k]])
                    
            if r_start > 0:
                range_counter += 1
                AR.range_[range_counter,:] = np.array([r_start, id_min])
                
            bMinFound=0
                    
    AR.range_ = AR.range_[~np.all(AR.range_ == 0, axis=1)]
            
    return AR.range_
        

def isCriteriaSatisfied(sum_, threshold, min_th_abs_ratio, window_acc_v_max, window_acc_v_min):
    bYes = sum_ > threshold and window_acc_v_max > threshold*min_th_abs_ratio and window_acc_v_min < -threshold*min_th_abs_ratio
    return bYes
                    

#%% Plotting Data

#plt.figure(figsize=(12, 10)); plt.subplot(311); plt.gca().set_title('Source Data (Fp1)', fontsize=16); plt.plot(x, 'k', label='Source Data'); plt.legend(loc='upper right');
#plt.subplot(312); plt.gca().set_title('Sum of First Derivatives', fontsize=16); plt.plot(MSDW.msdw, label='SDW'); plt.ylabel('Potential [μV]', fontsize=16); plt.legend(loc='upper right')#; #plt.show()
#plt.subplot(313); plt.gca().set_title('Detected Eyeblinks = %d' % AR.range_.shape[0], fontsize=16); plt.plot(x); plt.xlabel('Time (samples)', fontsize=16);
#for tt in range(len(AR.range_)):
#    plt.axvspan(AR.range_[tt,0], AR.range_[tt,1], alpha=0.2, color='#F08080', lw=0) 
#plt.tight_layout()
#plt.show()

#print('\nA total of %d eyeblinks were found' % AR.range_.shape[0])
#print('\nEye blink detection took %0.3f seconds' % (end-start))