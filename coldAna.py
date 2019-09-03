import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt

headerKeys = ["ID",              # unique string for each chip
              "chipType",        # v4, v7, v8, etc.
              "socket",          # int, which socket is this chip in?
              "channel",         # int, which channel is this waveform from?
              "conf",            # configuration bit (encoded as 2-digit hex)
              "testPulse",       # from conf, bool, is pulser on?
              "baseline",        # from conf, str, nominal baseline
              "gain",            # from conf, str, nominal gain
              "peakingTime",     # from conf, str, nominal peaking time
              "outputCoupling",  # from conf, str, ???
              "outputBuffer",    # from conf, str, ???
              "otherConf",       # config bit for all other channels
              "globalConf",      # global control bits
              "DACconf",         # internal DAC control bits
              "DACnum",          # internal DAC numerical setting
              "ExtPulserMag",    # external pulser amplitude in volts
              "ExtPulserRise",   # external pulser rise time in microseconds
              "temp",            # temperature (77 for LN2, 300 for RT)
              "N",               # int, number of sample in waveform
]

class waveform:
    def __init__(self, header, data):
        """
        Initialize a waveform object
        from a header (dict of header fields and their values)
        and data (iterable containing ADC measurements)
        """
        self.header = header
        
        self.samples = data

        self.ticks = np.arange(len(data))

        # assumes that sideband ends 5% of the way into the waveform
        self.calc_baseline(int(0.05*len(data)))
        
    def calc_baseline(self, sidebandEnd):
        "Calculate baseline by a simple mean in a region outside of the main pulse"
        self.baseline = np.mean(self.samples[self.ticks < sidebandEnd])

    def scatter(self, ax = plt, **kwargs):
        "Scatter plot the ADC samples to given axes, passing other keyword args unchanged"
        ax.scatter(self.ticks, self.samples, **kwargs)

    def plot(self, ax = plt, savefig = False, outDir = "./", ext = "png"):
        "Plot the ADC samples to given axes, with ledge features highlighted"
        pulserMag = self.header['ExtPulserMag']
        chip = self.header['ID']
        channel = self.header['channel']

        plt.clf()
    
        plt.plot(self.ticks, self.samples)
        plt.axhline(y = self.baseline, color = 'g', ls = '--')
        if "hasLedge" in dir(self):
            if self.hasLedge:
                if self.leftLobe:
                    plt.axvline(x = self.ledgeEdge[0], color = 'r', ls = '--')
                    plt.axvline(x = self.zeroCrossing, color = 'b', ls = '--')
                    plt.fill_between(self.ticks,
                                     self.samples,
                                     self.baseline,
                                     where = ((self.ticks > self.ledgeEdge[0]) &
                                              (self.ticks < self.zeroCrossing)),
                                     hatch = '////',
                                     edgecolor = '#1f77b4',
                                     facecolor = 'w')
                if self.rightLobe:
                    plt.axvline(x = self.ledgeEdge[1], color = 'r', ls = '--')
                    plt.fill_between(self.ticks,
                                     self.samples,
                                     self.baseline,
                                     where = ((self.ticks > self.zeroCrossing) &
                                              (self.ticks < self.ledgeEdge[1])),
                                     hatch = '\\\\\\\\',
                                     edgecolor = '#ff7f0e',
                                     facecolor = 'w')
    
        plt.xlim(0, np.max(self.ticks))
        plt.ylim(self.baseline - 1000, self.baseline + 1000)
        plt.xlabel(r'Time [ADC ticks]')
        plt.ylabel(r'ADC output')
    
        plt.text(2500, self.baseline + 750, "Ramp Voltage:")
        plt.text(2750, self.baseline + 550, str(pulserMag) + " V")

        plt.title("Chip: " + chip + ", Channel " + str(channel))
        plt.tight_layout()

        if savefig:
            ext = "."+ext
            outFileName = "_".join([chip,
                                    str(channel),
                                    str(pulserMag),
                                    ext])            
            plt.savefig(outDir+"/"+outFileName)
        else:
            plt.show()


    def fit_model(self, model, x0, ax = plt, **plotkwargs):
        """
        fit a given function of the form f(t, c1, c2, ...) with initial guess values for c1, c2...,
        then plot to given axes, passing other keyword args unchanged
        """
        def chi2(args):
            return sum((model(xi, *args) - yi)**2 for xi, yi in zip(self.ticks, self.samples))

        bfargs = opt.fmin_l_bfgs_b(chi2, x0, approx_grad = True)[0]
        print bfargs

        ax.plot(self.ticks, model(self.ticks, *bfargs), **plotkwargs)

        return bfargs

    def find_ledge(self):
        """
        try to find the ledge effect within the waveform
        do this by peak finding.  Every waveform should have one positive peak
        a waveform where the ledge effect is present will also have 
        another positive peak and a negative peak
        """
        
        # first, smooth the waveform out by convolution
        window_size = 15
        fringe_size = window_size/2
        filter = (1/float(window_size))*np.ones(window_size)
        diff = np.diff(self.samples, n = 1, prepend = self.baseline)
        smoothed = np.convolve(diff,
                               filter)[fringe_size:-fringe_size]
        for i in range(fringe_size):
            smoothed[i] = 0
            smoothed[-i-1] = 0

        diffThresh = 8
        diffThresh = 4

        noise = []
        noiseWindowSize = 30
        for i in range(len(self.samples) - noiseWindowSize):
            windowNoise = np.std(self.samples[i:i+noiseWindowSize])
            noise.append(windowNoise)
        noise = np.array(noiseWindowSize/2*[0] + noise + noiseWindowSize/2*[0])

        P = (np.array([np.sum((noise < ni for ni in noise), dtype = float)])/float(len(noise)))[0,:]
        # these are the first-pass peaks
        noisyPeaks = self.ticks[(self.ticks > 400) &
                                (noise > 18) &
                                # (noise > 0.4*np.max(noise[self.ticks > 400])) &
                                (P < 0.03) &
                                (np.diff(noise, n = 1, prepend = 0) > 0)]
        peaks = []
        for nP in noisyPeaks:
            # look around each peak within a small window
            # add the maximum within that window to peaks
            winSize = 150
            win = abs(self.ticks - nP) < winSize
            candidatePeaks = sorted(self.ticks[(noise == np.max(noise[win])) &
                                               (smoothed >= 0) & 
                                               (win)])
            if candidatePeaks:
                if not candidatePeaks[0] in peaks:
                    peaks.append(candidatePeaks[0])
                    
        if len(peaks) == 1:
            self.hasLedge = True
            self.leftLobe = True
            self.rightLobe = False
            self.ledgeEdge = peaks

            win = self.ticks > peaks[0]
            isMin = ((self.samples - self.baseline)**2 == np.min((self.samples[win] - self.baseline)**2))
            self.zeroCrossing = np.median(self.ticks[win & isMin])
        elif len(peaks) >= 2:
            self.hasLedge = True
            self.leftLobe = True
            self.rightLobe = True
            self.ledgeEdge = [peaks[0], peaks[-1]]

            win = (self.ticks > peaks[0]) & (self.ticks < peaks[-1])
            isMin = ((self.samples - self.baseline)**2 == np.min((self.samples[win] - self.baseline)**2))
            self.zeroCrossing = np.median(self.ticks[win & isMin])
        else:
            self.hasLedge = False
            self.leftLobe = False
            self.rightLobe = False
            self.ledgeEdge = None
            self.zeroCrossing = None


