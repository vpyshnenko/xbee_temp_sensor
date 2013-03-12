"""
API for battery voltage monitoring.
Assuming battery voltage is divided by pair of resistors feed to
ADC input
"""

K=4.43/0.892

def get_battery_from_adc(v):
    return v*K
    

