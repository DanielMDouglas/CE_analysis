import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt

headerKeys = ["ID", "chipType", "channel", "socket",
              "conf", "testPulse", "baseline", "gain",
              "peakingTime", "outputCoupling", "outputBuffer",
              "otherConf", "globalConf", "DAC"]

class waveform:
    def __init__(self, header, data):
        self.header = header
        
        self.samples = data

        self.ticks = np.arange(len(data))

        self.calc_baseline(int(0.75*len(data)))
        
    def calc_baseline(self, sidebandStart):
        self.baseline = np.mean(self.samples[self.ticks > sidebandStart])

    def plot(self, ax = plt, **kwargs):
        ax.scatter(self.ticks, self.samples, **kwargs)
        
    def fit_model(self, model, x0, ax = plt, **plotkwargs):
        def chi2(args):
            return sum((model(xi, *args) - yi)**2 for xi, yi in zip(self.ticks, self.samples))

        bfargs = opt.fmin_l_bfgs_b(chi2, x0, approx_grad = True)[0]
        print bfargs

        ax.plot(self.ticks, model(self.ticks, *bfargs), **plotkwargs)

        return bfargs
        
class waveformCollection:
    def __init__(self, waveformList):
        # initialize from a list of waveform objects

        self.waveforms = waveformList
        self.size = len(waveformList)
        
        self.uniques = {key: np.unique([wf.header[key] for wf in self.waveforms])
                        for key in headerKeys}

    def __getitem__(self, selectionHeader):
        # takes the header and returns a subset of waveforms
        # whose headers match the supplied header fields

        subSet = []

        for wf in self.waveforms:
            if all(wf.header[key] == value
                   for key, value in selectionHeader.items()):
                subSet.append(wf)

        return waveformCollection(subSet)

    def __iter__(self):
        # iterating through the collection should just
        # iterate through the individual waveforms

        for wf in self.waveforms:
            yield wf

    def byHeaderCol(self, key):
        # given a key in headerKeys, iterate through all
        # values of that key in this collection
        # and yield (value, waveformCollection) pairs 
        
        for value in self.uniques[key]:
            selectionHeader = {key: value}
            yield value, self[selectionHeader]
        

def load_file(inFileName,
              headerSize = 8,
              bufferSize = 2000):
    # returns a waveformCollection object from a file
    headerStrings = np.loadtxt(inFileName,
                               usecols = range(headerSize),
                               dtype = str)
    
    # lookup tables for interpreting the configuration byte
    testPulseValue = {0: "OFF",
                      1: "ON"}
    baselineValue = {0: "900 mV",
                     1: "200 mV"}
    gainValue = {0: "4.7 mV/fC",
                 2: "7.8 mV/fC",
                 1: "14 mV/fC",
                 3: "25 mV/fC"}
    peakingTimeValue = {2: "0.5 usec",
                        0: "1 usec",
                        3: "2 usec",
                        1: "3 usec"}
    outputCouplingValue = {0: "DC",
                           1: "AC"}
    outputBufferValue = {0: "OFF",
                         1: "ON"}

    headers = [{"ID": headerString[0],
                "chipType": headerString[1],
                "channel": int(headerString[2]),
                "socket": int(headerString[3]),
                "conf": headerString[4],
                "testPulse": testPulseValue[(int(headerString[4], 16) & 128) >> 7],
                "baseline": baselineValue[(int(headerString[4], 16) & 64) >> 6],
                "gain": gainValue[(int(headerString[4], 16) & 48) >> 4],
                "peakingTime": peakingTimeValue[(int(headerString[4], 16) & 12) >> 2],
                "outputCoupling": outputCouplingValue[(int(headerString[4], 16) & 2) >> 1],
                "outputBuffer": outputBufferValue[int(headerString[4], 16) & 1],
                "otherConf": headerString[5],
                "globalConf": headerString[6],
                "DAC": headerString[7]}
               for headerString in headerStrings]
    
    data = np.loadtxt(inFileName,
                      usecols = range(headerSize, headerSize + bufferSize))

    return waveformCollection([waveform(thisHeader, dat) for thisHeader, dat in zip(headers, data)])
