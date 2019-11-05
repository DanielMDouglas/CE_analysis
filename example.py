from coldAna import *
from coldData import *
import matplotlib.pyplot as plt

d = dataFile('/Users/mayajoyce/maya_tutorial/run3/batch1/batch1_warm_0.5us.dat')
wfc = d.load()

#select a subset of waveforms that match these headers
foo = wfc[{'socket': 1, 'channel': 5}]

fig = plt.figure()

for extPulserMag, pulserCollection in foo.byHeaderCol('ExtPulserMag'):
    for wf in pulserCollection.waveforms:
        wf.find_ledge()
        if wf.hasLedge:
            print 'waveform with mag' , extPulserMag, 'has ledge at' , wf.ledgeEdge
            if wf.rightLobe:
                print 'ledge has length', wf.ledgeEdge[1] - wf.ledgeEdge[0]
        plt.plot(wf.samples, label = extPulserMag)

plt.legend()
plt.show()
