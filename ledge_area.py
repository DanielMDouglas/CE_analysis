import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats as st

from coldAna import *
from coldData import V7_cold_ledge

mpl.rc('font', family = 'FreeSerif', size = 16, weight = 'bold')
mpl.rc('text', usetex = True)
plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

def fit_model(x, y, model, c0, bounds = None):
    """
    fit a given function of the form f(t, c1, c2, ...) with initial guess values for c1, c2...
    """
    def chi2(args):
        return sum((model(xi, *args) - yi)**2 for xi, yi in zip(x, y))
    
    bfargs = opt.fmin_l_bfgs_b(chi2, c0, approx_grad = True, bounds = bounds)[0]
    return bfargs

def fit_coupled_models(x1, x2, y1, y2, model, constraint, c0, bounds = None):
    """
    fit a given function of the form f(t, c1, c2, ..., cn) with initial 
    guess values for c1, c2, ..., cn-1
    to two separate data sets, where the parameters are constrained by some function
    """

    def chi2(args):
        params1, params2 = constraint(*args)
        chi2_1 = sum((model(xi, *params1) - yi)**2 for xi, yi in zip(x1, y1))
        chi2_2 = sum((model(xi, *params2) - yi)**2 for xi, yi in zip(x2, y2))

        return chi2_1 + chi2_2
        
    bfargs = opt.fmin_l_bfgs_b(chi2, c0, approx_grad = True, bounds = bounds)[0]
    return bfargs

@np.vectorize
def quadratic_model(V, A, B, C):
    """
    it's a parabola
    """
    return max(0, A*V**2 + B*V + C)

def quadratic_solution(A, B, C):
    """
    return the left root of a parabola with negative A
    """
    if A == 0:
        return -C/B
    else:
        return (-B + np.sqrt(B**2 - 4.*A*C))/(2.*A)

def quadratic_zero_coupling(A, B, C, D, E):
    """
    given a subset of paramters in two quadratic models,
    return the full set of parameters s.t. the two
    parabolas share a zero-crossing
    """
    root = quadratic_solution(A, B, C)
    F = -D*root**2 - E*root
    return (A, B, C), (D, E, F)

model_V_space = np.linspace(0.0, 1.6, 1000)

thisCollection = V7_cold_ledge[8].load()
# thisCollection = thisCollection[{"ID": "P211", "channel": 0}]
plotWaveforms = False
plotRegressions = False
# plotWaveforms = True
# plotRegressions = True
plotHistograms = False

shape = (len(thisCollection.uniques['ID']),
         len(thisCollection.uniques['channel']),
         len(thisCollection.uniques['ExtPulserMag']))
Vcrit = np.zeros(shape)
leftA = np.zeros(shape)
rightA = np.zeros(shape)

hasLedge = np.zeros(shape, dtype = bool)
leftLobe = np.zeros(shape, dtype = bool)
rightLobe = np.zeros(shape, dtype = bool)

V = thisCollection.uniques['ExtPulserMag']

