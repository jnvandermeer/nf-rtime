#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:32:34 2019

@author: johan
"""


# import functools
# import logging
# import re
# import sys


import numpy as np
# import scipy as sp
# from scipy import signal
# from sklearn.covariance import LedoitWolf as LW

import sys
sys.path.append("..") # Adds higher directory to python modules path.
from callpyff import bcixml 
import time





class sending_to_nfstim(object):
    def __init__(self, sampling_frequency, thr=1.0, dur=1.0, bcinet=None, chs=None, feedback_type='eeg', verbose=False, dt_between_sending_data=1/60., **kwargs):
        
        """
        This is quite heavily integrated with the neurofeedback stimulation stuff running on the stimulus computer.
        the names of the variables are the same as over there, and you'd need to understand some of the 'gears' of
        the stimulus to understand signals are passed and thay they mean.

        The messages are basically all Pyff "Control" signals, which trigger a variety of things such as setting the 
        threshold (for EEG or EMG), playing of a visual or auditory marker, or passing through a signal.

        It seems rather overcomplicated to use an entire encoding of a Control Signal with an XML-like means.. and 
        it is. This (as well as the pyff/psychopy in python2) will be one of the things that will be re-written,
        once me (or someone else) can get to that.

        Regarding Pyff, much is made of the Control and the Interaction signals. It is a bit of a horrible mess. 
        Interaction signals are things that start/stop the stimulation, but if you carefully look at the signal
        itself, they are no different - just a different location (interaction - 0, control - 1) in a dictionary.
        Why no two different kinds of data streams for the two purposes? 

        
        Then also give the bcinet object - so as to communicate with the nf-stim setup.

        
        """
        
        self.verbose=verbose
        self.bcinet=bcinet
        
        if feedback_type == 'eeg':
            self.control_ev_key = 'hit'
            self.signal_key = 'nfsignalContainer'
            self.set_thr_key = 'thrContainer'
            
            # so as to make the feedback go from 0 to 10 (5 units per lower/upper half)
            self._st_offset = -1
            self._st_scaling = 10
            
        elif feedback_type == 'emg':
            self.control_ev_key = 'hitError'
            self.signal_key = 'emgContainer'
            self.set_thr_key = 'emgThrContainer'
        
            # so as to make THAT feedback go from 0 to 20 (20 units between lowest and highest)
            self._st_offset = 0
            self._st_scaling = 20

        if 'st_scaling' in kwargs.keys():
            self._st_scaling=kwargs['st_scaling']        

        self.fs = sampling_frequency

        self.times_called = 0
        self.thr = thr
        self.dur = dur
        self.chs = chs
        
        self.dur_for_area = self.dur

        self.bcinet=bcinet
        
        self._current_duration = 0.0 # in seconds...
        self._current_audio_duration = 0.0 # in seconds...
        self._current_area = 0.0

        self.feedback_type = feedback_type

        
        print('thr: %.2f, dur: %.2f' % (thr, dur));
        if bcinet is not None:
            print('bcinet is passed on')
            
        self.signal_counter_sent = False
        self.signal_intensity_sent = False
        
            
        self.psduration = 0
        self.psarea = 0
        self.psareaduration = 0
        
        
        self.pprev_signal = 0
        self.pprev_duration = 0
        self.pprev_areaduration = 0
        self.pprev_area = 0


        if feedback_type == 'eeg':
            self._st_lower_offset = 0.2
            self._st_upper_offset = 0.05
            # self._st_min_dur_for_chime = self.dur # what is the minimum?
            self._st_max_dur_for_chime = 5 * self.dur # what's the maximum?


        elif feedback_type == 'emg':
            self._st_lower_offset = 0
            self._st_upper_offset = 0
            # self._st_min_dur_for_chime = self.dur
            self._st_max_dur_for_chime = 5 * self.dur # what's the maximum?


        st_scaling = self._st_scaling  
        self.st_scaling = st_scaling          
        if 'st_lower_offset' in kwargs.keys():
            self._st_lower_offset = kwargs['st_lower_offset']
        elif 'st_upper_offset' in kwargs.keys():
            self._st_upper_offset = kwargs['st_upper_offset']
        elif 'max4audio' in kwargs.keys():
            self._st_max_dur_for_chime = kwargs['max4audio']
        elif 'st_scaling' in kwargs.keys():
            st_scaling=kwargs['st_scaling']
            
        self.given_st_scaling= st_scaling

        # communicate this to the BCI system...            
        self.set_ststim_scaling(st_scaling)
        self.set_threshold(thr)
        self.set_stposition_loweroffset(self._st_lower_offset)
        self.set_stposition_upperoffset(self._st_upper_offset)
        # self.set_threshold(thr)

        # some lines to prevent sending so much data via the complicated XML/Control signal protocol
        # that the stimulus computer would have problems keeping up
        self.last_sent_time = time.time()
        self.dt_between_sending_data = dt_between_sending_data  # default value is 60, usual screen refresh rate
        # self._initialized = False
    
    
    def check_above_threshold(self, dat):
        """ checks if the data exceeds the threshold and zaps the respective 
            triggers towards the ststim
            dat = wyrm data, of which the average will be taken.
        """
        
        self.times_called += 1
        
        # self.fs=dat.fs
        self.datsamples = dat.shape[0]
        
        # average tge signal
        this_signal = dat # np.mean(dat[:,:],1)
        

        TF = np.zeros((this_signal.shape))
        audioTF = np.zeros((this_signal.shape))

        # repeatedly call it for each sample
        for i, s in enumerate(this_signal):
            self._check_each_sample(s)
            if self.TF:
                TF[i] = 1
            if self.audioTF:
                # audioTF[i] = 1
                audioTF[i] = self.audioTF
                
        return TF, audioTF
        


    def send_data_signal(self, dat):
        """ Sends a sample to the stimulus setup (using appropriate scaling)
            best not to send every sample!
        """
        
        this_signal = dat # np.mean(dat[:,:],1)
        to_send = np.median(this_signal)
        
        # change scalings - emg from 0 to 1; eeg from -1 to +1
        to_send_scaled = to_send / self._st_scaling + self._st_offset
        
        # check how much time since the last send:
        if time.time() - self.last_sent_time > self.dt_between_sending_data:
            if self.bcinet is not None:
                # send the actual signal. This is a horribly convoluted way of sending anything.
                # also no point in abstractifying this mess in order to make it more pretty.
                self.last_sent_time = time.time()
                self.bcinet.send_signal(bcixml.BciSignal({self.signal_key: to_send_scaled}, None, bcixml.CONTROL_SIGNAL))

        return to_send_scaled
        


    # apply a subfunction that we will call for each sample...
    # why it take me so long to come up with that solution?
    def _check_each_sample(self,s):
        """ A subfunction that runs on each sample and determines whether
            A trigger (of what kind) needs to be sent
        """
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
            self.psduration = 0   # total time above threshold
            self.psareaduration = 0 # total time abovethreshold since LAST AUDIO STIMULUS!!
            
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
                self.bcinet.send_signal(bcixml.BciSignal({self.control_ev_key: [True, -1]},None, bcixml.CONTROL_SIGNAL))
            else:
                pass
            if self.verbose:
                print('sending signal -- I ! - %d - %d - %s - %s' % (self.datsamples, self.times_called, str(True), str(-1)))
        

        if self.pprev_areaduration >= self.dur_for_area and s < self.pprev_signal and not self.signal_intensity_sent:
            self.signal_intensity_sent=True
            self.psareaduration=0
            # self.dur_for_area_to_send=self.psduration
            self.dur_for_area += 0.050
            
            # this will be converted to a chime with the correct pitch
            to_send_rating_from_0_to_10 = self._from_st_duration_to_0_10_rating(self.psduration)
            
            self.audioTF = to_send_rating_from_0_to_10 + 1
            
            if self.bcinet is not None:
                self.bcinet.send_signal(bcixml.BciSignal({self.control_ev_key: [False, to_send_rating_from_0_to_10]},None, bcixml.CONTROL_SIGNAL))
            else:
                pass
                # import ipdb; ipdb.set_trace()
            if self.verbose:
                print('sending signal! - %d %s - %s -- %s' % (self.times_called, str(False), str(self.pprev_area), str(self.dur_for_area)))
        
        
        self.pprev_signal = s
        self.pprev_duration = self.psduration
        self.pprev_areaduration = self.psareaduration
        self.pprev_area = self.psarea
        


    # I need some magic to convert a duration (specified what is minimum depending on self.thr) and scaling
    # into a number from 0 to 10.
    



    def set_ststim_scaling(self, new_scaling):
        """ set how much of signal you wish to put into your feedback here. 
            F.E. 10 uV for EEG means bottom screen = 0; top screen = 10.
            For the EMG it's f.e. 20 between bottom and the top!
        """
        
        # this basically just asks what the scling is supposed to be...
        self.given_st_scaling = new_scaling
        
        if self.feedback_type == 'eeg':
            self._st_offset = -1 + self._st_lower_offset * 2.0
            self._st_scaling = new_scaling * 0.5 / (1 - self._st_lower_offset - self._st_upper_offset)
        elif self.feedback_type == 'emg':
            self._st_offset = 0 + self._st_lower_offset / 1.0
            self._st_scaling = new_scaling / (1 - self._st_lower_offset - self._st_upper_offset)

        # also change value for threshold...            
        self.set_threshold(self.thr)



        
    def set_threshold(self, new_threshold):
        """ Sets a new threshold -- it will also change the threshold sent to the ststim!
        """
        
        # this changes the threshold...
        # so we do two things here: a) set internal transformation(s) so signal 
        # is transformed accordingly in subsequent calls to send_data_signal and
        # check_data_threshold
        #
        # + send a signal to nfstim with the changes to threshold
        self.thr = new_threshold
        
        # change scalings - emg from 0 to 1; eeg from -1 to +1
        new_threshold_for_st = self.thr / self._st_scaling + self._st_offset
        
        if self.bcinet is not None:
            self.bcinet.send_signal(bcixml.BciSignal({self.set_thr_key: new_threshold_for_st},None, bcixml.CONTROL_SIGNAL))
        else:
            pass
            # print('sending: %.2f' % new_threshold_for_st)
        
        self._new_thr_for_st = new_threshold_for_st
            

    def set_new_duration(self, new_duration):
        self.dur = new_duration
        self.dur_for_area = self.dur

            
    def set_stposition_loweroffset(self, offset):
        """ this should ideally remain 0, but if so required - you can apply an offset (fractional, between 0 and 1)
            to the lower part of the stimulus window.
            This means, you can lift up the stimulus a little bit -- just like with Matlab axes position definitions.
            So if you think it's ugly to have the stimulus only be at the lower half of the screen, you can put stuff
            into the middle while not tampering with any thresholding here.
           
            This does change _st_offset and _st_scaling, to accomodate the desired behavior.
            
        """
        self._apply_offset_changes(offset, self._st_upper_offset)
        
        
        
        
        
    def set_stposition_upperoffset(self, offset):
        """ this should ideally remain 0, but if so required - you can apply an offset (fractional, between 0 and 1)
            to the lower part of the stimulus window.
            This means, you can lift up the stimulus a little bit -- just like with Matlab axes position definitions.
        """
        self._apply_offset_changes(self._st_lower_offset, offset)
        
        
        
    def _apply_offset_changes(self, lower, higher):
        """ actually do the work
        """
        
        self._st_lower_offset = lower
        self._st_upper_offset = higher
        
        
        self.set_ststim_scaling(self.given_st_scaling)
        
        # space_left = 1.0 - lower - higher
        
        # self._new_st_scaling = self._st_scaling + 
            
    def _from_st_duration_to_0_10_rating(self, this_duration):
        
        # breakpoint()
        value = (this_duration - self.dur) / self._st_max_dur_for_chime * 10
        
        if value < 0:
            print('it should never happen that a marker is sent when the length is smaller than needed: ' + str(value))
            
        if value > 10:
            value = 10
            
        return value
        
        
