from coldAna import *

# this is set up for my machine specifically
# you will probably have to adjust the dataDir
# path to your specific directory

dataDir = "../data/"

V7_cold_ledge = load_file(dataDir + "2019-07-31-09-45.dat")

# V4_cold_500mV = load_file(dataDir + "V4-cold-500mV.dat")

# the rest are commented out for now to save time from loading them
# this can probably be done in a better way...

# V4_cold_100mV = load_file(dataDir + "V4-cold-100mV.dat")

# V7_warm = load_file(dataDir + "V7-Warm.dat",
#                     bufferSize = 400)

# V7_2019_07_25_14_30_00 = load_file(dataDir + "2019-07-25-14-30-00.dat",
#                                    bufferSize = 400)

# V7_2019_07_25_14_30_00_cold = load_file(dataDir + "2019-07-25-15-15-00-cold.dat",
#                                         bufferSize = 400)
