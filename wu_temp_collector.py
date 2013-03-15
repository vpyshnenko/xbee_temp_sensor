#!/usr/bin/env python2.7
"""
This script collects temperature data from wunderground.com

It is using wu.cfg which is JSON dictionary with following fields:

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

1. current time
2. observation time (as reported by API)
3. temperature in C (as reported by API)

"""

import json
import sys
import logging
import time,datetime
import string
import urllib2,urllib
import getopt


API_ENDPOINT="http://api.wunderground.com/api/%s/conditions/q/%s.json"
CFG_FILE="wu.cfg"
WU_LOGFILE="wu.log"
DATA_FILE = 'wu.csv'

def usage():
    print """
%s [-c] [-d]

-c -- log to console instead of log file
-d -- debug, dry-run mode. No data written

"""  % sys.argv[0]

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
        opts, args = getopt.getopt(sys.argv[1:], 'dc', [])

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    console = False
    debug_mode = False

    for o, a in opts:
        if o in ['-d']:
            debug_mode = True
        elif o in ['-c']:
            console = True
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
        cfg=read_config(CFG_FILE)
    except:
        log.error("Error reading config file %s" % CFG_FILE)
        sys.exit(1)
        
    key  = cfg["key"]
    query = cfg["location"]
    log.info("Using query %s" % query)

    try:
        f = urllib2.urlopen(API_ENDPOINT % (urllib.quote_plus(key), urllib.quote_plus(query)))
        try:
            json_string = f.read()
            parsed_json = json.loads(json_string)
            local_time= time.time()
            observation_time = int(parsed_json['current_observation']['observation_epoch'])
            temp_c = parsed_json['current_observation']['temp_c']
            log.info("Current temperature is: %s" % temp_c)
        except:
            log.error("Error fetching data from API")
            sys.exit(1)
        finally:
            f.close()
    except:
        log.error("Error fetching connecting to API")
        sys.exit(1)

    csv_report = '{0},{1},{2}\n'.format(local_time,observation_time,temp_c)

    if debug_mode:
        print csv_report
    else:
        data_file = file(DATA_FILE, 'a')
        try:
            data_file.write(csv_report)
            data_file.flush()
        except:
            log.error("Error writing cfg file")
            sys.exit(1)
        finally:
            data_file.close();

if __name__ == '__main__':
    main()
