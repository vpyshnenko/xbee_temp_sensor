#!/usr/bin/python

"""
this script reads xbee_base.log and compiles data file that logs
battery voltage against time in the CSV format, suitable for importing
into a spreadsheet
"""

import datetime
import re

LOG_FILE = '/var/tmp/xbee_base.log.backup'
SEC_FRACTION = re.compile(',.*$')

start_time = None
output_hour = 0.0

for line in file(LOG_FILE, 'r'):
    fields = line.split(' ')
    fields[1] = re.sub(SEC_FRACTION, '', fields[1])

    timestamp = datetime.datetime.strptime(
        ' '.join(fields[0:2]), '%Y-%m-%d %H:%M:%S')

    if start_time is None:
        start_time = timestamp

    delta = (timestamp-start_time).days + (timestamp-start_time).seconds / (24*3600.0)
    delta_hours = delta * 24.0
    
    if 'adc0' in fields[6]:
        value = float(fields[6].replace('adc0=', ''))

        if delta_hours > output_hour:
            print '{0:.2f},{1:.3f}'.format(delta_hours, value)
            output_hour += 0.25

