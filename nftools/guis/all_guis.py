# breakpoint()
from pynfb.widgets import signal_viewers as sv
#from pynfb_widgets import signal_viewers as sv
from PyQt5 import QtWidgets, QtGui
# import datetime
#import sv.SignalViewer as SignalViewer
#import sv.RawSignalViewer as RawSignalViewer
#print(pynfb_widgets)
# print('hallo')
# from .sv import *
from PyQt5.QtCore import QTime, QTimer
import mne
import time
import numpy as np
from datetime import datetime



# I can change this as I want/need:
class CustomSignalViewer(sv.RawSignalViewer):
    def __init__(self, fs, names, seconds_to_plot=5, signals_to_plot=1, overlap=False, notch_filter=True, **kwargs):

        signals_to_plot = len(names)
            
        super(CustomSignalViewer, self).__init__(fs, names, seconds_to_plot=seconds_to_plot, signals_to_plot=signals_to_plot, overlap=overlap, notch_filter=notch_filter, **kwargs)
        self.indexes_to_plot = [slice(j, min(self.n_signals, j+signals_to_plot)) for j in range(0, self.n_signals, signals_to_plot)]
        self.n_signals_to_plot = signals_to_plot


        # we should add a little button -- keep on plotting it or not -- and then we can overload the update function to work or not (somehow)
        # this will liberate CPU resoruces if you want...
        self.plot_check_box = PlotButton(self) # we add the Plotbutton
        self.plot_check_box.setGeometry(18*2+100+10, 0, 100, 100)
        self.plot_check_box.setChecked(True)
        # breakpoint()


    def update(self, data):
        if self.plot_check_box.isChecked():
            if data is not None:
                super(CustomSignalViewer, self).update(data)
            else:
                QtGui.QApplication.processEvents()
        else:
            # just process events - don't do anything else. This is... pyqtgraph
            QtGui.QApplication.processEvents()
            # pass # this will effectively discard our data, as if nothing happened. So we can kind-of prevent plotting from taking place!!


        

class PlotButton(QtWidgets.QCheckBox):
    def __init__(self, parent):
        super(PlotButton, self).__init__('Plot', parent)
        self.setMaximumHeight(18)
        self.setStyleSheet("QCheckBox { background-color: #393231; color: #E5DfC5 }"
                           "QCheckBoxx:checked { background-color: #252120 }")



#class AnalysisWindow(sv.RawSignalViewer):
#    def __init__(self, fs, names, seconds_to_plot=5, overlap=True, **kwargs):
#        signals_to_plot = len(names)
#        super(AnalysisWindow, self).__init__(fs, names, seconds_to_plot=5, signals_to_plot = signals_to_plot, overlap=True, notch_filter=True, **kwargs)



# I need to sub-class directly from the (more base) SignalViewer, and fix the things properly.
class AnalyzeData(sv.SignalViewer):
    def __init__(self, sampling_freq, names, controller, **kwargs):
        self.seconds_to_plot=5
        super(AnalyzeData, self).__init__(sampling_freq, names, self.seconds_to_plot, overlap=True, signals_to_plot=None, notch_filter=False, **kwargs)
        self.controller=controller
        # figure out how the scaling is controlled... and fix that...
        # figure out... the scaling of the signal!!
        # we willl... overload the base function.
        # overload THIS:
        self.yrange = self.controller.given_st_scaling
        self.getPlotItem().setYRange(0, self.yrange)
        
        # our 'plot button' addon:
        self.plot_check_box = PlotButton(self) # we add the Plotbutton
        self.plot_check_box.setGeometry(18*2+100+10, 0, 100, 100)
        self.plot_check_box.setChecked(True)
        self.show()
        
        
    def prepare_y_data(self, chunk_len):
            # check thecurrent scaling and apply it (in a fashion) to signals 4 and 5
            # so markers are always between 0 and 1-4
        
        return self.y_raw_buffer
        
        
    def update(self, chunk):
        if self.plot_check_box.isChecked():

            if self.yrange != self.controller.st_scaling:
                self.yrange = self.controller.st_scaling
                self.getPlotItem().setYRange(0, self.yrange)

            sc=self.yrange                            
            chunk[:,3]=chunk[:,3] * sc / 5.0 # takes care of the visual markers (always should be 1 or 0)
            chunk[:,4]=chunk[:,4] * sc / 5.0 / 3.0 #+ 1.0 # * 2.0 * sc / 5.0 

   
                
            
            # check thecurrent scaling and apply it (in a fashion) to signals 4 and 5
            # so markers are always between 0 and 1-4
            # if chunk[:,3]
            
            super(AnalyzeData, self).update(chunk)
            
            
        else:
            QtGui.QApplication.processEvents()




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
        # self.close() # I found that NOT closing the window is actually better...




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





