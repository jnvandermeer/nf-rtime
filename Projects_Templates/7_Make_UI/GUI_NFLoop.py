# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'NFLoop.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(500, 353)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.TimeRunning = QtWidgets.QLabel(self.centralwidget)
        self.TimeRunning.setGeometry(QtCore.QRect(70, 30, 111, 16))
        self.TimeRunning.setObjectName("TimeRunning")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(140, 90, 59, 15))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(9, 121, 91, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(10, 240, 101, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(10, 282, 91, 16))
        self.label_4.setObjectName("label_4")
        self.EEGThr = QtWidgets.QLineEdit(self.centralwidget)
        self.EEGThr.setGeometry(QtCore.QRect(110, 120, 91, 23))
        self.EEGThr.setObjectName("EEGThr")
        self.EMGThr = QtWidgets.QLineEdit(self.centralwidget)
        self.EMGThr.setGeometry(QtCore.QRect(230, 120, 91, 23))
        self.EMGThr.setObjectName("EMGThr")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(260, 90, 59, 15))
        self.label_5.setObjectName("label_5")
        self.EEGStScaling = QtWidgets.QLineEdit(self.centralwidget)
        self.EEGStScaling.setGeometry(QtCore.QRect(120, 240, 71, 23))
        self.EEGStScaling.setObjectName("EEGStScaling")
        self.EEGstLOffset = QtWidgets.QLineEdit(self.centralwidget)
        self.EEGstLOffset.setGeometry(QtCore.QRect(120, 280, 31, 23))
        self.EEGstLOffset.setObjectName("EEGstLOffset")
        self.EEGUOffset = QtWidgets.QLineEdit(self.centralwidget)
        self.EEGUOffset.setGeometry(QtCore.QRect(160, 280, 31, 23))
        self.EEGUOffset.setObjectName("EEGUOffset")
        self.EMGStScaling = QtWidgets.QLineEdit(self.centralwidget)
        self.EMGStScaling.setGeometry(QtCore.QRect(240, 240, 71, 23))
        self.EMGStScaling.setObjectName("EMGStScaling")
        self.EMGUOffset = QtWidgets.QLineEdit(self.centralwidget)
        self.EMGUOffset.setGeometry(QtCore.QRect(280, 280, 31, 23))
        self.EMGUOffset.setObjectName("EMGUOffset")
        self.EMGLOffset = QtWidgets.QLineEdit(self.centralwidget)
        self.EMGLOffset.setGeometry(QtCore.QRect(240, 280, 31, 23))
        self.EMGLOffset.setObjectName("EMGLOffset")
        self.EEGThrIncrement = QtWidgets.QLineEdit(self.centralwidget)
        self.EEGThrIncrement.setGeometry(QtCore.QRect(140, 150, 31, 23))
        self.EEGThrIncrement.setObjectName("EEGThrIncrement")
        self.EMGThrIncrement = QtWidgets.QLineEdit(self.centralwidget)
        self.EMGThrIncrement.setGeometry(QtCore.QRect(260, 150, 31, 23))
        self.EMGThrIncrement.setObjectName("EMGThrIncrement")
        self.EEGIncrementDown = QtWidgets.QPushButton(self.centralwidget)
        self.EEGIncrementDown.setGeometry(QtCore.QRect(110, 150, 21, 23))
        self.EEGIncrementDown.setObjectName("EEGIncrementDown")
        self.EEGIncrementUp = QtWidgets.QPushButton(self.centralwidget)
        self.EEGIncrementUp.setGeometry(QtCore.QRect(180, 150, 21, 23))
        self.EEGIncrementUp.setObjectName("EEGIncrementUp")
        self.EMGIncrementDown = QtWidgets.QPushButton(self.centralwidget)
        self.EMGIncrementDown.setGeometry(QtCore.QRect(230, 150, 21, 23))
        self.EMGIncrementDown.setObjectName("EMGIncrementDown")
        self.EMGIncrementUp = QtWidgets.QPushButton(self.centralwidget)
        self.EMGIncrementUp.setGeometry(QtCore.QRect(300, 150, 21, 23))
        self.EMGIncrementUp.setObjectName("EMGIncrementUp")
        self.StopLoop = QtWidgets.QPushButton(self.centralwidget)
        self.StopLoop.setGeometry(QtCore.QRect(380, 28, 91, 23))
        self.StopLoop.setObjectName("StopLoop")
        self.StartCamera = QtWidgets.QPushButton(self.centralwidget)
        self.StartCamera.setGeometry(QtCore.QRect(380, 100, 91, 23))
        self.StartCamera.setObjectName("StartCamera")
        self.StopCamera = QtWidgets.QPushButton(self.centralwidget)
        self.StopCamera.setGeometry(QtCore.QRect(380, 130, 91, 23))
        self.StopCamera.setObjectName("StopCamera")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(380, 70, 101, 20))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(10, 210, 351, 20))
        self.label_7.setObjectName("label_7")
        self.ShowSignals = QtWidgets.QPushButton(self.centralwidget)
        self.ShowSignals.setGeometry(QtCore.QRect(380, 180, 91, 23))
        self.ShowSignals.setObjectName("ShowSignals")
        self.HideSignals = QtWidgets.QPushButton(self.centralwidget)
        self.HideSignals.setGeometry(QtCore.QRect(380, 210, 91, 23))
        self.HideSignals.setObjectName("HideSignals")
        self.Time = QtWidgets.QLabel(self.centralwidget)
        self.Time.setGeometry(QtCore.QRect(170, 31, 59, 15))
        self.Time.setObjectName("Time")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 20))
        self.menubar.setObjectName("menubar")
        self.menuNeurofeedback_Loops_Options = QtWidgets.QMenu(self.menubar)
        self.menuNeurofeedback_Loops_Options.setObjectName("menuNeurofeedback_Loops_Options")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.menuNeurofeedback_Loops_Options.addSeparator()
        self.menuNeurofeedback_Loops_Options.addAction(self.actionSave)
        self.menubar.addAction(self.menuNeurofeedback_Loops_Options.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.TimeRunning.setText(_translate("MainWindow", "Loop Running:"))
        self.label.setText(_translate("MainWindow", "EEG"))
        self.label_2.setText(_translate("MainWindow", "Threshold (uV)"))
        self.label_3.setText(_translate("MainWindow", "St Scaling (uV)"))
        self.label_4.setText(_translate("MainWindow", "St Offsets (%)"))
        self.label_5.setText(_translate("MainWindow", "EMG"))
        self.EEGIncrementDown.setText(_translate("MainWindow", "PushButton"))
        self.EEGIncrementUp.setText(_translate("MainWindow", "PushButton"))
        self.EMGIncrementDown.setText(_translate("MainWindow", "PushButton"))
        self.EMGIncrementUp.setText(_translate("MainWindow", "PushButton"))
        self.StopLoop.setText(_translate("MainWindow", "Stop Loop"))
        self.StartCamera.setText(_translate("MainWindow", "Start Camera"))
        self.StopCamera.setText(_translate("MainWindow", "Stop Camera"))
        self.label_6.setText(_translate("MainWindow", "Control Options"))
        self.label_7.setText(_translate("MainWindow", "Scaling/Offset Options for Display on Stimulus Computer"))
        self.ShowSignals.setText(_translate("MainWindow", "Show Signals"))
        self.HideSignals.setText(_translate("MainWindow", "Hide Signals"))
        self.Time.setText(_translate("MainWindow", "00:00"))
        self.menuNeurofeedback_Loops_Options.setTitle(_translate("MainWindow", "Neurofeedback Loops Options"))
        self.actionSave.setText(_translate("MainWindow", "Save"))

