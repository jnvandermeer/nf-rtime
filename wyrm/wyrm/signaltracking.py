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
        
        self.thr = thr
        self.dur = dur
        self.chs = chs

        self.bcinet=bcinet
        
        self._current_duration = 0.0 # in seconds...
        self._current_audio_duration = 0.0 # in seconds...
        self._current_area = 0.0
        

        
        print('thr: %.2f, dur: %.2f' % (thr, dur));
        if bcinet is not None:
            print('bcinet is up')
            
        self.signal_counter_sent = False
        self.signal_intensity_sent = False
        
        
        # self._initialized = False
    
    
    def check_rising(self, dat):
        
        
        # average tge signal
        this_signal = np.mean(dat.data[:,:],1)
        
        # naje something that's true/false:
        bigger_than_thr = this_signal >= self.thr
        
        durations=[]
        area_durations=[]
        areas=[]

        sign_duration=self._current_duration
        area_duration=self._current_audio_duration
        area=self._current_area
        
        for sig, tf in zip(this_signal, bigger_than_thr):
            if tf==True:
                sign_duration += 1.0/dat.fs # time 
                area_duration += 1.0/dat.fs
                area += sig * (1/dat.fs) # area
                
            else:
                sign_duration=0.0
                area_duration=0.0
                area=0.0

            durations.append(sign_duration)
            area_durations.append(area_duration)
            areas.append(area)
        
        
        send_counter = False
        send_signal_intensity = False
            
        
        # check/count whether things are above threshold
        if max(durations) >= self.dur:
            send_counter = True
            index_of_duration = durations.index(max(durations))
            

        if max(area_durations) >= self.dur and not max(area_durations) == area_durations[-1]:
            send_signal_intensity = True
            # what's the area at the highest time?
            
            index_of_area = np.where(np.logical_and(bigger_than_thr, this_signal==max(this_signal)))
            area_to_send = areas[index_of_area]
            # max(consider_these_values)
            # index_highest_voltage = this_signal.index(max_this_signal)
            self._current_audio_duration = (len(areas) - index_of_area) / dat.fs


        
        if send_counter and not self.signal_counter_sent:
            # print('sending signal!')
            self.signal_sent = True
            
            # reset...
            # self._current_duration = 0.0 # in seconds...
            
            if self.bcinet is not None:
                print('sending signal! - %s - %s' % (str(True), str(-1)))
                
                #send interaction signal - 2 elements: [True/False, Intensity]
                
            # we send a signal - which contains a value
            # a values of -1 does not play any sound -- a value > 1 plays a sound - since the value determines what the pitch is


        
        if send_signal_intensity and not self.signal_counter_sent:
            print('sending signal!')
            self.signal_intensity_sent = True
            
            # ... what... IS the intensity !!?!?!?            
            if self.bcinet is not None:
                print('sending signal! - %s - %s' % (str(False), str(area_to_send)))
            
            
            self.signal_intensity_sent = False
            
            
        # if it hits 0 anytime after - reset stuff...
        # is there any False (or 0) AFTER index?
        if self.signal_counter_sent and any(bigger_than_thr[index_of_duration:]==False):

            # time to reset everything            
            self.signal_counter_sent = False
            self.signal_intensity_sent = False

            self._current_duration = 0.0 # in seconds...
            self._current_audio_duration = 0.0 # in seconds...
            self._current_area = 0.0
        

            
        # check if we need to reset signal_intensity_sent here:
        # if self.signal_intensity_sent = True and 
        
        # check if anywhere after the max durations, a False occurs...
        # where in the list did it occur?
        
        
        # dat
        
        
        # check whether things are above threshold for longer than a specific time:
        
        
        
        # self._cu