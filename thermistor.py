
"""
Simple module implementing math for the Sure Electronics thermoresistor
used in a resistor divider with R1 5.6k

Vo = Vcc * Rt / (Rt + R1)

Notice that ADC returns a code that is equal to

Vo = code * Vcc / 1023

or 

Vo / Vcc = code / 1023

combining two equations and solving for Rt:

Vo / Vcc = Rt / (Rt + R1) = code / 1023

Rt = (code * R1) / (1023 - code)

"""

import numpy

R1 = 5.6   # kohm

# a copy of calibration table from datasheet, sorted by resistance.
# Resistance is in kohm, temperature in C.
# Note that numpy.interp() requires X to be in the incrementing order

calibration_r = [
    0.925,
    1.064,
    1.301,
    1.412,
    1.622,
    1.896,
    2.19,
    2.556,
    2.952,
    3.455,
    4.064,
    4.806,
    5.74,
    6.848,
    8.227,
    10,
    12.35,
    15.13,
    18.4,
    22.72,
    28.42,
    35.36,
    44.19,
    56.48,
    72.09,
    92.57,
    121.
    ]

calibration_t = [
    100,
    95,
    90,
    85,
    80,
    75,
    70,
    65,
    60,
    55,
    50,
    45,
    40,
    35,
    30,
    25,
    20,
    15,
    10,
    5,
    0,
    -5,
    -10,
    -15,
    -20,
    -25,
    -30
    ]



def get_t(res):
    """
    given resistance, compute and return temperature C. Reisstance is in kOhm

    (res - cal_res_1) / (cal_res_2 - cal_res_1) = (temp - cal_temp_1) / (cal_temp_2 - cal_temp_1)

    temp = cal_temp_1 + (res - cal_res_1) / (cal_res_2 - cal_res_1) * (cal_temp_2 - cal_temp_1)

    """
    y = numpy.interp([res], calibration_r, calibration_t)
    return y[0]

def get_res_from_adc(code):
    if code >= 1023.0:
        return R1 * 100000  # just very large R, to make sure we never divide by 0
    return float(code) * R1 / (1023.0 - float(code))

def get_t_from_adc(code):
    """
    returns temperature C from ADC value. This assumes thermistor is used
    in resistor divider with R1

    Rt = (code * R1) / (1023 - code)

    """
    return get_t(float(code) * R1 / (1023 - code))




