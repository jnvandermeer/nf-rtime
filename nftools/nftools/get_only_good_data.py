import mne
import re
import numpy as np

def get_only_good_data(raw_in, verbose=False):
    """ pass in a MNE raw object, with annotations and 'bad channels'
        get back the bad_channel_mask, bad samples, and the data within
        the MNE raw object with all gunk removed. Helper function.
        returns:
        bad_channel_mask (np arr of True/False; bad = False)
        np_data_in_raw_purged = a copy of the data with all bad inds, etc -  removed.
    """

    sampling_freq = raw_in.info['sfreq']
    bad_channels = raw_in.info['bads']
    bad_segments = [(a['onset'], a['duration']) for a in raw_in.annotations if re.search('BAD', a['description'])]
    # print(bad_channels)
    # for s in bad_segments: print('%.2g, %.2g' % (s[0], sum(s)))

    bad_channel_indices = [i for i, ch in enumerate(raw_in.info['ch_names'])  if ch in bad_channels]
    bad_channel_mask = [ch not in bad_channels for ch in raw_in.ch_names]


    if bad_segments:
        bad_segment_samples = np.concatenate([range(int(b * sampling_freq), int((b+d) * sampling_freq)) for b, d in bad_segments])
    else:
        bad_segment_samples=[]

    if verbose:
        print('channels to remove: %s' % bad_channel_indices)
        print('channel mask: ' + repr(bad_channel_mask))
        print('number of samples to remove: %s' % len(bad_segment_samples))

    # orig data
    np_data_in_raw_purged = raw_in.get_data()
    np_data_in_raw_purged = np.delete(np_data_in_raw_purged, bad_segment_samples, axis=0)
    np_data_in_raw_purged = np.delete(np_data_in_raw_purged, bad_channel_indices, axis=1)

    if verbose:
        print('raw original shape: %d, %d' % raw_in.get_data().shape)
        print('np new shape: %d, %d' % np_in_forica.shape)

    return bad_channel_mask, np_data_in_raw_purged


def no_bad_samples(raw_in, verbose=False):
    """ returns a raw data instance, in which data marked as 'bad' has been removed!
        we leave a marker 'b' where boundary is.
    """
    sampling_freq = raw_in.info['sfreq']
    bad_segments = [(a['onset'], a['duration']) for a in raw_in.annotations if re.search('BAD', a['description'])]
    bad_onsets = np.array([a['onset'] for a in raw_in.annotations])

    # magick to make boundary events:
    if len(bad_onsets)>1:
        for i in range(1, len(bad_onsets)):
            bad_onsets[i:] -= raw_in.annotations[i-1]['duration']

    boundary_annotations = mne.Annotations(0, 0, 'begin')
    for bad_ons in bad_onsets:
        boundary_annotations.append(bad_ons, 0, 'b')


    if bad_segments:
        bad_segment_samples = np.concatenate([range(int(b * sampling_freq), int((b+d) * sampling_freq)) for b, d in bad_segments])
    else:
        bad_segment_samples=[]

    if verbose:
        print('number of samples to remove: %s' % len(bad_segment_samples))

    np_data_in_raw_purged = raw_in.get_data()
    np_data_in_raw_purged = np.delete(np_data_in_raw_purged, bad_segment_samples, axis=1)
    # breakpoint()
    new_raw = mne.io.RawArray(
        np_data_in_raw_purged,
        raw_in.info
        )

    # potentailly we could do better here, but not now - we just inject new annots based on what we removed:
    if len(boundary_annotations) == 1:
        new_raw.set_annotations(None)
    else:
        new_raw.set_annotations(boundary_annotations[1:])


    return new_raw
    

def no_bad_channels(raw_in):
    """ returns a new raw data instance - with all bad channels removed!
    """
    annots = raw_in.annotations

    bad_channels = raw_in.info['bads']
    bad_channel_mask = [ch not in bad_channels for ch in raw_in.ch_names]

    bad_channel_indices = [i for i, ch in enumerate(raw_in.info['ch_names'])  if ch in bad_channels]

    data = raw_in.get_data()
    data = np.delete(data, bad_channel_indices, axis=0)


    old_info = raw_in.info
    new_ch_names = [ch_name for ch_name in old_info['ch_names'] if ch_name not in old_info['bads']]
    new_ch_infos = [infos for infos, ch_name in zip(old_info['chs'], old_info['ch_names']) if ch_name not in old_info['bads']]

    new_info = old_info.copy()
    new_info['bads'] = []
    new_info['chs'] = new_ch_infos
    new_info['ch_names'] = new_ch_names
    new_info['nchan'] = old_info['nchan'] - len(bad_channel_indices)

    # breakpoint()

    new_raw = mne.io.RawArray(
        data,
        new_info
        )

    new_raw.set_annotations(annots)
    new_raw.set_montage('standard_1020')

    return new_raw


def detect_channel_types(channel_names):

    standard_montage = mne.channels.read_montage("standard_1005")
    ch_types = ['misc'] * len(channel_names)
    for i, name in enumerate(channel_names):
        if name in standard_montage.ch_names:
            ch_types[i] = 'eeg'
        elif re.match('.*(eog|EOG).*', name):
            ch_types[i] = 'eog'
        elif re.match('.*(ecg|ECG).*', name):
            ch_types[i] = 'ecg'
        elif re.match('.*(sti|STI).*', name):
            ch_types[i] = 'stim'
        elif re.match('.*(emg|EMG).*', name):
            ch_types[i] = 'emg' 

    return ch_types
