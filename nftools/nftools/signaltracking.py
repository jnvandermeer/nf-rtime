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
    def __init__(self,thr=1.0,dur=1.0,chs=chs,bcinet=bcinet):
        
        """
        Set the threshold to use
        Set the duration (above threshold) to use
        
        Then also give the bcinet object - so as to communicate with the nf-stim setup
        
        """
        
        self.thr = thr
        self.dur = dur
        
        self._current_duration = 0.0 # in seconds...
    
    
    def check(dat):
        
        
        # build a true/false vector:
        v=[np.mean(dat.data[:,self.chs],1) >= self.thr]
        
        l=[];s=self._current_duration;
        for i in v:
        if v==True:
            s+=1.0/dat.fs
        else:
            s==0.0
        l.append(s)
        
        # check/count whether things are above threshold
        
        
        
        
        # dat
        
        
        # check whether things are above threshold for longer than a specific time:
        
        
        
        # self._cu