# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import pyvisa
import math
import matplotlib.pyplot as plt
import numpy as np


class Ds1102ze:
    def __init__(self):
        self.channel = 1
        self.maxpacketsize = 250000
        self.rm = pyvisa.ResourceManager()
        # insert your device here
        # resources.list_resources() will show you the USB resource to put below
        self.oscilloscope = self.rm.open_resource('USB0::0x1AB1::0x0517::DS1ZE224612603::INSTR')

    def setchannel(self, channel):
        self.channel = channel

    def getidn(self):
        return self.oscilloscope.query("*IDN?")

    def listresources(self):
        return self.rm.list_resources()

    def setstartstop(self, start, stop):
        self.oscilloscope.write(":STOP")
        self.oscilloscope.write(":WAV:MODE RAW")
        self.oscilloscope.write(":WAV:SOUR CHAN%s" % self.channel)
        self.oscilloscope.write(":WAV:FORM BYTE")
        self.oscilloscope.write(":WAV:START %s" % start)
        self.oscilloscope.write(":WAV:STOP %s" % stop)

    def getdatapacket(self):
        self.oscilloscope.write("WAV:DATA? CHAN%s" % self.channel)
        data = self.oscilloscope.read_raw()
        return data[11:-1]

    def getdata(self, datasize=None):
        memorysize = int(self.oscilloscope.query(":ACQ:MDEP?"))
        if datasize is None:
            datasize = memorysize
        if datasize > memorysize:
            raise ValueError("Datasize bigger than memorysize")
        numberofpackets = math.ceil(datasize / self.maxpacketsize)
        datalastpacket = datasize % self.maxpacketsize
        data = b""
        for packetnumber in range(numberofpackets):
            if packetnumber==numberofpackets-1 and datalastpacket != 0:
                self.setstartstop(packetnumber * self.maxpacketsize + 1, packetnumber * self.maxpacketsize + datalastpacket)
            else:
                self.setstartstop(packetnumber * self.maxpacketsize + 1, (packetnumber + 1) * self.maxpacketsize)
            data = data + self.getdatapacket()
        return data

    def converttovoltage(self, data):
        YOR = float(self.oscilloscope.query(":WAV:YOR?"))
        YREF = float(self.oscilloscope.query(":WAV:YREF?"))
        YINC = float(self.oscilloscope.query(":WAV:YINC?"))
        voltage = []
        for point in range(len(data)):
            voltage.append((data[point]-YOR-YREF)*YINC)
        return voltage

    def plotvalues(self, voltage):
        deltatime = float(self.oscilloscope.query(":WAV:XINC?"))
        time = np.arange(0, deltatime * len(voltage), deltatime)
        plt.figure(0)
        plt.plot(time, voltage)
        plt.xlabel('t / s')
        plt.ylabel('U / V')
        plt.grid()
        plt.show()

    def plotfft(self, voltage, type="stem"):
        if type != "stem" and type != "semilog":
            raise ValueError("Type must be stem or semilog")
        halfvoltagelength = len(voltage) // 2
        voltagelength = len(voltage)
        amplitudes = np.fft.fft(voltage)/voltagelength
        amplitudes[1:] = amplitudes[1:]*2

        n = np.arange(halfvoltagelength)
        deltatime = float(self.oscilloscope.query(":WAV:XINC?"))
        T = voltagelength*deltatime
        frequencys = n/T

        plt.figure(1)
        if type=="stem":
            plt.stem(frequencys, np.abs(amplitudes[:halfvoltagelength]), 'b', markerfmt=" ", basefmt="-b")
        elif type=="semilog":
            plt.semilogy(frequencys, np.abs(amplitudes[:halfvoltagelength]), 'b')
        plt.xlabel('f / Hz')
        plt.ylabel('|A(f)|')
        plt.grid()
        plt.show()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    scope = Ds1102ze()
    print(scope.getidn())

    data = scope.getdata(1048576*8)
    voltage=scope.converttovoltage(data)
    print(len(voltage))
    print(len(data))
    print(np.average(voltage))
    scope.plotvalues(voltage)
    scope.plotfft(voltage, "semilog")