class NFChangeThresholds(QtWidgets.QWidget):
    def __init__(self, *args):
        super(NFChangeThresholds, self).__init__()
        

        self.threshold_names_objects = args

        self.begin_time = time.time()  # so, let's store our begin time, so as to make events later on.
        # these are GUI events; they should contain a timestamp and a code, much like our 
        # stimulus annotations. BUT -- they should be coded into our EEG as events.
        # what was the list again of our stimulus events?
        self.GUI_Annotations = mne.Annotations(0, 0, 'start the GUI', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')) #, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))



        self.obs={}
        self.items=[]
        
        combined_layouts = QtWidgets.QVBoxLayout()
        for i, item in enumerate(self.threshold_names_objects):
            self.items.append(item)
            layout_combined=self.make_controls(item, i)            
            combined_layouts.addLayout(layout_combined)

        self.setLayout(combined_layouts)

        # make also the datetime, for when this GUI was initiated! - this will be the orig time of these annotations...
        # self.created_datetime = datetime.now()
        # self.GUI_Annotations.orig_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # we have to initialize like this.        
        
        # for item
        # put this into a little list that we put into 'self', and reference to it repeatedly (so we don't lose the references to them?)

        # make, for each of the threshold items, 2 (!!) QDoubleSpinBoxes -- one for threshold, another for duration
        # and... put those in a horizontal layout.
        # combined_layouts = QtWidgets.QVBoxLayout()
      
        self.show()



    def make_controls(self, controller, i):
        

        
        
        # self.obs[i]={}
        thr_object = controller
        thr_name = controller.feedback_type

        # set the label:
        label_thr = QtWidgets.QLabel()
        label_thr.setText(thr_name.upper() + ' ' + 'Threshold')
        # self.obs[i]['label_thr']=label_thr
        
        # set the cycling/stuff here
        spinbox_thr = QtWidgets.QDoubleSpinBox()
        initial_value = thr_object.thr        # grab the value from thr_object:
        increment_value = initial_value / 20. # set to 5 % of value..
        spinbox_thr.setValue(initial_value)
        spinbox_thr.setSingleStep(increment_value)
        # self.obs[i]['spinbox_thr']=spinbox_thr
        
        # write: Increment
        label_incr = QtWidgets.QLabel()
        label_incr.setText('Increment')
        # self.obs[i]['label_incr']=label_incr

        # write down the increment in an editable txt box
        lineedit_incr = QtWidgets.QLineEdit()
        # breakpoint()
        lineedit_incr.setText('%.2g' % increment_value)
        # self.obs[i]['lineedit_incr']=lineedit_incr

        # set the label:
        label_thrdur = QtWidgets.QLabel()
        label_thrdur.setText('Duration')
        # self.obs[i]['label_thrdur']=label_thrdur
        
        # set the cycling/stuff here
        spinbox_thrdur = QtWidgets.QDoubleSpinBox()
        initial_valuedur = thr_object.dur        # grab the value from thr_object:
        increment_valuedur = initial_valuedur / 20. # set to 5 % of value..
        spinbox_thrdur.setValue(initial_valuedur)
        spinbox_thrdur.setSingleStep(increment_valuedur)
        # self.obs[i]['spinbox_thrdur']=spinbox_thrdur
        
        # write: Increment
        label_incrdur = QtWidgets.QLabel()
        label_incrdur.setText('Increment')
        # self.obs[i]['label_incrdur']=label_incrdur
        

        # write down the increment in an editable txt box
        lineedit_incrdur = QtWidgets.QLineEdit()
        lineedit_incrdur.setText('%.2g' % increment_valuedur)
        # self.obs[i]['lineedit_incrdur']=lineedit_incrdur


        # fix the Layout:
        layout_line1 = QtWidgets.QHBoxLayout()

        layout_line1.addWidget(label_thr)
        layout_line1.addWidget(spinbox_thr)
        layout_line1.addWidget(label_incr)
        layout_line1.addWidget(lineedit_incr)
        # breakpoint()
        layout_line1.addStretch()
        layout_line1.addWidget(label_thrdur)
        layout_line1.addWidget(spinbox_thrdur)
        layout_line1.addWidget(label_incrdur)
        layout_line1.addWidget(lineedit_incrdur)




        # Control Feedback parameters on-the-fly:
        label_fbrange = QtWidgets.QLabel()
        label_fbrange.setText('FB Range')
        # self.obs[i]['label_fbrange']=label_fbrange
        

        lineedit_fbrange = QtWidgets.QLineEdit()
        lineedit_fbrange.setText('%.2g' % controller.given_st_scaling)
        # self.obs[i]['lineedit_fbrange']=lineedit_fbrange

        label_fbedges = QtWidgets.QLabel()
        label_fbedges.setText('FB Margins (L/U)')
        # self.obs[i]['label_fbedges']=label_fbedges

        lineedit_upperedge = QtWidgets.QLineEdit()
        lineedit_upperedge.setText('%.2g' % controller._st_lower_offset)
        # self.obs[i]['lineedit_upperedge']=lineedit_upperedge

        lineedit_loweredge = QtWidgets.QLineEdit()
        lineedit_loweredge.setText('%.2g' % controller._st_upper_offset)
        # self.obs[i]['lineedit_loweredge']=lineedit_loweredge


        layout_line2 = QtWidgets.QHBoxLayout()
        layout_line2.addStretch()
        layout_line2.addWidget(label_fbrange)
        layout_line2.addWidget(lineedit_fbrange)
        layout_line2.addWidget(label_fbedges)
        layout_line2.addWidget(lineedit_loweredge)
        layout_line2.addWidget(lineedit_upperedge)
        layout_line2.addStretch()

        layout_combined = QtWidgets.QVBoxLayout()
        layout_combined.addLayout(layout_line1)
        layout_combined.addLayout(layout_line2)


        # the actions of all of the buttons.. or ""Signals"":
        # spinbox has arrows and just changing the text?
        my_validator = QtGui.QDoubleValidator()
        
        
        oldvalues={}
        
        # print('hallo')
        # actually change the threshold (spinbox)
        # it should use the approproate function of the 'item' and send a marker
        # spinbox_thr.valueChanged.connect(lambda: print('value changed!'))
        # spinbox_thr.valueChanged.connect(lambda: breakpoint())
        spinbox_thr.valueChanged.connect(lambda: controller.set_threshold(spinbox_thr.value()))
        spinbox_thr.valueChanged.connect(lambda: self.GUI_Annotations.append(time.time()-self.begin_time, 0, controller.feedback_type + '_thr ' + '%.3g' % spinbox_thr.value()) if oldvalues['spinbox_thr'] != spinbox_thr.value() else None)
        # breakpoint()
        self.GUI_Annotations.append(time.time()-self.begin_time, 0, 'start ' + controller.feedback_type + '_thr ' + '%.3g' % spinbox_thr.value())
        oldvalues['spinbox_thr'] = spinbox_thr.value()

        # the callback should use the appropriate function, + change the increment of the spinbox
        # when this is called, no markers/signals. Only when thing REALLY change.
        # lineedit_incr.setValidator(my_validator)
        # lineedit_incr.editingFinished.connect(lambda: print('editing done!'))
        lineedit_incr.editingFinished.connect(lambda: spinbox_thr.setSingleStep(float(lineedit_incr.text())))

        # actually change the threshold (spinbox)
        # it should use the approproate function of the 'item' and send a marker
        spinbox_thrdur.valueChanged.connect(lambda: controller.set_new_duration(spinbox_thrdur.value()))
        spinbox_thrdur.valueChanged.connect(lambda: self.GUI_Annotations.append(time.time()-self.begin_time, 0, controller.feedback_type + '_dur ' + '%.3g' % spinbox_thrdur.value()) if oldvalues['spinbox_thrdur'] != spinbox_thrdur.value() else None)
        self.GUI_Annotations.append(time.time()-self.begin_time, 0, 'start ' + controller.feedback_type + '_dur ' + '%.3g' % spinbox_thrdur.value())
        oldvalues['spinbox_thrdur'] = spinbox_thrdur.value()


        # the callback should use the appropriate function, + change the increment of the spinbox
        lineedit_incrdur.setValidator(my_validator)
        lineedit_incrdur.editingFinished.connect(lambda: spinbox_thrdur.setSingleStep(float(lineedit_incrdur.text())))


        # it should use the apppropriate function of the item
        lineedit_fbrange.setValidator(my_validator)
        lineedit_fbrange.editingFinished.connect(lambda: controller.set_ststim_scaling(float(lineedit_fbrange.text())))
        lineedit_fbrange.editingFinished.connect(lambda: self.GUI_Annotations.append(time.time()-self.begin_time, 0, controller.feedback_type + '_range ' + '%.3g' % float(lineedit_fbrange.text())) if oldvalues['lineedit_fbrange'] != lineedit_fbrange.text() else None)
        self.GUI_Annotations.append(time.time()-self.begin_time, 0, 'start ' + controller.feedback_type + '_range ' + '%.3g' % float(lineedit_fbrange.text()))
        oldvalues['lineedit_fbrange'] = lineedit_fbrange.text()

        # it should use the apppropriate function of the item
        lineedit_loweredge.setValidator(my_validator)
        lineedit_loweredge.editingFinished.connect(lambda: controller.set_stposition_loweroffset(float(lineedit_loweredge.text())))
        lineedit_loweredge.editingFinished.connect(lambda: self.GUI_Annotations.append(time.time()-self.begin_time, 0, controller.feedback_type + '_ledge ' + '%.3g' % float(lineedit_loweredge.text())) if oldvalues['lineedit_loweredge'] != lineedit_loweredge.text() else None)
        self.GUI_Annotations.append(time.time()-self.begin_time, 0, 'start ' + controller.feedback_type + '_lmargin ' + '%.3g' % float(lineedit_loweredge.text()))
        oldvalues['lineedit_loweredge'] = lineedit_loweredge.text()


        # it should use the apppropriate function of the item
        lineedit_upperedge.setValidator(my_validator)
        lineedit_upperedge.editingFinished.connect(lambda: controller.set_stposition_upperoffset(float(lineedit_upperedge.text())))
        lineedit_upperedge.editingFinished.connect(lambda: self.GUI_Annotations.append(time.time()-self.begin_time, 0, controller.feedback_type + '_ledge ' + '%.3g' % float(lineedit_upperedge.text())) if oldvalues['lineedit_upperedge'] != lineedit_upperedge.text() else None)
        self.GUI_Annotations.append(time.time()-self.begin_time, 0, 'start ' + controller.feedback_type + '_umargin ' + '%.3g' % float(lineedit_upperedge.text()))
        oldvalues['lineedit_upperedge'] = lineedit_upperedge.text()
 
        return layout_combined



#class MonitorRTSignal(QtWidgets.QWidget):
#    super(MonitorRTSignal, self).__init__()

    # so this should have the following 'signals', just like RawSignalViewer, Or perhaps I shoul take a closer look at pyqtgraph.
    # - The NF; without Amplitude Detection (but ... Spatially Filtered
    # - The Amplitude Signal
    # - The Markers - for Audio
    # - The Markers - for Visual
    # - The Threshold; as it currently stands
    # The Update function should just contain all of these as separate signals;
    # sig; fsig; markers = [] (some collection of markers; Boolean for each time point); thr.
    # I could indeed add a pushbutton (or checkbox) to control for whether things should update or now; once for each of the graph
    # ical elements. That should facilitate slow computers and save CPU - but still allow user to check things if they wish it.

    # a separate widget should likely have some push buttons to manipulate various aspects of the threshold or other variables

    # Then we should have again another separate widget that likely has different types of Qt elements in it; with again
    # a little clock thingy; as well as the button to 'stop' things.


# I need a new RawSignalViewer, with the following 'Channels': SpatialFilteredEEG; Evelope; Threshold; markers (visual); markers (audotory) + Which One; graded across several levels; Duration (not shown).


