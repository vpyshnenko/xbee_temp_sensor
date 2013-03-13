
"""
API for TMP36 temperature sensor

  scale factor: 10 mV/C
  offset: 500 mV
  Vout = 750 mV at 25 C

  v1 = 500
  T = (v - v1) / 10

"""

V1 = 500.0
K = 10.0

def get_t_from_adc(Vmv):
    """
    returns temperature in C from ADC value. 
    """
    return (Vmv - V1) / K
