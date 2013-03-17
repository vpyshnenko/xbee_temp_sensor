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
CFG_FILE="sensors.cfg"
DATA_FILE = 'data_collector.csv'
LOCK_FILE='xbee_sensor_monitor.lock'
SERIAL_PORT= '/dev/ttyUSB0'

log = None
global_lock = lockfile.FileLock(LOCK_FILE)

# Default values for VREF and Battery volage divider. Could be overriden in config
VREF = 3221 # LM 7833
BATTERY_K=4.43/0.892 # Voldate divider from Vcc to ADC1

def cleanup():
    global log
    if log:
        log.info("Stop")
    if global_lock.is_locked():
        global_lock.release()

def usage():
    print """
%s [-s <port>] [-f <cfg file>] [-c] [-d] [-o <csv file>]

-s <port> -- use serial port <port>. Default is' %s'
-f <cfg file> -- config file name. Default is '%s'
-c -- log to console instead of log file
-d -- debug mode, do not update csv (more logging)
-o <csv file> -- CSV file name. Default is '%s'

"""  % (sys.argv[0], SERIAL_PORT, CFG_FILE, DATA_FILE)

def read_config(cfg_fname):
    log.info("Reading config file %s" % cfg_fname)
    f=open(cfg_fname,"r")
    try:
        return json.load(f)
    finally:
        f.close()

def get_adc_v(pkt, adc_idx,vref):
    "Retruns ADC value in volts"
    return float(pkt.get_adc(adc_idx))*vref/(pkt.num_samples * 1023.0)

def get_battery_from_adc(v,k):
    return k*v

def main():
    global log

    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'cdf:s:o:', [])
        except getopt.GetoptError:
            usage()
            sys.exit(2)

        try:
            # timeout=0 causes it to raise AlreadyLocked. Any timeout >0
            # causes LockTimeout
            global_lock.acquire(timeout=0)
        except lockfile.AlreadyLocked:
            log.error('Another copy of this program is running')
            sys.exit(1)

        atexit.register(cleanup)

        console = False
        debug_mode = False
        port = SERIAL_PORT;
        cfg_fname = CFG_FILE
        data_fname = DATA_FILE
        
        for o, a in opts:
            if o in ['-s']:
                port = a
            elif o in ['-f']:
                cfg_fname = a
            elif o in ['-o']:
                data_fname = a
            elif o in ['-c']:
                console = True
            elif o in ['-d']:
                debug_mode = True
            else:
                usage()
                sys.exit(1)

        log_format = '%(asctime)s %(process)d %(filename)s:%(lineno)d %(levelname)s %(message)s'
        if debug_mode:
            log_level=logging.DEBUG
        else:
            log_level=logging.INFO
        if console:
            logging.basicConfig(level=log_level, format=log_format)
        else:
            logging.basicConfig(level=log_level, format=log_format,
                                filename=MAIN_LOGFILE, filemode='a')
        log = logging.getLogger('default')

        try:
            cfg = read_config(cfg_fname)
        except Exception, ex:
            log.error("Error reading config file %s" % ex)
            sys.exit(1)

        log.info('Using serial port %s' % port)

        s = serial.serialposix.Serial(port=port,
                                      baudrate=9600, bytesize=8, parity='N', stopbits=1,
                                      timeout=120,
                                      rtscts=1)

        log.info("Starting collection")

        data_file = file(data_fname, 'a')

        pkt_reader = xbee_api.read_packet(s)
        while True:
            pkt = pkt_reader.next()

            try:

                sensor_address = str(pkt.address)
                try:
                    scfg = cfg[sensor_address]
                    vref = scfg["vref"]
                    battery_k = scfg["vccK"]
                except KeyError:
                    log.warning("No config for sensor '%s'. Using defaults" % sensor_address)
                    vref = VREF
                    battery_k = BATTERY_K
                    
                radc0 = pkt.get_adc(0)
                radc1 = pkt.get_adc(1)
                adc0 = float(get_adc_v(pkt,0,vref))
                adc1 = float(get_adc_v(pkt,1,vref))
                battery_V = get_battery_from_adc(adc1,battery_k)/1000.0
                temp_C = tmp36.get_t_from_adc(adc0)

                log.info('A={0} T={1:.1f}C V={2:.3f}V'.format(
                    pkt.address,
                    temp_C, battery_V))

                csv_report = '{0},{1},{2},{3},{4:.1f},{5:.3f}\n'.format(
                    time.time(), pkt.address, radc0, radc1, temp_C, battery_V*1000.0)

                if not debug_mode:
                    try:
                        data_file.write(csv_report)
                        data_file.flush()
                    except IOError, ex:
                        log.error("Error writing CSV file: %s" % ex)
                    
            except IndexError, e:
                # I get this from pkt.get_adc() when packet is broken
                log.error('Broken XBee packet: "{0}"'.format(pkt))


    except serial.SerialException, ex:
        log.debug("Serial error %s" % ex)

if __name__ == '__main__':
    main()
