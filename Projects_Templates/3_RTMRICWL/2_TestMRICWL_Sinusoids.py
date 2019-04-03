
# coding: utf-8

# # Replaying Old Data
# 
# - Work under a separate branch with git (i.e. git checkout -b my-new-branch)
# 
# - Make a new folder in Projects (for your specific purposes)
# 
# - Copy this ipynb file that folder
# 
# - The data is stored on L-Drive
# 
# - the main gist of re-playing existing data is:
#     - that your first load everything into a big matrix with mne
#     - then initialize a specific **amp** (i.e., the "replayamp")
#     - then do exactly the same as normal, with a while True loop with calls to amp.get_data()
#     

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


# In[2]:


# this is the replay notebook - so select a file for playback - this is for eeglab files.

#fn=easygui.fileopenbox(default='*.set')
fn='trial_data_for_mri_cwl_development_withtrend.set'
# fn='eoec_withsins_30hT.set'
#fn='trio2_eoec_outside_before.set'
print(fn)

raw_fromfile = mne.io.read_raw_eeglab(fn)
montage=mne.channels.read_montage('standard_1005', ch_names=raw_fromfile.ch_names)  # always use MNE definitions
raw_fromfile.set_montage(montage)


# In[3]:


# properties of the recording, and some properties of the While Loop:
fs = raw_fromfile.info['sfreq']
nbchan = raw_fromfile.info['nchan']-1
updateTime = 0.1  # run some kind of calculation every X seconds
buffSize = 1.0  # run calculation on last X seconds of data


# In[4]:


# preparation to plot stuff in real time:
#get_ipython().run_line_magic('matplotlib', 'qt5')
plt.ion()  # enable widget plots & interactive plots

time_in_plot=2.0  # how much time in x-axis
sy1=deque(np.zeros(round(fs * time_in_plot)), round(fs * time_in_plot))  # for plotting - the FILO list
sy2=deque(np.zeros(round(fs * time_in_plot)), round(fs * time_in_plot))  # for plotting - the FILO list
sy3=deque(np.zeros(round(fs/10 * time_in_plot)), round(fs/10 * time_in_plot))  # for plotting - the FILO list

channel_to_plot=1
sx = np.linspace(0, time_in_plot, round(fs * time_in_plot))
sx2 = np.linspace(0, time_in_plot, round(fs/10* time_in_plot))


# In[5]:


# real-time data filtering -- high-pass filter (of 1.0 Hz)

f_low = 1.0
# f_high = 15.0
butter_ord = 3
lenchannels = nbchan

#rt_b, rt_a = signal.butter(butter_ord, [f_low / fn, f_high / fn], btype='band')
rt_b_hp, rt_a_hp = signal.butter(butter_ord, 2*f_low/fs, btype='high', analog=False)  # a digital high-pass filter
rt_zi_hp = proc.lfilter_zi(rt_b_hp, rt_a_hp, lenchannels)


# In[6]:


# real-time data filtering -- band-pass filter (of 12.0 - 15.0 Hz)

f_low = 12.0
f_high = 15.0
butter_ord = 3
lenchannels = nbchan

#rt_b, rt_a = signal.butter(butter_ord, [f_low / fn, f_high / fn], btype='band')
rt_b_bp, rt_a_bp = signal.butter(butter_ord, [2*f_low/fs, 2*f_high/fs], btype='band', analog=False)  # a digital high-pass filter
rt_zi_bp = proc.lfilter_zi(rt_b_bp, rt_a_bp, lenchannels)


# In[7]:


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


# In[8]:


amp = libmushu.get_amp('replayamp')
amp.configure(seed_d, seed_m, seed_ch, seed_fs, realtime=True, blocksize_samples=100)


# In[9]:


from rtfilters import HPF, LPF, BPF, MR, CWL, RESAMPLESAFE


# In[10]:


hpf=HPF(f=1.0, fs=5000, order=3, nbchan=38)
#bpf=BPF(f=[12.0, 15.0], fs=5000, order=3, nbchan=38)
#mr=MR(trsamples=10000, N_thr=5, corr_thr = 0.995, forget=6)
mr=MR(trsamples=9750, N_thr=5, corr_thr = 0.995, forget=5, highpass=[])
lpf=LPF(f=125, fs=5000, order=3, nbchan=38)
resample=RESAMPLESAFE(fs_source=5000, fs_target=500)
cwl=CWL(seconds_in_window=6.0, tdelay=0.050, ichs=list(range(30)), icws=list(range(32,38)), fs=500, highpass=[])

# there are several recommendations to follow when building your MRI artifact removal.
# it IS possible to do DC measurements in the MRI, but signal quality of MRI correction will suffer (only a little bit!) due to necessity of
# applying HPF on data for MRI artifact considerations, and absence of any filter on the data that is corrected.
# better to use hpf separately on data --> THEN MRI correction without any filters, than NO hpf and using hpf within the mr correction
# however, the latter I still implement in case of SCP NF - when you have to use the second option.


