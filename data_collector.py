#!/usr/bin/env python2.7
#
#

import atexit

import json
import getopt
import datetime
import httplib
import logging
import serial
import sys
import time
import numbers
import lockfile

import xbee_api
import tmp36
import battery

MAIN_LOGFILE = 'data_collector.log'
DATA_FILE = 'data_collector.csv'
LOCK_FILE='xbee_sensor_monitor.lock'

logger = None
global_lock = lockfile.FileLock(LOCK_FILE)

VREF = 1221 #LM385-1.2

def cleanup():
    global logger
    if logger:
        logger.info("Stop")
    if global_lock.is_locked():
        global_lock.release()

def usage():
    print """
%s [-s /dev/ttyUSB0]

-s port -- use serial port <port>. Default is /dev/ttyUSB0
-c -- output packet log to console
-d -- debug mode (more logging)

"""  % sys.argv[0]

def get_adc_v(pkt, adc_idx):
    "Retruns ADC value in volts"
    return float(pkt.get_adc(adc_idx))*VREF/(pkt.num_samples * 1024.0)

def voltage_correction(v):
    "empirical formula to correct estimated voltage to actual one"
    return -12.4647 + 10.3012*v - 2.14076*(v**2) + 0.152242*(v**3)

def temp_correctiom(t,va):
    "correctes estimated temperature based on actual voltage"
    tc = 20.0-16.4 # it was measuring 16.4C when it was actually 21C
    return t-10.7156 + 3.24716*va + tc

def main():
    global logger

    log_format = '%(asctime)s %(process)d %(filename)s:%(lineno)d %(levelname)s %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        filename=MAIN_LOGFILE,
                        filemode='a')

    logger = logging.getLogger('default')

    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], 's:cd', [])

        except getopt.GetoptError:
            usage()
            sys.exit(2)

        try:
            # timeout=0 causes it to raise AlreadyLocked. Any timeout >0
            # causes LockTimeout
            global_lock.acquire(timeout=0)
        except lockfile.AlreadyLocked:
            logger.error('Another copy of this program is running')
            sys.exit(1)

        atexit.register(cleanup)

        serial_port= '/dev/ttyUSB0'
        console = False

        for o, a in opts:
            if o in ['-s']:
                serial_port = a
            elif o in ['-c']:
                console = True
            elif o in ['-d']:
                logger.setLevel(logging.DEBUG)
            else:
                usage()
                sys.exit(1)

        print 'Using serial port %s' % serial_port

        s = serial.serialposix.Serial(port=serial_port,
                                      baudrate=9600, bytesize=8, parity='N', stopbits=1,
                                      timeout=120,
                                      rtscts=1)

        logger.info("Starting collection")

        data_file = file(DATA_FILE, 'a')

        pkt_reader = xbee_api.read_packet(s)
        while True:
            pkt = pkt_reader.next()

            try:
                radc0 = pkt.get_adc(0)
                radc1 = pkt.get_adc(1)
                adc0 = float(get_adc_v(pkt,0))
                adc1 = float(get_adc_v(pkt,1))
                battery_V = voltage_correction(battery.get_battery_from_adc(adc1)/1000.0)
                temp_C = temp_correctiom(tmp36.get_t_from_adc(adc0),battery_V)

                time_now = time.time()
                report = 'A={0} T={1:.1f}C V={2:.3f}V'.format(
                    pkt.address,
                    temp_C, battery_V)

                if console:
                    print report
                else:
                    logger.debug(report)

                csv_report = '{0},{1},{2},{3},{4:.1f},{5:.3f}\n'.format(
                    time.time(), pkt.address, radc0, radc1, temp_C, battery_V*1000.0)

                data_file.write(csv_report)
                data_file.flush()
                    
            except IndexError, e:
                # I get this from pkt.get_adc() when packet is broken
                logger.error('Broken XBee packet: "{0}"'.format(pkt))


    except serial.SerialException,e:
        print e

if __name__ == '__main__':
    main()
