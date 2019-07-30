import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats as st

from coldAna import *
from coldData import V4_cold_500mV as thisCollection

colors = {ID: i for ID, i in zip(thisCollection.uniques['ID'],
                                 ['c', 'b', 'g', 'k', 'r'])}

# keep track of which items have already been added to the legend
inLegend = set()

for config, perConfCollection in thisCollection.byHeaderCol('conf'):
    for chip, perChipCollection in perConfCollection.byHeaderCol('ID'):

        bls = [wf.baseline for wf in perChipCollection]

        plt.scatter(config,
                    np.std(bls),
                    color = colors[chip],
                    label = chip if not chip in inLegend else "")
        inLegend.add(chip)

plt.xlabel(r'Configuration Byte')
plt.ylabel(r'Baseline Standard Deviation [ADC Counts]')
plt.legend()
plt.show()
