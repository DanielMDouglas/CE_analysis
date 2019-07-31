import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats as st

from coldAna import *
from coldData import V4_cold_500mV as thisCollection

subCollection = thisCollection[{"peakingTime": "2 usec", "gain": "14 mV/fC"}]
thisWF = subCollection.waveforms[100]

@np.vectorize
def gauss_and_BL(x, baseline, height, width, t0, ceiling):
    return np.min((baseline + height*st.norm.pdf(x, loc = t0, scale = width), ceiling))

guessParams = [thisWF.baseline, 23000, 2, 763, 14050]

fig, (ax1, ax2) = plt.subplots(2, 1, sharex = True)

bfParams = thisWF.fit_model(gauss_and_BL,
                            guessParams,
                            ax = ax1,
                            label = 'fit',
                            color = 'orange')

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
