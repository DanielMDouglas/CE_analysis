import numpy as np
import scipy.optimize as opt

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

