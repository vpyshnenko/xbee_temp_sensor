
"""
API for TMP36 temperature sensor

  scale factor: 10 mV/C
  Vout = 750 mV at 25 C

  v1 = 750
  t1 = 25
  T = t1 + (v - v1) * 10

"""

import numpy

V1 = 750.0
T1 = 25.0
K = 10

def get_t_from_adc(Vmv):
    """
    returns temperature C from ADC value. 

    code    Vout
    ------------
    0       0
    1023    Vref
    
    """
    return T1 + (Vmv - V1) / K
