# breakpoint()
from pynfb.widgets import signal_viewers as sv
#from pynfb_widgets import signal_viewers as sv
from PyQt5 import QtWidgets

#import sv.SignalViewer as SignalViewer
#import sv.RawSignalViewer as RawSignalViewer
#print(pynfb_widgets)
# print('hallo')
# from .sv import *



# I can change this as I want/need:
class CustomSignalViewer(sv.RawSignalViewer):
    def __init__(self, fs, names, seconds_to_plot=5, overlap=False, **kwargs):
        super(CustomSignalViewer, self).__init__(fs, names, seconds_to_plot=5, overlap=False, **kwargs)





# most basic example of visualization; but then that we can have the pushbutton/RUNLOOP
# command to stop the loop as we require.
class AcquireData(QtWidgets.QWidget):

    # init our modest window
    def __init__(self, fs, names, **kwargs):
        super(AcquireData, self).__init__()
        self.datawidget = CustomSignalViewer(fs, names, **kwargs)
        
        self.stopacquisition = QtWidgets.QPushButton('Stop Acquisition')

        # make the 'grid' layout:
        # customize with rowSpan and colSpan
        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.datawidget, 1, 1)
        layout.addWidget(self.stopacquisition, 2, 1)


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
