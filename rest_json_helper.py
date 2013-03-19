"""
Simple helper function to do HTTP request to give URL and parse response
as a JSON document.

The main reason for this module is to isloate code working with urllib2.
In python 2.7 there is a connection leak in urllib2 which could cause
some long-term running REST API pollers to stop working.

See https://github.com/vzaliva/xbee_temp_sensor/issues/1 for details.
"""

import urllib2
import json
import subprocess

USE_URLLIB2 = False

def json_GET(endpoint, timeout):
    if USE_URLLIB2:
        f = urllib2.urlopen(endpoint, body, timeout)
        try:
            json_string = f.read()
        finally:
            f.close()
    else:
        json_string = subprocess.check_output(["curl", "-s", "-connect-timeout=%d" %timeout, endpoint])
    return json.loads(json_string)
        
 
