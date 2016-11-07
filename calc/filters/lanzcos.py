#!/usr/bin/env 
"""
Lanczos Filter

121 point low pass lanczos filter.  Assumes hourly data


"""

__all__ = ["low_pass_weights", "spectral_window", "spectral_filtering", "lanzcos35"]

import numpy as np

def low_pass_weights(window, cutoff):
    """Calculate weights for a low pass Lanczos filter.

    Args:

    window: int
        The length of the filter window.

    cutoff: float
        The cutoff frequency in inverse time steps.

    """
    order = ((window - 1) // 2 ) + 1
    nwts = 2 * order + 1
    w = np.zeros([nwts])
    n = nwts // 2
    w[n] = 2 * cutoff
    k = np.arange(1., n)
    sigma = np.sin(np.pi * k / n) * n / (np.pi * k)
    firstfactor = np.sin(2. * np.pi * cutoff * k) / (np.pi * k)
    w[n-1:0:-1] = firstfactor * sigma
    w[n+1:-1] = firstfactor * sigma
    return w[1:-1]
    

    
def spectral_window(wgts35, n):
    
    Ff = np.arange(0,1,2./n)
    if (not np.round(Ff[-1],8) == 1.0 ) and ( n % 2 == 0):
        Ff = np.append(Ff, 1.0) #matlab difference in array generation using floats

    window = np.zeros(len(Ff))
    for i in np.arange(1,len(Ff)):
       window[i] = wgts35[0] + 2. * np.sum(wgts35[1:-1] * np.cos(np.arange(1,len(wgts35) - 1. ) * np.pi * Ff[i]))
    
    return (window, Ff)

def spectral_filtering(x, window):
    Nx = len(x)
    Cx = np.fft.fft(x)
    
    Cx = Cx[0: np.floor(Nx / 2) +1 ]
        
    CxH = Cx * window
    filt = np.conj(CxH[Nx - len(CxH) :0:-1])
    CxH = np.append(CxH, filt)
    y = np.real(np.fft.ifft(CxH))
    
    
    return(y, Cx)

"""------------------------------------------------------------------------------------"""

def lanzcos35(data, dt, Cf=35. ):
    """ Input - data (array-like) to be transformed   
                timestep   
                cuttoff frequency
    
        Output - filtered data (array-like)
        
        Data shoud be hourly and every hour
    """

    


    window_size = 121. * 2.
    wgts35 = low_pass_weights(window_size, 1. / Cf ) #filter coefs
    
    Nf = 1. / (2. * (dt * 24.)) #nyquist frequency
    Cf = Cf / Nf
        
    (window, Ff) = spectral_window(wgts35[len(wgts35) // 2:-1], len(data))
    Ff = Ff * Nf

    (y, Cx) = spectral_filtering(data, window)
    
    if len(y) > len(data):
        y = y[:-1]
    return (y)

def test():

    x = data['data']
    t = data['time'] * 24. 
    dt = (24. * 1.) / (1/data['dt'] )

    y=lanzcos(data,dt,cf)

if __name__ == "__main__":
    lanzcos35() 
