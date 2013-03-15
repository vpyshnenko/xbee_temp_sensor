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
import getopt
import cosm

CFG_FILE="cosm.cfg"
WATERMARK_FILE="cosm.%s.watermark"
COSM_LOGFILE="cosm.log"
MAX_DATAPOINTS=490 # Max number of datapoints per post. COSM limit is 500
DATA_FILE = 'data_collector.csv'

def usage():
    print """
%s [-f <cfg file>] [-c] [-d] [-i <csv file>]

-c -- log to console instead of log file
-d -- debug, dry-run mode. No data submitted, watermarks not modified.
-f <cfg file> -- config file name. Default is '%s'
-i <csv file> -- CSV file name. Default is '%s'

"""  % (sys.argv[0],CFG_FILE,DATA_FILE)

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

def main():
    global log
    global debug_mode

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dcf:i:', [])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    console = False
    debug_mode = False
    cfg_fname = CFG_FILE
    data_fname = DATA_FILE
    
    for o, a in opts:
        if o in ['-d']:
            debug_mode = True
        elif o in ['-c']:
            console = True
        elif o in ['-f']:
            cfg_fname = a
        elif o in ['-i']:
            data_fname = a
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
        cfg=read_config(cfg_fname)
    except:
        log.error("Error reading config file %s" % cfg_fname)
        sys.exit(1)
        
    feed = cfg["feed"]
    key  = cfg["key"]
    log.info("Using feed %s" % feed)
    watermark = read_watermark(WATERMARK_FILE % feed)
    log.info("Using watermark %s" % watermark)

    f=open(data_fname,"r")
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
                        cosm.submit_datapoints(feed,ch,key,temps[ch])
                        # Voltage datastream is 100+temp datasteam
                        cosm.submit_datapoints(feed,ch+100,key,volts[ch])
                    write_watermark(WATERMARK_FILE % feed,w)
                    watermark = w
                    temps={}
                    volts={}
                    n={}

        for ch in n:
            cosm.submit_datapoints(feed,ch,key,temps[ch])
            # Voltage datastream is 100+temp datasteam
            cosm.submit_datapoints(feed,ch+100,key,volts[ch])
        write_watermark(WATERMARK_FILE % feed,w)
            
    finally:
        f.close()



if __name__ == '__main__':
    main()
