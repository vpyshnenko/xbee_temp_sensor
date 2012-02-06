#!/usr/bin/python

import getopt
import datetime
import httplib
import logging
import serial
import socket
import urllib
import sys
import time

import xbee_api
import thermistor
import tmp36


MAIN_LOGFILE = '/var/tmp/xbee_base.log'

logger = None


def send_nimbits(name, value):
    # create dictionary
    data = {"email":"vadimk@gmail.com",
            "secret":"a8909970-e892-4bc4-afb8-7330d4d6ddc6",
            "point":name,
            "value":value}

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    try:
        conn = httplib.HTTPConnection("app.nimbits.com")

        conn.request("POST", "/service/currentvalue", urllib.urlencode(data), headers)

        response = conn.getresponse()
        logger.info('Nimbits data point "%s": response: %s %s' % (
                name, response.status, response.reason))
    except socket.error, e:
        logger.error('%s: nimbits socket error: %s' % (datetime.datetime.now(), e))


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

        serial_port= '/dev/ttyS0'
        send_to_nimbits = True
        console = False

        for o, a in opts:
            if o in ['-s']:
                serial_port = a
            elif o in ['-n']:
                send_to_nimbits = False
            elif o in ['-c']:
                console = True
            else:
                usage()
                sys.exit(1)

        print 'Using serial port %s' % serial_port
        print 'Sending to nimbits: %s' % send_to_nimbits

        s = serial.serialposix.Serial(port=serial_port,
                                      baudrate=9600, bytesize=8, parity='N', stopbits=1,
                                      timeout=120,
                                      rtscts=1)

        s.open()

        time_track = 0

        pkt_reader = xbee_api.read_packet(s)
        while True:
            pkt = pkt_reader.next()

            adc0 = pkt.get_adc(0)
            adc1 = pkt.get_adc(1)
            temp_C = tmp36.get_t_from_adc(adc1)

            # res = thermistor.get_res_from_adc(adc1)
            # temp_C = thermistor.get_t(res)
            # temp_F = 32 + temp_C * 5 / 9

            # send to nimbits every 5 min
            if send_to_nimbits and (time.time() - time_track) > 300:
                send_nimbits('temp', temp_C)
                send_nimbits('Vbatt', adc0)
                time_track = time.time()

            report = 'packet_size=%d adc0=%.3f mV adc1=%.3f mV temp=%.1f C' % (
                pkt.packet_size, adc0, adc1, temp_C)

            if console:
                print report
            else:
                logger.info(report)


    except serial.SerialException,e:
        print e


if __name__ == '__main__':
    main()
