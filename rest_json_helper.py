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

def json_REST(endpoint, body, timeout):
    f = urllib2.urlopen(endpoint, body, timeout)
    try:
        json_string = f.read()
        return json.loads(json_string)
    finally:
        f.close()
 