# In[11]:


amp.get_sampling_frequency()


# In[12]:


amp.start()


# In[13]:


def runLoop():
    alld=dynarray.DynamicArray((None, len(amp.get_channels())))     # the growing numpy data matrix
    allm=[]     # markers
    sfreq = amp.get_sampling_frequency()  # sampling frequency
    ch_names=amp.get_channels()  # channel names

    rb = RingBuffer(buffSize * 1000)  # the buffer containing the last X seconds of data - declared in MILISECONDS
    totalTime = seed_d.shape[0]/raw_fromfile.info['sfreq']

    fig=plt.figure()  # plotting...
    th=fig.suptitle('')
    ah1=fig.add_subplot(131)
    ah2=fig.add_subplot(132)
    ah3=fig.add_subplot(133)
    l1, = ah1.plot(sx, sy1)
    l2, = ah2.plot(sx, sy2)
    l3, = ah3.plot(sx2, sy3)


    # l=LoopState(); l.start()
    markeroffset = 0  # needed to store all data in one big mat/vector
    t0=time.time()
    curTime=time.time()
    markTime=time.time()
    st=''
    i=0; fnames=[] # for making a movie...
    while curTime - t0 < totalTime:  # l.get_state() != 'Stop':


        # keep track of time:
        curTime = time.time()

        # this is where you get the data
        data, marker = amp.get_data()


        if data.shape[0] > 0:  # this is crucial for remembering filter state.


            data2=hpf.handle(data)
            data3=mr.handle(data2)
            data4=lpf.handle(data3)
            data5=resample.handle(data4)
            data6=cwl.handle(data5)

            # something like this:
            #filterchain = [HPFilter, MRFilter, LPFilter, ResampleFilter, HPFilter, CWLFilter]

            #corr_data = ProcessFilters(chain, (data, marker))


            # use case -- first using the MR Corrector
            #mr_data = MRFilter.filter(data)

            # then -- using the CWL corrector
            #cwl_mr_data = CWLFilter.filter(data)


            #dataf, rt_zi_bp = signal.lfilter(rt_b_bp, rt_a_bp, data, axis=0, zi=rt_zi_bp)  # how to operate directly on the data

            cnt = io.convert_mushu_data(data, marker, sfreq, ch_names)
            mr_cnt = io.convert_mushu_data(data3, marker, sfreq, ch_names)
            cwl_cnt = io.convert_mushu_data(data6, marker, sfreq, ch_names)

            # f_cnt, rt_zi_bp = proc.lfilter(cnt, rt_b_bp, rt_a_bp, zi=rt_zi_bp)  # real-time data preprocessing...

            # plotting...
            sy1.extend(cnt.data[:,channel_to_plot])  # to visualize/plot -- s1 and s2 are deque's
            sy2.extend(mr_cnt.data[:,channel_to_plot])
            sy3.extend(cwl_cnt.data[:,channel_to_plot])


            l1.set_ydata(sy1)
            l2.set_ydata(sy2)
            l3.set_ydata(sy3)
            msy1=np.mean(sy1)
            msy2=np.mean(sy2)
            msy3=np.mean(sy3)
            ah1.set_ylim(-5000+msy1, 5000+msy1)
            ah2.set_ylim(-250+msy2, 250+msy2)
            ah3.set_ylim(-250+msy3, 250+msy3)

            fig.canvas.draw()
            fig.canvas.flush_events()

            # i+=1; fname = '_tmp%03d.png' % i; plt.savefig(fname); fnames.append(fname)

            # currently has no purpose
            newsamples = cnt.data.shape[0]

            # append to ringbuffer, so we can calculate features later on on the last N secs/samples of data.
            rb.append(cwl_cnt)

            # append it to the big matrix, for saving later on with pickle.
            alld.extend(data6)
            for m in marker:
                allm.append([m[0] + markeroffset, m[1]])
            markeroffset += newsamples / float(sfreq) * 1000.



            # do the following every 0.1 msec - with with the ringbuffer:
            if curTime - markTime > updateTime:
                # do Stuff

                markTime = curTime
                # 1) obtain last 1-second(s)
                d = rb.get()



                # clear_output(wait=True)  # write some logging information here
                # clear_output clear the output of the cell, but if you do that you also remove the figures, it seems
                # so don't do it!
                str1 = 'Playing Back - time = %f' % (curTime - t0)
                str2 = 'Length Markers: %d' % len(allm)
                str3 = '%d, %d' % data.shape
                #str4 = 'Feature Value: %f' % feature
                #str5 = 'Scaled Signal for NF: %f' % signalToSend
                #print(str1 + '\n' + str2 + '\n' + str3 + '\n' + str4 + '\n' + str5)

                # print('Length Markers: %d' % len(allm))
                # print(data.shape)
                th.set_text(str1 + '\n' + str2 + '\n' +str3)
                #featureth.set_text(str4 + '\n' + str5)



                
runLoop()
    

