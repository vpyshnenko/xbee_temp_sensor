#!/usr/bin/env python2.7
"""
This script collects temperature data from wireless theromostat by https://radiothermostat.com/

It is using radiothermostat.cfg which is JSON dictionary with following required fields:

{
"IP":"theromostat IP address or host name",
}

The script writes CSV file radiothermostat.csv with the following fields:

1. current time (unit timestamp)
2. temperature in C (as reported by API)
3. HVAC operating state (0-OFF, 1-HEAT, -1-COOL)
4. Fan state (0-OFF, 1-ON)

Additionaly, config file might contain following fields

"cosm": {
"key":"your key",
"feed":123,
"temp_datastream":10,
"tstate_datastream":20,
"fstate_datastream":30
}

If they present, it will additionally submit data to COSM.com to specified
feed and datastreams.

"""

import json
import sys
import logging
import time,datetime
import string
import urllib2,urllib
import getopt
import cosm


API_ENDPOINT="http://%s/tstat"
CFG_FILE="radiothermostat.cfg"
RT_LOGFILE="radiothermostat.log"
DATA_FILE = 'radiothermostat.csv'
API_TIMEOUT=5

def usage():
    print """
%s [-f <cfg file>] [-c] [-d] [-o <csv file>] [-t seconds]

-c -- log to console instead of log file
-d -- debug, dry-run mode. No data written or sent.
-f <cfg file> -- config file name. Default is '%s'
-o <csv file> -- CSV file name. Default is '%s'
-t <seconds> -- Loop mode: query every 't' seconds. (off by default)

"""  % (sys.argv[0], CFG_FILE, DATA_FILE)

def read_config(cfg_fname):
    log.info("Reading config file %s" % cfg_fname)
    f=open(cfg_fname,"r")
    try:
        return json.load(f)
    finally:
        f.close()

def main():
    global log
    global debug_mode

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dcf:o:t:', [])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    console = False
    debug_mode = False
    cfg_fname = CFG_FILE
    data_fname = DATA_FILE
    sleep_time = 0 # non zero means loop mode
    
    for o, a in opts:
        if o in ['-d']:
            debug_mode = True
        elif o in ['-c']:
            console = True
        elif o in ['-f']:
            cfg_fname = a
        elif o in ['-o']:
            data_fname = a
        elif o in ['-t']:
            sleep_time = int(a)
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
                            filename=RT_LOGFILE, filemode='a')
    log = logging.getLogger('default')

    try:
        cfg = read_config(cfg_fname)
    except Exception, ex:
        log.error("Error reading config file %s" % ex)
        sys.exit(1)
        
    ip  = cfg["IP"]
    log.info("Thermosat IP %s" % ip)

    if cfg.has_key("cosm"):
        cosm_feed = cfg["cosm"]["feed"]
        cosm_key  = cfg["cosm"]["key"]
        cosm_temp_datastream  = cfg["cosm"]["temp_datastream"]
        cosm_tstate_datastream  = cfg["cosm"]["tstate_datastream"]
        cosm_fstate_datastream  = cfg["cosm"]["fstate_datastream"]
        log.debug("Will log to COSM feed %s", cosm_feed)
    
    if not debug_mode:
        data_file = file(data_fname, 'a')
        
    try:
        while True:
            try:
                f = urllib2.urlopen(API_ENDPOINT % ip, None, API_TIMEOUT)
                try:
                    json_string = f.read()
                    parsed_json = json.loads(json_string)
                    local_time= time.time()
                    temp_f = float(parsed_json['temp'])
                    temp_c = (temp_f-32.0)*5.0/9.0
                    temp_cs = "{:.1f}".format(temp_c)
                    tstate = int(parsed_json['tstate'])
                    fstate = int(parsed_json['fstate'])
                    if tstate==2:
                        tstate=-1
                    s = "Current temperature is: " + temp_cs
                    if fstate:
                        s+=" Fan in ON."
                    else:
                        s+=" Fan in OFF."
                    if tstate==0:
                        s+=" HVAC is OFF."
                    elif tstate==1:
                        s+=" HVAC is heating."
                    else:
                        s+=" HVAC is cooling."
                    log.info(s)
                except Exception, ex:
                    log.error("Error fetching data from API: %s" % ex)
                    next
                finally:
                    f.close()
            except Exception, ex:
                log.error("Error fetching connecting to API: %s" %ex)
                next

            csv_report = '{0},{1:.3f},{2},{3}\n'.format(local_time,temp_c,tstate,fstate)

            if debug_mode:
                print csv_report
            else:
                # Write to file
                try:
                    data_file.write(csv_report)
                    data_file.flush()
                except IOError, ex:
                    # Error writing CSV is fatal
                    log.error("Error writing CSV file: %s" % ex)
                    sys.exit(1)
                    
                # Send to COSM
                if cfg.has_key("cosm"):
                    data = {cosm_temp_datastream:temp_cs,
                            cosm_tstate_datastream:tstate,
                            cosm_fstate_datastream:fstate
                            }
                    ts = datetime.datetime.utcfromtimestamp(int(local_time)).isoformat('T')+"Z"
                    for ds in data:
                        try:
                            cosm_report =string.join([ts,str(data[ds])],",") + "\r\n"
                            cosm.submit_datapoints(cosm_feed,ds,cosm_key,cosm_report)
                        except Exception, ex:
                            # Error sending to COSM is non-fatal, but logged
                            log.warning("Error sending to COSM datastream %s. %s" % (ds,ex))

            if sleep_time>0:
                time.sleep(sleep_time)
            else:
                break
    finally:
        if not debug_mode:
            data_file.close();

if __name__ == '__main__':
    main()
