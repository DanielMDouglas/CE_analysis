import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats as st

from coldAna import *
from coldData import V7_cold_ledge as thisCollection
print "loaded data"
print thisCollection.size

subCollection = thisCollection[{"peakingTime": "2 usec", "gain": "14 mV/fC"}]
print "down-selected waveforms"
print subCollection.size

thisWF = subCollection.waveforms[subCollection.size-1]

@np.vectorize
def gauss_and_BL(x, baseline, height, width, t0):
    return baseline + height*st.norm.pdf(x, loc = t0, scale = width)

guessParams = [thisWF.baseline, 23000, 2, 273]

fig, (ax1, ax2) = plt.subplots(2, 1, sharex = True)

print "fitting..."
bfParams = thisWF.fit_model(gauss_and_BL,
                            guessParams,
                            ax = ax1,
                            label = 'fit',
                            color = 'orange')
print "done!"

thisWF.plot(ax = ax1,
            marker = '+',
            label = 'data',
            color = 'b')

ax1.set_ylabel(r'ADC counts')
ax1.legend()

ax2.plot(thisWF.ticks, thisWF.samples - gauss_and_BL(thisWF.ticks, *bfParams))
    
ax2.set_xlabel(r'Time [ADC ticks]')
ax2.set_ylabel(r'Data - Model')

plt.show()
