from coldAna import *

# lookup tables for interpreting the configuration byte
lookup = {"testPulseValue":      {0: False,
                                  1: True},
          "baselineValue":       {0: "900 mV",
                                  1: "200 mV"},
          "gainValue":           {0: "4.7 mV/fC",
                                  2: "7.8 mV/fC",
                                  1: "14 mV/fC",
                                  3: "25 mV/fC"},
          "peakingTimeValue":    {2: "0.5 usec",
                                  0: "1 usec",
                                  3: "2 usec",
                                  1: "3 usec"},
          "outputCouplingValue": {0: "DC",
                                  1: "AC"},
          "outputBufferValue":   {0: False,
                                  1: True}}

class dataFile:
    def __init__(self, fileName, headerSize = 13):
        self.fileName = fileName
        self.headerSize = headerSize

    def load(self):
        "returns a waveformCollection object from a file"
        headerStrings = np.loadtxt(self.fileName,
                                   usecols = range(self.headerSize),
                                   dtype = str)
        
        headers = [{"ID": headerString[0],
                    "chipType": headerString[1],
                    "socket": int(headerString[2]),
                    "channel": int(headerString[3]),
                    "conf": headerString[4],
                    "testPulse": lookup["testPulseValue"][(int(headerString[4], 16) & 128) >> 7],
                    "baseline": lookup["baselineValue"][(int(headerString[4], 16) & 64) >> 6],
                    "gain": lookup["gainValue"][(int(headerString[4], 16) & 48) >> 4],
                    "peakingTime": lookup["peakingTimeValue"][(int(headerString[4], 16) & 12) >> 2],
                    "outputCoupling": lookup["outputCouplingValue"][(int(headerString[4], 16) & 2) >> 1],
                    "outputBuffer": lookup["outputBufferValue"][int(headerString[4], 16) & 1],
                    "otherConf": headerString[5],
                    "globalConf": headerString[6],
                    "DACconf": headerString[7],
                    "DACnum": headerString[8],
                    "ExtPulserMag": float(headerString[9]),
                    "ExtPulserRise": headerString[10],
                    "temp": headerString[11],
                    "N": int(headerString[12])}
                   for headerString in headerStrings]
    
        data = np.loadtxt(self.fileName,
                          usecols = range(self.headerSize, self.headerSize + headers[0]['N']))
        
        return waveformCollection([waveform(thisHeader, dat) for thisHeader, dat in zip(headers, data)])


# this is set up for my machine specifically
# you will probably have to adjust the dataDir
# path to your specific directory

dataDir = "../data/"

V7_cold_ledge = [dataFile(dataDir + "V7/2019-07-31-batch0.dat"),
                 dataFile(dataDir + "V7/2019-08-27-batch1.dat"),
                 dataFile(dataDir + "V7/2019-08-27-batch2.dat"),
                 dataFile(dataDir + "V7/2019-08-27-batch3.dat"),
                 dataFile(dataDir + "V7/2019-08-28-batch4.dat"),
                 dataFile(dataDir + "V7/2019-08-28-batch5.dat"),
                 dataFile(dataDir + "V7/2019-08-28-batch6.dat"),
                 dataFile(dataDir + "V7/2019-08-28-batch7.dat"),
                 dataFile(dataDir + "V7/2019-08-28-batch8.dat")]

V4_cold_500mV = dataFile(dataDir + "V4-cold-500mV.dat")
