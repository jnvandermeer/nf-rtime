# Estimators of Lag

1. Speed of the Loop, as measured in the size of data packets
2. and te-tb of single loop iterations
3. average of marker (eeg) and 'hit' annotation(s) -- there could be a systematic delay however due to time(costing) operations of t0 of the annotations struct; need to re-check it.


# Measurement Plan

1. Tests
   - Are we so slow that we grab 2 packets at once? Does this speed become slower if we update the graphics windows?
   - Does the speed become slower if we send stuff over to the Stimulation? 
   - Does this speed become slower if we send to stimulation and also receive all kinds of inputs?

2. Speed of TCP/IP Communications - Can we get some kind of speed effects if we fiddle around with the Nagle Algorithm used (commonly) in TCP/IP?

3. Speed of Bluetooth - Can we get a speed effect if we fiddle with the Latency Timer? For normal OS operations, 60 msec is very low - but for NF, it's a veritable eternity. Well, not that disastrous, but still something to take note of.

4. How Reliable are those lags? What could potentially cause time shifts - and how do we counteract those?

5. So what are the limits regarding those lags? Are they - in the grand sceme of things - something to worry about? Or can we - at a price - live with them?


# Potential Lag-Inducing hardware causes

1. TCP/IP Protocol
2. Network Traffic 'crowdedness'
3. CPU Jamming
4. Bluetooth Delays / timelags
5. (Time) Filtering Operations; Digital Filter Lags

