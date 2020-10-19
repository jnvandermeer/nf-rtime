import scipy
from scipy.signal import hilbert
from scipy.optimize import curve_fit, fmin, fmin_bfgs
import matplotlib.pyplot as plt
import numpy as np

def find_mode(v, make_plot=False):
    """ instead of determining the mean, or the median, we determine the mode to use as a threshold. 
        using a histogram approach and fit of a quadratic function

        The 'ahv'; is first calculated; this is the abs of the hilbert transform of v
        Then a histogram of the ahv is made to find the mode of ahv.

        The mode can be used as an amplifier-independent and signal intensity-independent estimator of 
        the base amplitude of the signal (v) that is the same even when signals are quite bursty

        Within scipy there is also another mode function in the stats module. I haven't check that
        function yet, but it might be used to replace this function.

        The shape of the histogram matches a Raileigh distrbution, so on order to estimate the mode
        an inverse quadratic function is fitted to the top part. This model is
        y = y_offset - rc * (x - x_offset)^2. The x_offset is then the estimator of the mode.
        See publication: Automatic noise-level detection for extra-cellular micro-electrode recordings,
        Dolan K, Martens HC, Schuurman PR, Bour LJ, Med Biol Eng Comput. 2009 Jul;47(7):791-800. 
        doi: 10.1007/s11517-009-0494-4.
        This approach is applied for microelectrode recordings; but, can also be used for the 
        EEG signals used in Neurofeedback.


        The histogram is based on 500 mins in the range of 0 to 5*the median value of ahv


        input
        -----
        v          = a 1D vector (shape of (N, ); NOT shape of (N, 1)!
        make_plot  = plot the histogram and its fit (True) or not (False [default])


        output
        ------
        mode       = the mode as estimated as described above


        """
    ahv=abs(hilbert(v))
    [h, edges] = np.histogram(ahv, bins=500, range=(0, 5*np.median(ahv)))
    
    # define model; the inverse quadratic function
    model = lambda x, xoff, yoff, rc: yoff - rc*(x - xoff)**2
    
    # grab our x and y that we wish to fit; add half of the diff of the edges
    fit_x, fit_y = zip(*np.array([[te, th] for th, te in zip(h, edges) if th > 0.50 * max(h)]))
    fit_x += np.mean(np.diff(fit_x))/2
    
    # make initial (best) guesses
    init_xoff, init_yoff, init_rc = (np.mean(fit_x), max(fit_y), ((max(fit_y)-min(fit_y))/np.mean(fit_x))**0.5)
    
    # fit the model!
    global my_fitting_cov # dirty trick to allow us to access the covariance (for checking cov between fitting parameters)
                          # since it's a dirty trick, I will use a very unlikely name to be overwritten
    ((xoff, yoff, rc), cov) = curve_fit(model, fit_x, fit_y, p0=[init_xoff, init_yoff, init_rc], absolute_sigma=True)
    
    if make_plot:
        plt.figure()
        plt.plot(edges[:-1] + np.mean(np.diff(fit_x))/2, h) # plot our original histogram
        plt.plot(fit_x, fit_y) # plot the part that we try to fit
        plt.plot(fit_x, list(map(lambda x: model(x, xoff, yoff, rc), fit_x))) # plot the model!!
        plt.vlines(xoff, 0, init_yoff)
        plt.legend(['abs(hilbert(v))', 'data to fit', 'quadratic fit','mode'])
        plt.xlabel('amplitude of signal (binned)')
        plt.ylabel('count of abs(hilbert(v)) within the bins')
        plt.title('find signal mode by fitting inverse quadratic')
    
    # return the mode, which is xoff. we don't care about yoff and rc.
    return xoff


# from Joe Kington's answer here https://stackoverflow.com/a/4495197/3751373
# with minor edits
def contiguous_regions(condition):
    """Finds contiguous True regions of the boolean array "condition". Returns
    a 2D array where the first column is the start index of the region and the
    second column is the end index.
    
    Works only on numpy vectors; so we expand it to work with the code
    obtained from stackoverflow.
    
    input MUST (likely) be a vector with no 1-dim dimensions
    """

    condition = np.expand_dims(condition, 1)
    
    # Find the indicies of changes in "condition"
    d = np.diff(condition,n=1, axis=0)
    idx, _ = d.nonzero() 

    # We need to start things after the change in "condition". Therefore, 
    # we'll shift the index by 1 to the right. -JK
    # LB this copy to increment is horrible but I get 
    # ValueError: output array is read-only without it 

    mutable_idx = np.array(idx)
    mutable_idx +=  1
    idx = mutable_idx

    if condition[0]:
        # If the start of condition is True prepend a 0
        idx = np.r_[0, idx]

    if condition[-1]:
        # If the end of condition is True, append the length of the array
        idx = np.r_[idx, condition.size] # Edit

    # Reshape the result into two columns
    idx.shape = (-1,2)
    return idx


