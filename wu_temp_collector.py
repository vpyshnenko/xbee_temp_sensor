#!/usr/bin/env python2.7
"""
This script collects temperature data from wunderground.com

It is using wu.cfg which is JSON dictionary with following required fields:

{
"key":"your key",
"location":"location query"
}

The query specifies location for which you want weather information. Examples:

CA/San_Francisco	US state/city
60290	US zipcode
Australia/Sydney	country/city
37.8,-122.4	latitude,longitude
KJFK	airport code
pws:KCASANFR70	PWS id
autoip	AutoIP address location
autoip.json?geo_ip=38.102.136.138	specific IP address location

The script writes CSV file wu.csv with the following fields:

1. current time (unix timestamp)
2. observation time (as reported by API)
3. temperature in C (as reported by API)

Additionaly, config file might contain following fields

"cosm": {
"key":"your key"
"feed":123
"datastream":123
}

If they present, it will additionally submit data to COSM.com to specified
feed and datastream.

"""

import json
import sys
import logging
import time,datetime
import string
from urllib import quote_plus
import getopt

import cosm
from rest_json_helper import json_REST


API_ENDPOINT="http://api.wunderground.com/api/%s/conditions/q/%s.json"
CFG_FILE="wu.cfg"
WU_LOGFILE="wu.log"
DATA_FILE = 'wu.csv'
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
                            filename=WU_LOGFILE, filemode='a')
    log = logging.getLogger('default')

    try:
        cfg = read_config(cfg_fname)
    except Exception, ex:
        log.error("Error reading config file %s" % ex)
        sys.exit(1)
        
    key  = cfg["key"]
    query = cfg["location"]
    log.info("Using query %s" % query)

    if cfg.has_key("cosm"):
        cosm_feed = cfg["cosm"]["feed"]
        cosm_key  = cfg["cosm"]["key"]
        cosm_datastream  = cfg["cosm"]["datastream"]
        log.debug("Will log to COSM %s/%s" % (cosm_feed, cosm_datastream))
    
    if not debug_mode:
        data_file = file(data_fname, 'a')
        
    try:
        while True:
            try:
                parsed_json = json_REST(API_ENDPOINT % (quote_plus(key), quote_plus(query)),
                                        None, API_TIMEOUT)
                local_time= time.time()
                observation_time = int(parsed_json['current_observation']['observation_epoch'])
                temp_c = parsed_json['current_observation']['temp_c']
                log.info("Current temperature is: %s" % temp_c)
            except Exception, ex:
                log.error("Error fetching data from API: %s" %ex)
                continue

            csv_report = '{0},{1},{2}\n'.format(local_time,observation_time,temp_c)

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
                    try:
                        ts = datetime.datetime.utcfromtimestamp(int(local_time)).isoformat('T')+"Z"
                        cosm_report =string.join([ts,str(temp_c)],",") + "\r\n"
                        cosm.submit_datapoints(cosm_feed,cosm_datastream,cosm_key,cosm_report)
                    except Exception, ex:
                        # Error sending to COSM is non-fatal, but logged anyway
                        log.error("Error sending to COSM: %s" % ex )

            if sleep_time>0:
                time.sleep(sleep_time)
            else:
                break
    finally:
        if not debug_mode:
            data_file.close();

if __name__ == '__main__':
    main()
