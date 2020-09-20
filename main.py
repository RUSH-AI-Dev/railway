from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread
from PyQt5 import QtCore, QtGui
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from scipy import signal

import serial
import serial.tools.list_ports
import pyaudio

import pandas as pd
import numpy as np

import time

import scipy


FORMAT = pyaudio.paInt16                # We use 16bit format per sample
CHANNELS = 1
RATE = 44100
CHUNK = 1024                            # 1024bytes of data red from a buffer
RECORD_SECONDS = 1

class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageSent = QtCore.pyqtSignal(str)

    def __init__(self, Project):
        super(Worker, self).__init__()
        self._isRunning = False
        self.project = Project

    def task(self):
        self._isRunning = True

    def stop(self):
        self._isRunning = False

class railway(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("./ui.ui", self)

        # ปุ่มสั่งงาน
        self.refresh.clicked.connect(self.scan)
        self.connect.clicked.connect(self.uart_connect)
        self.close.clicked.connect(self.uart_unconnect)

        self.b_xlsx.clicked.connect(self.save_xlsx)
        self.b_csv.clicked.connect(self.save_csv)
        self.b_txt.clicked.connect(self.save_txt)

        self.load_file.clicked.connect(self.load)
        self.analysis_2.clicked.connect(self.analysis_)
        self.pushButton.clicked.connect(self.analysis_spec)
        self.pushButton_2.clicked.connect(self.analysis_spec_2)

        self.capture_Button.clicked.connect(self.get)

        # ตัวแปรควมคุม
        self.if_uart = 0
        self.if_load = 0

        # ตัวแปรคำนวน
        self.samplerate = RATE

    def scan(self):
        self.if_uart = 1
        self.port_combobox.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combobox.addItem(p.device)

    def uart_connect(self):
        if self.if_uart != 0:
            # self.ser = serial.Serial(self.port_combobox.currentText(), 115200, timeout=10)
            self.audio = pyaudio.PyAudio()
            # start Recording
            self.stream = self.audio.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK)
        self.connect.setText('Connected')

    def uart_unconnect(self):
        if self.if_uart != 0:
            print("off")
            # self.ser.close()
        self.connect.setText('Connect')

    def get(self):
        if self.if_uart != 0:
            # self.ser.reset_input_buffer()
            timeout = time.time() + 10
            while True:
                if time.time() > timeout:
                    print(time.time())
                    self.capture_Button.setText('Time is up ... (Click this button to start again)')
                    break
                # self.ser.flush()
                # self.data = self.ser.readline().decode("ascii").replace("\x00", "")[:-1].split('|')

                self.data = np.fromstring(self.stream.read(CHUNK),dtype=np.int16)
                print(self.data.shape)
                self.data = list((np.int_(self.data)*3.3)/4096.0)

                if max(self.data) >= 1:
                    if len(self.data) >= CHUNK:
                        self.capture_Button.setText('Success ... (Click this button to restart)')
                        self.data_raw.insertItem(0, str(self.data))

                        ## plot ##
                        duration = len(self.data)/self.samplerate
                        self.time = np.arange(0, duration, 1/self.samplerate)
                        self.widget.canvas.axes.clear()
                        self.widget.canvas.axes.plot(self.time, self.data)
                        self.widget.canvas.axes.set_title("The graph shows the relationship between voltage and time.", fontname = 'Tahoma')
                        self.widget.canvas.axes.set_xlabel("time (s)", fontname = 'Tahoma')
                        self.widget.canvas.axes.set_ylabel("Ampiltude (V)", fontname = 'Tahoma')
                        self.widget.canvas.axes.legend(['AE Sensor'])
                        self.widget.canvas.draw()
                        ##########

                        n = len(self.data)
                        T = 1/self.samplerate
                        yf = scipy.fft(self.data)
                        xf = np.linspace(0.0, int(1.0/(2.0*T)), int(n/2))

                        self.widget_4.canvas.axes.clear()
                        self.widget_4.canvas.axes.plot(xf, 20 * np.log(2.0/n * np.abs(yf[:n//2])))
                        self.widget_4.canvas.axes.set_title("The graph shows the relationship between Decibel and frequency.", fontname = 'Tahoma')
                        self.widget_4.canvas.axes.set_ylabel("Magnitude (dB)", fontname = 'Tahoma')
                        self.widget_4.canvas.axes.set_xlabel("frequency (Hz)", fontname = 'Tahoma')
                        self.widget_4.canvas.axes.legend(['AE Sensor FFT'])
                        self.widget_4.canvas.draw()

                        f, t, Sxx = signal.spectrogram(np.asarray(self.data), self.samplerate)
                        plt.figure(figsize=(6.5,2.5))
                        plt.pcolormesh(t, f, Sxx, shading='gouraud')
                        plt.ylabel('Frequency [Hz]')
                        plt.xlabel('Time [sec]')
                        plt.savefig('spec_cap.png')
                        self.spec_2.setPixmap(QtGui.QPixmap('spec_cap.png'))

                        break

                    if len(self.data) != CHUNK:
                        self.capture_Button.setText('test again ... (Click this button to restart)')
                        break

    def load(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Python Files (*.py)", options=options)
        if self.fileName.split('/')[-1].split('.')[-1] == 'csv':
            self.data_load = pd.read_csv(self.fileName)
        if self.fileName.split('/')[-1].split('.')[-1] == 'txt':
            self.data_load = pd.read_csv(self.fileName)
        if self.fileName.split('/')[-1].split('.')[-1] == 'xlsx':
            self.data_load = pd.read_excel(self.fileName)

        self.load_name.setText('Latest file : ' + self.fileName)
        self.if_load = 1

    def analysis_(self):
        if self.if_load != 0:
            n = len(self.data_load['Voltage'])
            T = 1/self.samplerate
            yf = scipy.fft(self.data_load['Voltage'])
            xf = np.linspace(0.0, int(1.0/(2.0*T)), int(n/2))

            self.widget_2.canvas.axes.clear()
            self.widget_2.canvas.axes.plot(self.data_load['Time'] ,self.data_load['Voltage'])
            self.widget_2.canvas.axes.set_title("The graph shows the relationship between voltage and time.", fontname = 'Tahoma')
            self.widget_2.canvas.axes.set_ylabel("Ampiltude (V)", fontname = 'Tahoma')
            self.widget_2.canvas.axes.set_xlabel("time (s)", fontname = 'Tahoma')
            self.widget_2.canvas.axes.legend(['AE Sensor'])
            self.widget_2.canvas.draw()

            self.widget_3.canvas.axes.clear()
            self.widget_3.canvas.axes.plot(xf, 20 * np.log(2.0/n * np.abs(yf[:n//2])))
            self.widget_3.canvas.axes.set_title("The graph shows the relationship between Decibel and frequency.", fontname = 'Tahoma')
            self.widget_3.canvas.axes.set_ylabel("Magnitude (dB)", fontname = 'Tahoma')
            self.widget_3.canvas.axes.set_xlabel("frequency (Hz)", fontname = 'Tahoma')
            self.widget_3.canvas.axes.legend(['AE Sensor FFT'])
            self.widget_3.canvas.draw()

            self.buff = []
            for i in self.data_load['Voltage']:
                self.buff.append(i)

            self.spec.setPixmap(QtGui.QPixmap('spec.png'))

    def analysis_spec(self):
        f, t, Sxx = signal.spectrogram(np.asarray(self.data), self.samplerate)
        plt.figure(figsize=(6.5,2.5))
        plt.pcolormesh(t, f, Sxx, shading='gouraud')
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.show()

    def analysis_spec_2(self):
        f, t, Sxx = signal.spectrogram(np.asarray(self.data), self.samplerate)
        plt.figure(figsize=(6.5,2.5))
        plt.pcolormesh(t, f, Sxx, shading='gouraud')
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.show()


    def save_xlsx(self):
        if self.if_uart != 0:
            t = time.ctime().split(':')
            t_ = t[0] + '_' + t[1] + '_' + t[2] + '.xlsx'
            df = pd.DataFrame(list(zip(self.time, self.data)), columns=['Time', 'Voltage'])
            df.to_excel('dataset/' + t_)

            self.save_name.setText('Latest file : ' + t_)

    def save_csv(self):
        if self.if_uart != 0:
            t = time.ctime().split(':')
            t_ = t[0] + '_' + t[1] + '_' + t[2] + '.csv'
            df = pd.DataFrame(list(zip(self.time, self.data)), columns=['Time', 'Voltage'])
            df.to_csv('dataset/' + t_)

            self.save_name.setText('Latest file : ' + t_)

    def save_txt(self):
        if self.if_uart != 0:
            t = time.ctime().split(':')
            t_ = t[0] + '_' + t[1] + '_' + t[2] + '.txt'
            df = pd.DataFrame(list(zip(self.time, self.data)), columns=['Time', 'Voltage'])
            df.to_csv('dataset/' + t_)

            self.save_name.setText('Latest file : ' + t_)


app = QApplication([])
windows = railway()
windows.show()
app.exec_()

