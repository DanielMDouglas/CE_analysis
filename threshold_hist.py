import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rc('font', family = 'FreeSerif', size = 16, weight = 'bold')
mpl.rc('text', usetex = True)
plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

data = np.loadtxt("../data/thresholds.dat", dtype = str)
cleaned = [[id, int(channel), float(thresh)]
           for id, channel, thresh
           in data if thresh != 'nan']

bins = np.linspace(0, 1.5, 31)

ids = ["P211", "A1537", "A2910", "A2653"]
for id in ids:
    plt.hist([i[2] for i in cleaned if i[0] == id], bins = bins, histtype = 'step', label = id)

plt.hist([i[2] for i in cleaned], bins = bins, histtype = 'step', label = "Total", color = "black")

plt.xlabel(r'$V_{\mathrm{crit}}$ [V]')
plt.legend()
plt.show()

plt.hist2d([i[1] for i in cleaned],
           [i[2] for i in cleaned],
           bins = (range(17), bins))
plt.colorbar()
plt.xlabel(r'Channel')
plt.ylabel(r'$V_{\mathrm{crit}}$ [V]')
plt.tight_layout()
plt.show()

chips = [list(np.unique(data[:,0])).index(i[0]) for i in cleaned]
plt.hist2d(chips,
           [i[2] for i in cleaned],
           bins = (range(len(np.unique(data[:,0]))+1), bins))
plt.colorbar()
plt.xlabel(r'Chip')
plt.xticks(range(len(np.unique(data[:,0]))), np.unique(data[:,0]), rotation = 'vertical')
plt.ylabel(r'$V_{\mathrm{crit}}$ [V]')
plt.tight_layout()
plt.show()

# plt.hist([i[0] for i in cleaned], bins = np.unique(data[:,0]))
# plt.show()
