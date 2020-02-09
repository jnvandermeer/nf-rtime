# breakpoint()
from pynfb.widgets import signal_viewers as sv
#from pynfb_widgets import signal_viewers as sv
from PyQt5 import QtWidgets
# import datetime
#import sv.SignalViewer as SignalViewer
#import sv.RawSignalViewer as RawSignalViewer
#print(pynfb_widgets)
# print('hallo')
# from .sv import *
from PyQt5.QtCore import QTime, QTimer





# I can change this as I want/need:
class CustomSignalViewer(sv.RawSignalViewer):
    def __init__(self, fs, names, seconds_to_plot=5, overlap=False, **kwargs):
        signals_to_plot = len(names)
        super(CustomSignalViewer, self).__init__(fs, names, seconds_to_plot=5, signals_to_plot = signals_to_plot, overlap=False, **kwargs)
        self.indexes_to_plot = [slice(j, min(self.n_signals, j+signals_to_plot)) for j in range(0, self.n_signals, signals_to_plot)]
        self.n_signals_to_plot = signals_to_plot





# most basic example of visualization; but then that we can have the pushbutton/RUNLOOP
# command to stop the loop as we require.
class AcquireData(QtWidgets.QWidget):

    # init our modest window
    def __init__(self, fs, names, **kwargs):
        super(AcquireData, self).__init__()
        self.datawidget = CustomSignalViewer(fs, names, **kwargs)
        
        self.stopacquisition = QtWidgets.QPushButton('Stop Acquisition')

        self.timerinfo = MySimpleTimer()
        # make the 'grid' layout:
        # customize with rowSpan and colSpan
        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.datawidget, 1, 1, 1, 2)
        layout.addWidget(self.timerinfo, 2, 1, 1, 1)
        layout.addWidget(self.stopacquisition, 2, 2, 1, 1)



        self.setLayout(layout)

        # we could register the action of the push button, like so:
        self.stopacquisition.clicked.connect(self.button_close_window)

        self.RUNLOOP = True

        self.show()


    def update(self, chunk):
        self.datawidget.update(chunk)

  


    def button_close_window(self):
        self.RUNLOOP = False
        self.close()




# something to count upwards:
class MySimpleTimer(QtWidgets.QLabel):
    def __init__(self):
        super(MySimpleTimer, self).__init__()

        self.time = QTime() # we set the clock to 0; otherwise it'll copy the computer time
                                       # format = h, m, s, msec
        self.time.start() # starting up the clock!

        timer = QTimer(self)           # when 1000 msec expires; to something & refresh
        timer.timeout.connect(self.update_seconds)
        timer.start(1000)
        self.update_seconds()          #so things don't look fishy?


    def update_seconds(self):


        elapsed_seconds, _ = divmod(self.time.elapsed(), 1000)
        m, s = divmod(elapsed_seconds, 60)
        h, m = divmod(m, 60)
        to_print_str = (f'{m:02d}:{s:02d}') # Python 3.6+
        if h > 0:
            to_print_str = (f'{h:02d}:{m:02d}:{s:02d}') # Python 3.6+

        self.setText(to_print_str)