class waveformCollection:
    def __init__(self, waveformList):
        "initialize from a list of waveform objects"

        self.waveforms = waveformList
        self.size = len(waveformList)
        
        self.uniques = {key: np.unique([wf.header[key] for wf in self.waveforms])
                        for key in headerKeys}

    def __getitem__(self, selectionHeader):
        """ 
        takes a dict of header key: value pairs and returns a subset
        of waveforms whose headers match the supplied header fields
        """

        subSet = []

        for wf in self:
            if all(wf.header[key] == value
                   for key, value in selectionHeader.items()):
                subSet.append(wf)

        return waveformCollection(subSet)

    def __iter__(self):
        """
        iterating through the collection should just
        iterate through the individual waveforms
        """
        for wf in self.waveforms:
            yield wf

    def byHeaderCol(self, key):
        """
        given a key in headerKeys, iterate through all
        values of that key in this collection
        and yield (value, waveformCollection) pairs
        """

        for value in self.uniques[key]:
            selectionHeader = {key: value}
            yield value, self[selectionHeader]

    def broadcast(self, function, iterkeys = None, dtype = np.float64, *args, **kwargs):
        """
        Do the function to all waveforms in the collection, with the result saved in a numpy array
        """
        if iterkeys:
            shape = tuple(len(self.uniques[key])
                          for key in iterkeys)
            result = np.zeros(shape, dtype = dtype)
            thiskey = iterkeys[0]
            for i, (colVal, subCollection) in enumerate(self.byHeaderCol(thiskey)):
                result[i] = broadcast(function,
                                      subCollection,
                                      iterkeys[1:],
                                      *args,
                                      **kwargs)

        else:
            if len(self.waveforms) == 1:
                result = function(self.waveforms[0], *args, **kwargs)
            elif len(self.waveforms) > 1:
                result = np.array([function(wf, *args, **kwargs)
                                   for wf in self])
            else:
                raise ValueError, "No waveforms in collection!"

        return result
