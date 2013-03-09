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

MAIN_LOGFILE = 'data_collector.log'
DATA_FILE = 'data_collector.csv'
LOCK_FILE='xbee_sensor_monitor.lock'

logger = None
global_lock = lockfile.FileLock(LOCK_FILE)

VREF = 1235 #LM385-1.2

def cleanup():
    if global_lock.is_locked():
        global_lock.release()

def usage():
    print """
%s [-s /dev/ttyUSB0]

-s port -- use serial port <port>. Default is /dev/ttyUSB0
-c -- output packet log to console

"""  % sys.argv[0]

def get_adc_v(pkt, adc_idx):
    "Retruns ADC value in volts"
    return float(pkt.get_adc(adc_idx)/pkt.num_samples * VREF / 1024)

def main():
    global logger

    log_format = '%(asctime)s %(process)d %(filename)s:%(lineno)d %(levelname)s %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        filename=MAIN_LOGFILE,
                        filemode='w')

    logger = logging.getLogger('default')

    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], 's:c', [])

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
            else:
                usage()
                sys.exit(1)

        print 'Using serial port %s' % serial_port

        s = serial.serialposix.Serial(port=serial_port,
                                      baudrate=9600, bytesize=8, parity='N', stopbits=1,
                                      timeout=120,
                                      rtscts=1)

        data_file = file(DATA_FILE, 'a')

        pkt_reader = xbee_api.read_packet(s)
        while True:
            pkt = pkt_reader.next()

            try:
                adc0 = float(get_adc_v(pkt,0))
                adc1 = float(get_adc_v(pkt,1))
                temp_C = tmp36.get_t_from_adc(adc0)

                time_now = time.time()
                report = 'packet_size={0} adc0={1:.3f} mV adc1={2:.3f} mV T={3:.1f} C'.format(
                    pkt.packet_size, adc0, adc1, temp_C)

                if console:
                    print report
                else:
                    logger.info(report)

                    data_file.write(str(pkt))
                    data_file.flush()
                    
            except IndexError, e:
                # I get this from pkt.get_adc() when packet is broken
                logger.error('Broken XBee packet: "{0}"'.format(pkt))


    except serial.SerialException,e:
        print e

if __name__ == '__main__':
    main()
