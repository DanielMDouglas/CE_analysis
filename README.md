# DUNE Cold Electronics Analysis scripts

## Overview

This package contains some useful scripts for analyzing waveforms collected from DUNE FEASIC chips

## Dependencies

The only packages required by these scripts are the standard Python numerical and plotting libraries:

 --* numpy
 --* scipy
 --* matplotlib

## Data Format

The waveforms which are produced by the data acquisition (DAQ) software are simple plaintext files containing individual waveforms.  Each line in a given file contains a single waveform and is preceded by a header with 13 values:

### Header Values

The thirteen header fields are:

| Header Position | Name                      | Description                                 |
| --------------- | ------------------------- | ------------------------------------------- |
| 1               | Chip ID                   | A unique ID for each chip                   |
| 2               | Chip Type                 | String indicating the chip version          |
| 3               | Socket                    |	Which socket the chip was in during testing |
| 4               | Channel                   | Which channel is the waveform from          |
| 5               | Config                    | The configuration byte currently loaded     |
| 6               | Other Config              | Configuration byte of all other channels    |
| 7               | Global Control            | Global control bits                         |
| 8               | DAC Config                | Internal DAC control bits	            |
| 9               | DAC Numerical             | Internal DAC numerical setting              |
| 10              | External Pulser Magnitude | External pulser amplitude in volts          |
| 11              | External Pulser Rise Time | External pulser rise time in microseconds   |
| 12              | Temperature               | Temperature (77 for LN2, 300 for RT)        |
| 14              | Buffer Length             | Number of data points that follow           |

#### Config Bytes

For the V7 configuration bytes, a little decoding is needed:

| Test Pulse | Baseline   | Gain           | Peaking Time  | SMN Monitor        | Output Buffer    |
| ---------- | ---------- | -------------- | ------------- | ------------------ | ---------------- |
| 0 = OFF    | 0 = 900 mV | 00 = 4.7 mV/fC | 10 = 0.5 usec | 0 = Disabled       | 0 = OFF          |
| 1 = ON     | 1 = 200 mV | 10 = 7.8 mV/fC | 00 = 1 usec   | 1 = To test pad    | 1 = ON (typical) |
|            |            | 01 = 14 mV/fC  | 11 = 2 usec   | (keep set to zero) |                  |
|            |            | 11 = 25 mV/fC  | 01 = 3 usec   |                    |                  |

Just read across the table left to right to figure out the bits

For example: typical settings in a TPC and with external test pulse:

Test pulser = ON,
Baserline = 900 mV,
Gain = 14 mV/fC,
Peaking = 2 usec,

Gives bits 1001 1101 which is hex: 9D

#### Global Control Bits

| Reserved      | SDC    | SLKH            | Ch 16 filter | Channel 0  | STB1            | Leakage    |
| ------------- | ------ | --------------- | ------------ | ---------- | --------------- | ---------- |
| 00 = reserved | 0 = DC | 0 = 1x leakage  | 0 = disabled | 0 = Normal | 0 = Temperature | 0 = 500 pA |
|               | 1 = AC | 1 = 10x leakage | 1 = enabled  | 1 = STB1   | 1 = Bandgap     | 1 = 100 pA |

Usually we keep these all set to zero
To monitor temperature: 0000 0100 = hex: 04
Leakage 100 pA = 0000 0001 = hex: 01
Leakage 500 pA = 0000 0000 = hex: 00
Leakage 1000 pA = 0001 0001 = hex: 11
Leakage 5000 pA = 0001 0000 = hex: 10

#### Binary to Hex Conversion

| Binary | Hex |
| ------ | --- |
| 0000   | 0   |
| 0001   | 1   |
| 0010   | 2   |
| 0011   | 3   |
| 0100   | 4   |
| 0101   | 5   |
| 0110   | 6   |
| 0111   | 7   |
| 1000   | 8   |
| 1001   | 9   |
| 1010   | A   |
| 1011   | B   |
| 1100   | C   |
| 1101   | D   |
| 1110   | E   |
| 1111   | F   |

### ADC Samples

The data following the header are the output of a analog-to-digital converter (ADC) on the testing chip.  This ADC takes a sample every 0.25 usec (4 MHz) and converts it to a 14-bit integer (between 0 and 2^14).  As the precise values depend upon the configuration of the ADC, it is acceptable to report these units as "ADC ticks" (a unit of time) and "ADC counts" (a unit of, usually, voltage).

## coldData.py

This script reads the contents of a file (as described above) and loads it into a `waveformCollection` (described below).  A `dataFile` object is initialized with a filename and will return a `waveformCollection` upon execution of the `load` method.  For example:

```
myDataFileObject = dataFile("myDataFolder/myDataFile.dat")
myWaveformCollectionObject = myDataFileObject.load()
```

## coldAna.py

This program defines the `waveform` and `waveformCollection` classes.

### The `waveform` Class

This class contains the data from a single line of a data file as described above.  This is the output of a single channel, using a single configuration setting, etc.  The important attributes of this class are `header`, which is a ditionary containing the values of the header fields described above, and `samples`, which is a series of ADC values.  Also contained in this class are `ticks`, which is a series which serves as the t-coordinate (in ADC ticks) of the `samples`.  `ticks` is always just `[0, 1, 2, ..., Nsamples - 1]`.

Additionally, the `waveform` class has some utility methods, such as

 * plot: plots the waveform vs. time, highlighting the ledge (if `find_ledge` has been run and this waveform has a ledge feature)
 * calc_baseline: given a sideband region (a region of the waveform that is assumed to contain no response), find the baseline by taking an average of the samples.
 * find_ledge: search the waveform for features indicative of a ledge.  This method sets the `ledgeEdge` attribute, which containes the beginning and end of the found ledge.  It also sets a number of boolean flags:
 --* hasLedge: Does this waveform seem to have a ledge feature?
 --* leftLobe: Is the left (above the baseline) lobe contained in the sample series?
 --* rightLobe: Is the right (below the baseline) lobe contained in the sample series?

### The `waveformCollection` Class

This class is a simple container for `waveform` objects, which acts just like a list in most ways, with some special additions.  Important attributes of this class are `waveforms`, the list of actual `waveform` objects, `size`, the length of that list, and `uniques`, a dictionary of header fields and the unique values of those fields which are represented in the collection.

Selecting a subset of a `waveformCollection` object can be done by passing a dictionary of header values.  The result is another `waveformCollection` object which contains only waveforms with those header conditions.  For example:

```
allWaveforms = myBigDataFile.load()

justWaveformsFromChannel1 = allWaveforms[{'channel': 1}]

anEvenSmallerSubset = allWaveforms[{'channel': 1, 'socket': 3}]
```

`waveformCollection` objects are also iterable in the normal way:

```
for thisWaveform in allWaveforms:
    print thisWaveform.baseline
```

In addition, you can iterate through sub-collections by a header column using the `byHeaderCol` method:

```
for channel, subCollection in allWaveforms.byheaderCol("channel"):
    print channel, subCollection.size
    # do something else with subCollection
```

Lastly, the `broadcast` method is a simple way to apply a function to all `waveform` objects within a `waveformCollection` object.  If the function has a return value, it will be return in the form of a `numpy.ndarray`.  For example:

```
def get_average(thisWaveform):
    return np.mean(thisWaveform.samples)

averages = allWaveforms.broadcast(get_average)
```

## Contact/Contribute!

If you have any questions, comments, or would like to contribute, your help is greatly appreciated!  Please feel free to send me an email at dougl215@msu.edu or talk to me in person, since this software is probably only useful to a very small group of people :)