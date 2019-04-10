#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:32:34 2019

@author: johan
"""


import functools
import logging
import re
import sys


import numpy as np
import scipy as sp
from scipy import signal
from sklearn.covariance import LedoitWolf as LW


class above_thr(object):
    def __init__(self,thr=1.0,dur=1.0,bcinet=None, chs=None):
        
        """
        Set the threshold to use
        Set the duration (above threshold) to use
        
        Then also give the bcinet object - so as to communicate with the nf-stim setup
        
        """
        
        self.times_called = 0
        self.thr = thr
        self.dur = dur
        self.chs = chs
        
        self.dur_for_area = self.dur

        self.bcinet=bcinet
        
        self._current_duration = 0.0 # in seconds...
        self._current_audio_duration = 0.0 # in seconds...
        self._current_area = 0.0
        

        
        print('thr: %.2f, dur: %.2f' % (thr, dur));
        if bcinet is not None:
            print('bcinet is up')
            
        self.signal_counter_sent = False
        self.signal_intensity_sent = False
        
        
            
        self.psduration = 0
        self.psarea = 0
        self.psareaduration = 0
        
        self.pprev_signal = 0
        self.pprev_duration = 0
        self.pprev_areaduration = 0
        self.pprev_area = 0

        
        # self._initialized = False
    
    
    def check_rising(self, dat):
        
        self.times_called += 1
        
        self.fs=dat.fs
        self.datsamples = dat.data.shape[0]
        
        # average tge signal
        this_signal = np.mean(dat.data[:,:],1)
        

        TF = np.zeros((this_signal.shape))
        audioTF = np.zeros((this_signal.shape))

        # repeatedly call it for each sample
        for i, s in enumerate(this_signal):
            self._check_each_sample(s)
            if self.TF:
                TF[i] = 1
            if self.audioTF:
                audioTF[i] = 1
                
        
        return TF, audioTF
        

        

    # apply a subfunction that we will call for each sample...
    # why it take me so long to come up with that solution?
    def _check_each_sample(self,s):
        # s is the signal.
        
        
        self.TF = 0
        self.audioTF = 0
        
        # is it bigger than 0?
        if s > self.thr:
            self.psarea += (s-self.thr) / self.fs
            self.psduration += 1.0 / self.fs
            self.psareaduration += 1.0 / self.fs
        else:
            self.psarea = 0
            self.psduration = 0
            self.psareaduration = 0
            
        if self.psduration == 0:
            self.signal_counter_sent=False
            
        if self.pprev_areaduration == 0:
            self.signal_intensity_sent=False

        if self.pprev_duration == 0:
            self.dur_for_area =  self.dur

            

        # so if bigger than duration -- send the signal, but don't keep sending it...
        if self.psduration >= self.dur and not self.signal_counter_sent:
            self.signal_counter_sent=True
            self.TF = 1

            if self.bcinet is not None:
                pass
            else:
                print('sending signal -- I ! - %d - %d - %s - %s' % (self.datsamples, self.times_called, str(True), str(-1)))
        

        if self.pprev_areaduration >= self.dur_for_area and s < self.pprev_signal and not self.signal_intensity_sent:
            self.signal_intensity_sent=True
            self.psareaduration=0
            self.dur_for_area += 0.050
            
            self.audioTF = 1
            
            if self.bcinet is not None:
                pass
            else:
                # import ipdb; ipdb.set_trace()
                print('sending signal! - %d %s - %s -- %s' % (self.times_called, str(False), str(self.pprev_area), str(self.dur_for_area)))
        
        
        self.pprev_signal = s
        self.pprev_duration = self.psduration
        self.pprev_areaduration = self.psareaduration
        self.pprev_area = self.psarea
        
        
            
            
            
            
