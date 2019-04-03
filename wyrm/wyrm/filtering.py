#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 13:12:29 2019

@author: johan
"""


from scipy import signal
import numpy as np
# from scipy.signal import lfilter_zi






class bwFilter():
    def __init__(self, *args, **kwargs):
        if len(args)>0:
            print(self.__class__.__name__ + ": " + str(args))
        if len(kwargs)>0:
            print(self.__class__.__name__ + ": " + str(kwargs))
        
    
    def apply(self, dat, data):
        return(dat.copy(data=data))
    



class bwExponentialSmoother(bwFilter):
    def __init__(self, factor):
        super(bwExponentialSmoother, self).__init__(factor=factor)
        self.a = [1, -factor]
        self.b = [1 - factor]
        self.initialized=False
        self.bwFilter=bwFilter()

    def apply(self, dat):
        
        if not self.initialized:
            
            # import ipdb
            # ipdb.set_trace()
            self.initialized = True
            self.fs=dat.fs
            _, nbchan = dat.data.shape            
            self.nbchan=nbchan
            self.zi = np.zeros((max(len(self.a), len(self.b)) - 1, 1))
            self.zi = np.tile(self.zi, (nbchan, 1)).T
            # print('bla')
        
        data, self.zi = signal.lfilter(self.b, self.a, dat.data, zi=self.zi, axis=0)
        
        return self.bwFilter.apply(dat, data)



class bwSimpleAverager(bwFilter):
    def __init__(self, taps,f):
        super(bwSimpleAverager, self).__init__(taps=taps,f=f)

        self.bwFilter=bwFilter()
        
        self.initialized=False

        self.f=f
        self.taps=taps
        self.zi=-1


    def apply(self, dat):
        
        if not self.initialized:
            self.fs=dat.fs
            self.b = signal.firwin(self.taps,  2*self.f/self.fs)
            self.zi = signal.lfilter_zi(self.b, 1.0)
            _, nbchan = dat.data.shape            
            self.nbchan=nbchan
            self.zi = np.tile(self.zi, (nbchan, 1)).T
            self.initialized = True

            # print(self.initialized)
        
        #import ipdb
        #ipdb.set_trace()
        
        # one-by-one
        
        # dc=dat.data.copy()
        # for i, v in enumerate(dc):
        # zi=self.zi
        data, self.zi = signal.lfilter(self.b, 1.0, dat.data, zi=self.zi, axis=0)
        # self.zi = zi
        
        # newdata=dat.data
        # newdata[:,0] = data
        

        
        return self.bwFilter.apply(dat, data)






    

class bwHPF(bwFilter):
    """ to work with wyrm datasets - 2D, multi-channel EEG data
        you don't have to pre-specify how many channels you have
        it will harvest that directly out of the dat.
        
        Also, you don't have to specify what the fs is - that will, also,
        be harvested from dat - upon its first calling
    """
    
    def __init__(self, f=1.0, order=3):
        super(bwHPF, self).__init__(f=f, order=order)
        
        self.bwFilter = bwFilter()
        
        self.f=f
        self.order=order

        self.initialized=False
        self.zi = -1
        self.fs = -1
        self.b = -1
        self.a = -1

        
    
    def apply(self, dat):
        # do all kinds of stuff specific to this filter

        if not self.initialized:
            self.initialized = True
            self.fs=dat.fs
            
            _, nbchan = dat.data.shape            
            self.nbchan=nbchan


            self.b, self.a = signal.butter(self.order, 2*self.f/self.fs, btype='high', analog=False)
            zi = signal.lfilter_zi(self.b, self.a)
            self.zi = np.tile(zi, (nbchan, 1)).T
        
        
        data, self.zi = signal.lfilter(self.b, self.a, dat.data, zi=self.zi, axis=0)
        
        return self.bwFilter.apply(dat, data)
        



class bwLPF(bwFilter):
    """ keeps track of the zi for you"""
    def __init__(self, f=125.0, order=3):
        super(bwLPF, self).__init__(f=f, order=order)
        
        self.bwFilter = bwFilter()
        
        self.f=f
        self.order=order

        self.initialized=False
        self.zi = -1
        self.fs = -1
        self.b = -1
        self.a = -1

        
    
    def apply(self, dat):
        # do all kinds of stuff specific to this filter

        if not self.initialized:
            self.initialized = True
            self.fs=dat.fs
            
            _, nbchan = dat.data.shape            
            self.nbchan=nbchan


            self.b, self.a = signal.butter(self.order, 2*self.f/self.fs, btype='low', analog=False)
            zi = signal.lfilter_zi(self.b, self.a)
            self.zi = np.tile(zi, (nbchan, 1)).T
        
        
        data, self.zi = signal.lfilter(self.b, self.a, dat.data, zi=self.zi, axis=0)
        
        return self.bwFilter.apply(dat, data)



class bwBPF(bwFilter):
    """ keeps track of the zi for you"""
    def __init__(self, f_low=12.0, f_high=15.0, order=3):
        super(bwBPF, self).__init__(f_low=f_low, f_high=f_high, order=order)
        
        self.bwFilter = bwFilter()
        
        # self.f=f
        self.f_low, self.f_high = (f_low, f_high)
        self.order=order

        self.initialized=False
        self.zi = -1
        self.fs = -1
        self.b = -1
        self.a = -1

        
    
    def apply(self, dat):
        # do all kinds of stuff specific to this filter

        if not self.initialized:
            self.initialized = True
            self.fs=dat.fs
            
            _, nbchan = dat.data.shape            
            self.nbchan=nbchan


            self.b, self.a = signal.butter(self.order, [2*self.f_low/self.fs, 2*self.f_high/self.fs], btype='band', analog=False)
            zi = signal.lfilter_zi(self.b, self.a)
            self.zi = np.tile(zi, (nbchan, 1)).T
        
        
        data, self.zi = signal.lfilter(self.b, self.a, dat.data, zi=self.zi, axis=0)
        
        return self.bwFilter.apply(dat, data)