def detect_bursts(v, thr, dur):
    """ to prevent us from having to write this so many other times."""
    
    return [(b, e-b) for b, e in contiguous_regions(v > thr) if e-b > dur ]
    


def determine_optimal_threshold(v, fs, dur, bursts_per_5min, make_plot=False, inverse_training=False):
    """ uses the mode as well as find_consecutive_regions to optimize the threshold to 
        coincide with a number of bursts to be expected per 5 minutes.
        
        Uses Powell to optimize; not standard fminsearch or fmin.
    
        inputs
        ------
        
        v                 = the signal
        fs                = sampling rate
        dur               = desired burst duration
        bursts_per_5_min  = how many bursts you wish in a 5 minute interval
        make_plot         = if you wish to make a figure of convergence (True) or not (False [default])
        
        outputs
        -------
        thr               = multiplication of the MODE of the signal to reach N bursts
        nbursts           = how many bursts are actually detected at that threshold
        detected_bursts   = a list of onsets and durations (in samples!) of the bursts at optimum
        
        Note: The threshold is thr * find_mode(v); see find_mode function for more information.
        the mode is a reasonably unbiased estimate of the signal's power. Therefore the thr obtained
        with this method should be comparable across signal types, ranges, sampling rates and EEG systems (!) 
    
    """
    
    # pre-calculate to save computation time
    mode_v = find_mode(v)
    
    
    ahv = abs(hilbert(v))
    #if inverse_training:
    #    ahv = -1 * abs(hilbert(v))
    
    # how many bursts we need to have to fulfill criterion
    # breakpoint()
    nbursts = len(v)/fs/60/5 * bursts_per_5min # we fit until we get 90 bursts
    
    # this is the function to minimize
    #if inverse_training:
    #    model = lambda thr: abs(nbursts - len([(b, e-b) for b, e in contiguous_regions(ahv >  thr*mode_v) if e-b > dur*fs ]))
    #else:
    if inverse_training:
        model = lambda thr: abs(nbursts - len([(b, e-b) for b, e in contiguous_regions(-1*ahv > thr*mode_v) if e-b > dur*fs ]))
    else:
        model = lambda thr: abs(nbursts - len([(b, e-b) for b, e in contiguous_regions(ahv > thr*mode_v) if e-b > dur*fs ]))
    
    # optimize!
    # xopt, = fmin(model, 1, disp=0) # backwards search
    if inverse_training:
        tmp = scipy.optimize.minimize(model, -1, method="powell")    
    else:
        tmp = scipy.optimize.minimize(model, 1, method="powell")
    xopt = tmp.x
    
    
    if inverse_training:
        detected_bursts = detect_bursts(-1*abs(hilbert(v)), -1*2*find_mode(v), dur*fs) # a list of onsets and durations (in sampless)
    else:
        detected_bursts = detect_bursts(abs(hilbert(v)), 2*find_mode(v), dur*fs) # a list of onsets and durations (in sampless)
    
    
    if make_plot:
        plt.figure()
        xdata = np.arange(1000)*0.001 + xopt - 0.50
        ydata = list(map(model, xdata))
        plt.plot(xdata, ydata)
        plt.vlines(xopt, 0, max(ydata))
        plt.legend(['diff in bursts from {}'.format(nbursts), 'mode multiplier = {:2.4f}\nmin = {:2.2f}'.format(xopt, model(xopt))])
        plt.xlabel('threshold (mode_multiplier)')
        plt.ylabel('diff between requested bursts & bursts from threshold')
        plt.title('find threshold that produces {} bursts in 5 minutes\nWe have {:2.2f} minutes of data, so request = {:2.2f} bursts'.format(bursts_per_5min, len(v)/fs/60, nbursts))


        
    
    return float(xopt), len(detected_bursts), detected_bursts
    
