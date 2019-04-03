# import all the needed stuff:

import time
import sys
import numpy as np 
import matplotlib
import matplotlib.pyplot as plt

import easygui  # popup windows with buttons made easy
import mne  # EEGLAB for python
from IPython.display import clear_output  # to clear the cell output during while loop
import re  # regular expressions
import pickle  # to save/load data
import dynarray  # a growing numpy array

import logging
logging.basicConfig(level=logging.ERROR)

sys.path.append("../../mushu")  # driver for the amps
sys.path.append("../../mushu/libmushu")
import libmushu

sys.path.append("../../nftools")  # handy stuff needed for NF
from nftools.loopcontrol import LoopState
from nftools.analysis import convert_alld_allm_to_mne
from nftools.analysis import select_part_from_mne_dataset
from nftools.analysis import plot_compare_two_spectra


sys.path.append("../../wyrm")  # real-time data analysis
from wyrm.types import RingBuffer
from wyrm.types import BlockBuffer
from wyrm import io
from wyrm import processing as proc

import scipy
from scipy import signal

from collections import deque  # a FILO list useful for plotting!


# this is the replay notebook - so select a file for playback - this is for eeglab files.

#fn=easygui.fileopenbox(default='*.set')
#fn='trial_data_for_mri_cwl_development_withtrend.set'
fn='/home/johan/tmp/wetransfer-1fe966/igortest.set'

#fn='eoec_30hT.set'
#fn='trio2_eoec_outside_before.set'
print(fn)

raw_fromfile = mne.io.read_raw_eeglab(fn)
montage=mne.channels.read_montage('standard_1005', ch_names=raw_fromfile.ch_names)  # always use MNE definitions
raw_fromfile.set_montage(montage)


# properties of the recording, and some properties of the While Loop:
fs = raw_fromfile.info['sfreq']
nbchan = raw_fromfile.info['nchan']-1
updateTime = 0.1  # run some kind of calculation every X seconds
buffSize = 1.0  # run calculation on last X seconds of data


# preparation to plot stuff in real time:
%matplotlib qt5 
plt.ion()  # enable widget plots & interactive plots

time_in_plot=2.0  # how much time in x-axis
sy1=deque(np.zeros(round(fs * time_in_plot)), round(fs * time_in_plot))  # for plotting - the FILO list
sy2=deque(np.zeros(round(fs * time_in_plot)), round(fs * time_in_plot))  # for plotting - the FILO list

channel_to_plot=10
sx = np.linspace(0, time_in_plot, round(fs * time_in_plot))



# real-time data filtering -- high-pass filter (of 1.0 Hz)

f_low = 1.0
# f_high = 15.0
butter_ord = 3
lenchannels = nbchan

#rt_b, rt_a = signal.butter(butter_ord, [f_low / fn, f_high / fn], btype='band')
rt_b_hp, rt_a_hp = signal.butter(butter_ord, 2*f_low/fs, btype='high', analog=False)  # a digital high-pass filter
rt_zi_hp = proc.lfilter_zi(rt_b_hp, rt_a_hp, lenchannels)


# real-time data filtering -- band-pass filter (of 12.0 - 15.0 Hz)

f_low = 12.0
f_high = 15.0
butter_ord = 3
lenchannels = nbchan

#rt_b, rt_a = signal.butter(butter_ord, [f_low / fn, f_high / fn], btype='band')
rt_b_bp, rt_a_bp = signal.butter(butter_ord, [2*f_low/fs, 2*f_high/fs], btype='band', analog=False)  # a digital high-pass filter
rt_zi_bp = proc.lfilter_zi(rt_b_bp, rt_a_bp, lenchannels)



# prepare data for replay (warning: need probably a lot of memory)

mul_factor = 1.0
if 1e-6 in [raw_fromfile.info['chs'][0]['cal'], raw_fromfile.info['chs'][0]['range']]:
    mul_factor = 1.0 / 1e-6

seed_d=raw_fromfile[:-1,:][0] * mul_factor  # scale the data to seed (so no 1e-6 stuff in the replayed data)
seed_d=np.array(seed_d.transpose())
seed_ch=raw_fromfile.ch_names[0:-1]
seed_fs=raw_fromfile.info['sfreq']

# prepare for replay; markers:
seed_mdata=np.transpose(raw_fromfile[-1,:][0])
seed_m=[[i / raw_fromfile.info['sfreq'] * 1000, int(m[0])] for i, m in enumerate(seed_mdata) if m > 0] 


amp = libmushu.get_amp('replayamp')
amp.configure(seed_d, seed_m, seed_ch, seed_fs, realtime=True, blocksize_samples=100)