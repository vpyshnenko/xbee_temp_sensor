
"""
API for TMP36 temperature sensor

  scale factor: 10 mV/C
  offset: 500 mV
  Vout = 750 mV at 25 C

  v1 = 500
  T = (v - v1) * 10

"""

import numpy

V1 = 500.0
K = 10.0

def get_t_from_adc(Vmv):
    """
    returns temperature C from ADC value. 

    code    Vout
    ------------
    0       0
    1023    Vref
    
    """
    return (Vmv - V1) / K
