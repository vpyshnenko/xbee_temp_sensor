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
import time

CFG_FILE="cosm.cfg"
WATERMARK_FILE="cosm.%s.watermark"
COSM_LOGFILE="cosm.log"

def read_watermark(watermark_fname):
    log.error("Reading watermark file %s" % watermark_fname)
    try:
        f=open(watermark_fname,"r")
        try:
            cfg = json.load(f)
            return cfg["maxtime"]
        finally:
            f.close()
    except:
        log.warning("Error reading watermark file %s. Assuming 0" % CFG_FILE)
        return 0

def read_config(cfg_fname):
    log.info("Reading config file %s" % cfg_fname)
    f=open(CFG_FILE,"r")
    try:
        return json.load(f)
    finally:
        f.close()
        
def main():
    global log

    log_format = '%(asctime)s %(process)d %(filename)s:%(lineno)d %(levelname)s %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        filename=COSM_LOGFILE,
                        filemode='w')

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

    print feed,key,watermark




if __name__ == '__main__':
    main()