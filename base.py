#!/usr/bin/python
#
#

import json
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
import xbee_api
import thermistor
import tmp36


MAIN_LOGFILE = '/var/tmp/xbee_base.log'
BATTERY_DATA_FILE = '/var/tmp/battery.log'
DATA_LOGGER_UPDATE_INTERVAL = 300  # 5 min
BATTERY_LOG_INTERVAL = 1800    # 30 min

PACHUBE_PRIVATE_FEED_KEY = 'WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g'
PACHUBE_FEED_ID = '55025'

logger = None


def send_pachube(data):
    """
    Send data to pachube.

    API docs:  https://pachube.com/docs/quickstart/

    Do not forget to create the feed using command

    curl --request POST --data '{"title":"XBee Sensor 1", "version":"1.0.0"}' --header "X-PachubeApiKey: WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g" --verbose http://api.pachube.com/v2/feeds

    This returns status code "201" ("feed created") and the url,
    including feed id

curl --request POST --data '{"title":"XBee Sensor 1", "version":"1.0.0"}' --header "X-PachubeApiKey: WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g" --verbose http://api.pachube.com/v2/feeds
* About to connect() to api.pachube.com port 80 (#0)
*   Trying 216.52.233.122... connected
* Connected to api.pachube.com (216.52.233.122) port 80 (#0)
> POST /v2/feeds HTTP/1.1
> User-Agent: curl/7.19.7 (i486-pc-linux-gnu) libcurl/7.19.7 OpenSSL/0.9.8k zlib/1.2.3.3 libidn/1.15
> Host: api.pachube.com
> Accept: */*
> X-PachubeApiKey: WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g
> Content-Length: 44
> Content-Type: application/x-www-form-urlencoded
> 
< HTTP/1.1 201 Created
< Date: Sat, 07 Apr 2012 15:59:28 GMT
< Content-Type: text/html; charset=utf-8
< Connection: keep-alive
< Location: http://api.pachube.com/v2/feeds/55025
< X-Pachube-Logging-Key: logging.Vi9ag7wY54Fdpmeor9i2
< X-PachubeRequestId: 6d43ae2264d491e21b824e2f4d151a81b843599a
< Cache-Control: no-cache
< Content-Length: 1
< Age: 0
< 
* Connection #0 to host api.pachube.com left intact
* Closing connection #0


    :param data: a dictionary, key is feed name, value is current value
    """
    pachube_json = json.dumps(
        {
            'version':'1.0.0',
            'datastreams':
                [{'id':k, 'current_value':float(v)}
                 for k,v in data.iteritems()]
            }
        )

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "X-PachubeApiKey": PACHUBE_PRIVATE_FEED_KEY,
               "Accept": "*/*"}
    try:
        conn = httplib.HTTPConnection("api.pachube.com")

        conn.request("PUT", "/v2/feeds/{0}".format(PACHUBE_FEED_ID), headers=headers, body=pachube_json)

        response = conn.getresponse()
        logger.info('Pachube update: response: %s %s' % (
                response.status, response.reason))
        if response.status != 200:
            logger.error(response.read())

    except socket.error, e:
        logger.error('%s: Pachube socket error: %s' % (datetime.datetime.now(), e))


def send_nimbits(name, value):
    assert isinstance(value, numbers.Real)

    # create dictionary
    data = {"email":"vadimk@gmail.com",
            "secret":"a8909970-e892-4bc4-afb8-7330d4d6ddc6",
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

            adc0 = float(pkt.get_adc(0))
            adc1 = float(pkt.get_adc(1))
            temp_C = tmp36.get_t_from_adc(adc1)

            # res = thermistor.get_res_from_adc(adc1)
            # temp_C = thermistor.get_t(res)
            # temp_F = 32 + temp_C * 5 / 9

            # send to data_logger every 5 min
            if time.time() >= data_logger_update_time:
                if send_to_data_logger:
                    send_pachube({'temp': temp_C, 'Vbatt': adc0})
#                    send_nimbits('temp', temp_C)
#                    send_nimbits('Vbatt', adc0)
                data_logger_update_time += DATA_LOGGER_UPDATE_INTERVAL

            if time.time() >= battery_log_time:
                record_battery_v(battery_file, adc0)
                battery_log_time += BATTERY_LOG_INTERVAL

            report = 'packet_size={0} adc0={1:.3f} mV adc1={2:.3f} mV T={3:.1f} C'.format(
                pkt.packet_size, adc0, adc1, temp_C)

            if console:
                print report
            else:
                logger.info(report)


    except serial.SerialException,e:
        print e


if __name__ == '__main__':
    main()
