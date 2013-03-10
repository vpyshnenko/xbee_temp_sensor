#!/usr/bin/env python2.7
"""
This script will read CSV file with sensor data and will post to COSM.com

It is using cosm.cfg which is JSON dictionary with following fields:

{
"key":"your key"
"feed":123
}
"""

import json
import sys
import logging
import time,datetime
import string
import urllib2

CFG_FILE="cosm.cfg"
WATERMARK_FILE="cosm.%s.watermark"
COSM_LOGFILE="cosm.log"
MAX_DATAPOINTS=300 # Max number of datapoints per post. COSM limit is 500
DATA_FILE = 'data_collector.csv'

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
    log.info("Writing watermark file %s with value %s" % (watermark_fname,w))
    f=open(watermark_fname,"w")
    try:
        json.dump({"maxtime":w},f)
    finally:
        f.close()

def read_config(cfg_fname):
    log.info("Reading config file %s" % cfg_fname)
    f=open(CFG_FILE,"r")
    try:
        return json.load(f)
    finally:
        f.close()

def submit_datapoints(feed,datastream,key,csv):
    log.debug("Writing %s bytes to %s/%s" % (len(csv),feed,datastream))
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request("http://api.cosm.com/v2/feeds/%s/datastreams/%s/datapoints.csv" % (feed,datastream), csv)
    request.add_header('Host','api.cosm.com')
    request.add_header('Content-type','text/csv')
    request.add_header('X-ApiKey', key)
    url = opener.open(request)

def main():
    global log

    log_format = '%(asctime)s %(process)d %(filename)s:%(lineno)d %(levelname)s %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        filename=COSM_LOGFILE,
                        filemode='a')

    log = logging.getLogger('default')
    log.setLevel(logging.DEBUG)

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
        temps=""
        volts=""
        n=0
        for l in f:
            c = string.strip(l).split(",")
            w=float(c[0])
            if w>watermark:
                ts = datetime.datetime.fromtimestamp(w).isoformat('T')
                t = c[4] # temp
                v = c[5] # volts
                ch = int(c[1]) # channel
                temps+=string.join([ts,t],",") + "\n"
                volts+=string.join([ts,v],",")+ "\n"
                n=n+1
                if n==MAX_DATAPOINTS:
                    submit_datapoints(feed,ch,key,temps)
                    # Voltage datastream is 100+temp datasteam
                    submit_datapoints(feed,ch+100,key,volts)
                    write_watermark(WATERMARK_FILE % feed,w)
                    watermark = w
                    temps=""
                    volts=""
                    n=0
                
        if len(temps) or len(volts):
            if len(volts):
                submit_datapoints(feed,ch+100,key,volts)
            if len(temps):
                submit_datapoints(feed,ch,key,temps)
            write_watermark(WATERMARK_FILE % feed,w)
            
    finally:
        f.close()



if __name__ == '__main__':
    main()