for i, (chip, subCollection) in enumerate(thisCollection.byHeaderCol('ID')):
    # print "chip:", chip
        
    for j, (channel, perChannelCollection) in enumerate(subCollection.byHeaderCol('channel')):
        # print "channel:", channel
        
        for k, (pulserMag, perVoltageCollection) in enumerate(perChannelCollection.byHeaderCol('ExtPulserMag')):
            # print "pulser V:", pulserMag, "V" 
            
            for wf in perVoltageCollection.waveforms:
                wf.find_ledge()
                if plotWaveforms:
                    wf.plot()

                hasLedge[i, j, k] = wf.hasLedge
                leftLobe[i, j, k] = wf.leftLobe
                rightLobe[i, j, k] = wf.rightLobe

                if wf.hasLedge:
                    if wf.leftLobe:
                        leftArea = np.sum(wf.samples[(wf.ticks > wf.ledgeEdge[0]) &
                                                     (wf.ticks < wf.zeroCrossing)]
                                          - wf.baseline)
                    else:
                        leftArea = 0
                    if wf.rightLobe:
                        rightArea = np.sum(wf.samples[(wf.ticks < wf.ledgeEdge[1]) &
                                                      (wf.ticks > wf.zeroCrossing)]
                                           - wf.baseline)
                    else:
                        rightArea = 0
                        
                    leftA[i,j,k] = leftArea
                    rightA[i,j,k] = rightArea


        if all(leftA[i, j, :] == 0):
            thisVcrit = np.nan
        else:
            leftMask = (~hasLedge[i, j, :]) | (hasLedge[i, j, :] & leftLobe[i, j, :])
            leftV = V[leftMask]
            leftData = leftA[i, j, leftMask]
            leftArgs = fit_model(leftV,
                                 leftData,
                                 quadratic_model,
                                 [1, 1, 1],
                                 bounds = [(None, 0),
                                           (None, None),
                                           (None, None)])
        
            rightMask = (~hasLedge[i, j, :]) | (hasLedge[i, j, :] & rightLobe[i, j, :])
            rightV = V[rightMask]
            rightData = rightA[i, j, rightMask]
            rightArgs = fit_model(rightV,
                                  np.abs(rightData),
                                  quadratic_model,
                                  [1, 1, 1],
                                  bounds = [(None, 0),
                                            (None, None),
                                            (None, None)])
        
            bf = fit_coupled_models(leftV,
                                    rightV,
                                    leftData,
                                    np.abs(rightData),
                                    quadratic_model,
                                    quadratic_zero_coupling,
                                    np.concatenate((leftArgs, rightArgs[:-1])),
                                    bounds = [(None, 0),
                                              (None, None),
                                              (None, None),
                                              (None, 0),
                                              (None, None)])

            leftArgs, rightArgs = quadratic_zero_coupling(*bf)
            thisVcrit = quadratic_solution(*leftArgs)

        # print "Vcrit:", round(thisVcrit, 2), "V"
        
        Vcrit[i, j, k] = thisVcrit

        print chip, channel, thisVcrit

        if plotRegressions:
            plt.scatter(leftV, leftData, label = "Positive lobe", marker = '+')
            plt.scatter(rightV, np.abs(rightData), label = "Negative lobe", marker = '+')

            plt.plot(model_V_space, quadratic_model(model_V_space, *leftArgs))
            plt.plot(model_V_space, quadratic_model(model_V_space, *rightArgs))

            plt.xlim(np.min(model_V_space), np.max(model_V_space))
            plt.ylim(0, 1.1*max(leftA[i, j, :]))
            plt.title("Chip: " + chip + ", Channel " + str(channel))
            plt.xlabel(r'Ramp Voltage [V]')
            plt.ylabel(r'Area Under Ledge')
            plt.tight_layout()
        
            plt.legend(title = r'$V_{\mathrm{crit}} = $' + str(round(thisVcrit, 2)) + r' V', frameon = False)
            plt.show()

if plotHistograms:
    bins = np.linspace(-14000, 15000, 25)
    for thisLeftA, thisRightA, (chip, subCollection) in zip(leftA,
                                                            rightA,
                                                            thisCollection.byHeaderCol('ID')):
        plt.hist([l + r for l, r in zip(thisLeftA, thisRightA)],
                 bins = bins,
                 histtype = 'step',
                 label = chip)
    plt.hist([l + r for l, r in zip(np.concatenate(leftA), np.concatenate(rightA))],
             bins = bins,
             histtype = 'step',
             label = "Total",
             color = 'k')

    plt.xlabel(r'L + R')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

    bins = np.linspace(0, 1.5, 25)
    for thisVcrit, (chip, subCollection) in zip(Vcrit, thisCollection.byHeaderCol('ID')):
        plt.hist(thisVcrit,
                 bins = bins,
                 histtype = 'step',
                 label = chip)
    plt.hist(np.concatenate(Vcrit),
             bins = bins,
             histtype = 'step',
             label = "Total",
             color = 'k')
        
    plt.xlabel(r'$V_{\mathrm{crit}}$ [V]')
    plt.legend()
    plt.tight_layout()
    plt.show()
