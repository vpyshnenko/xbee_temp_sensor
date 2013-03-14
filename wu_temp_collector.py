#!/usr/bin/env python2.7
"""
This script collects temperature data from wunderground.com

It is using wu.cfg which is JSON dictionary with following fields:

{
"key":"your key"
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

"""

import json
import sys
import logging
import time,datetime
import string
import urllib2
import getopt


API_ENDPOINT="http://api.wunderground.com/api/%s/conditions/q/%s.json"
CFG_FILE="wu.cfg"
COSM_LOGFILE="cosm.log"
MAX_DATAPOINTS=490 # Max number of datapoints per post. COSM limit is 500
DATA_FILE = 'data_collector.csv'

def usage():
    print """
%s [-c] [-d]

-c -- log to console instead of log file
-d -- debug, dry-run mode. No data submitted, watermarks not modified.

"""  % sys.argv[0]

def read_watermark(watermark_fname):
    log.info("Reading watermark file %s" % watermark_fname)
    try:
        f=open(watermark_fname,"r")
        try:
            cfg = json.load(f)
            return cfg["maxtime"]
        finally:
            f.close()
    except:
        log.warning("Error reading watermark file %s. Assuming 0" % watermark_fname)
        return 0

def write_watermark(watermark_fname,w):
    global debug_mode
    if debug_mode:
        return
    log.info("Writing watermark file %s with value %s" % (watermark_fname,w))
    f=open(watermark_fname,"w")
    try:
        json.dump({"maxtime":w},f)
    finally:
        f.close()

def read_config(cfg_fname):
    log.info("Reading config file %s" % cfg_fname)
    f=open(cfg_fname,"r")
    try:
        return json.load(f)
    finally:
        f.close()

def submit_datapoints(feed,datastream,key,csv):
    if len(csv)==0:
        return
    log.debug("Writing %s bytes to %s/%s" % (len(csv),feed,datastream))
    if debug_mode:
        log.debug(csv)
        return
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request("http://api.cosm.com/v2/feeds/%s/datastreams/%s/datapoints.csv" % (feed,datastream), csv)
    request.add_header('Host','api.cosm.com')
    request.add_header('Content-type','text/csv')
    request.add_header('X-ApiKey', key)
    url = opener.open(request)

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
                            filename=COSM_LOGFILE, filemode='a')
    log = logging.getLogger('default')

    try:
        cfg=read_config(CFG_FILE)
    except:
        log.error("Error reading config file %s" % CFG_FILE)
        sys.exit(1)
        
    feed = cfg["feed"]
    key  = cfg["key"]
    log.info("Using feed %s" % feed)
    watermark = read_watermark(WATERMARK_FILE % feed)
    log.info("Using watermark %s" % watermark)

    f=open(DATA_FILE,"r")
    try:
        temps={}
        volts={}
        n={}
        for l in f:
            c = string.strip(l).split(",")
            w=float(c[0])
            if w>watermark:
                #  ISO 8601 date
                ts = datetime.datetime.utcfromtimestamp(int(w)).isoformat('T')+"Z"
                t = c[4] # temp
                v = c[5] # volts
                ch = int(c[1]) # channel
                if not (ch in n):
                    n[ch]=0
                    volts[ch]=""
                    temps[ch]=""
                temps[ch]+=string.join([ts,t],",") + "\r\n"
                volts[ch]+=string.join([ts,v],",")+ "\r\n"
                n[ch]+=1
                if n[ch]==MAX_DATAPOINTS:
                    for ch in n:
                        submit_datapoints(feed,ch,key,temps[ch])
                        # Voltage datastream is 100+temp datasteam
                        submit_datapoints(feed,ch+100,key,volts[ch])
                    write_watermark(WATERMARK_FILE % feed,w)
                    watermark = w
                    temps={}
                    volts={}
                    n={}

        for ch in n:
            submit_datapoints(feed,ch,key,temps[ch])
            # Voltage datastream is 100+temp datasteam
            submit_datapoints(feed,ch+100,key,volts[ch])
        write_watermark(WATERMARK_FILE % feed,w)
            
    finally:
        f.close()



if __name__ == '__main__':
    main()
