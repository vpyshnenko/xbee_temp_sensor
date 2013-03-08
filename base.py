#!/usr/bin/env python
#
#

import atexit

try:
    import json
except ImportError:
    import simplejson as json

import getopt
import datetime
import httplib
import logging
import serial
import socket
import urllib
import sys
import time
import numbers
import pdb
import lockfile

import xbee_api
import thermistor
import tmp36


MAIN_LOGFILE = '/var/tmp/xbee_base.log'
BATTERY_DATA_FILE = '/var/tmp/battery.log'
DATA_LOGGER_UPDATE_INTERVAL = 300  # 5 min
BATTERY_LOG_INTERVAL = 1800    # 30 min

logger = None
global_lock = lockfile.FileLock('/var/lock/xbee_sensor_monitor')


def cleanup():
    if global_lock.is_locked():
        global_lock.release()


def send_nimbits(name, value):
    assert isinstance(value, numbers.Real)

    # create dictionary
    data = {"email":NIMBITS_EMAIL,
            "secret":NIMBITS_SECRET,
            "point":name,
            "value":'{0:.3f}'.format(value)}

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    try:
        conn = httplib.HTTPConnection("app.nimbits.com")

        conn.request("POST", "/service/currentvalue",
                     urllib.urlencode(data), headers)

        response = conn.getresponse()
        logger.info('Nimbits data point "%s": response: %s %s' % (
                name, response.status, response.reason))
    except socket.error, e:
        logger.error('%s: nimbits socket error: %s' % (datetime.datetime.now(), e))

def record_battery_v(battery_file, value):
    assert isinstance(value, numbers.Real)
    now = datetime.datetime.now()
    battery_log_line = '{0} {1:.3f}\n'.format(now.strftime('%Y-%m-%d %H:%M:%S'),
                                              value)
    battery_file.write(battery_log_line)
    battery_file.flush()


def usage():
    print """
%s [-n] [-s /dev/ttyS0]

-n      -- do not send data to nimbits (by default, send)
-s port -- use serial port <port>. Default is /dev/ttyS0

"""  % sys.argv[0]


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
            opts, args = getopt.getopt(sys.argv[1:], 's:nc', [])

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

        serial_port= '/dev/ttyS0'
        send_to_data_logger = True
        console = False

        for o, a in opts:
            if o in ['-s']:
                serial_port = a
            elif o in ['-n']:
                send_to_data_logger = False
            elif o in ['-c']:
                console = True
            else:
                usage()
                sys.exit(1)

        print 'Using serial port %s' % serial_port
        print 'Sending to data_logger: %s' % send_to_data_logger

        s = serial.serialposix.Serial(port=serial_port,
                                      baudrate=9600, bytesize=8, parity='N', stopbits=1,
                                      timeout=120,
                                      rtscts=1)

        s.open()

        battery_file = file(BATTERY_DATA_FILE, 'a')

        data_logger_update_time = time.time()
        battery_log_time = time.time()

        pkt_reader = xbee_api.read_packet(s)
        while True:
            pkt = pkt_reader.next()

            try:
                adc0 = float(pkt.get_adc(0))
                adc1 = float(pkt.get_adc(1))
                temp_C = tmp36.get_t_from_adc(adc1)

                # res = thermistor.get_res_from_adc(adc1)
                # temp_C = thermistor.get_t(res)
                # temp_F = 32 + temp_C * 5 / 9

                # send to data_logger every 5 min
                time_now = time.time()
                if time_now >= data_logger_update_time:
                    data_logger_update_time += DATA_LOGGER_UPDATE_INTERVAL
                    if time_now > data_logger_update_time:
                        # this happens if we got stuck in pkt_reader.next() for a long time
                        # and data_logger_update_time is in the past
                        data_logger_update_time = time_now + DATA_LOGGER_UPDATE_INTERVAL

                if time_now >= battery_log_time:
                    record_battery_v(battery_file, adc0)
                    battery_log_time += BATTERY_LOG_INTERVAL
                    if time_now > battery_log_time:
                        battery_log_time = time_now + BATTERY_LOG_INTERVAL

                report = 'packet_size={0} adc0={1:.3f} mV adc1={2:.3f} mV T={3:.1f} C'.format(
                    pkt.packet_size, adc0, adc1, temp_C)

                if console:
                    print report
                else:
                    logger.info(report)
            except IndexError, e:
                # I get this from pkt.get_adc() when packet is broken
                logger.error('Broken XBee packet: "{0}"'.format(pkt))


    except serial.SerialException,e:
        print e


if __name__ == '__main__':
    main()
