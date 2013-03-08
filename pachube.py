

"""

        API docs:  https://pachube.com/docs/quickstart/

        Do not forget to create the feed using command

        curl --request POST --data '{"title":"XBee Sensor 1", "version":"1.0.0"}' --header "X-PachubeApiKey: WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g" --verbose http://api.pachube.com/v2/feeds

        This returns status code "201" ("feed created") and the url,
        including feed id

    curl --request POST --data '{"title":"XBee Sensor 1", "version":"1.0.0"}' --header "X-PachubeApiKey: WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g" --verbose http://api.pachube.com/v2/feeds
    * About to connect() to api.pachube.com port 80 (#0)
    *   Trying 216.52.233.122... connected
    * Connected to api.pachube.com (216.52.233.122) port 80 (#0)
    > POST /v2/feeds HTTP/1.1
    > User-Agent: curl/7.19.7 (i486-pc-linux-gnu) libcurl/7.19.7 OpenSSL/0.9.8k zlib/1.2.3.3 libidn/1.15
    > Host: api.pachube.com
    > Accept: */*
    > X-PachubeApiKey: WEUcLNOl6Myth65O73einj2inPCSAKw2MCtHc1l5QlI5UT0g
    > Content-Length: 44
    > Content-Type: application/x-www-form-urlencoded
    > 
    < HTTP/1.1 201 Created
    < Date: Sat, 07 Apr 2012 15:59:28 GMT
    < Content-Type: text/html; charset=utf-8
    < Connection: keep-alive
    < Location: http://api.pachube.com/v2/feeds/55025
    < X-Pachube-Logging-Key: logging.Vi9ag7wY54Fdpmeor9i2
    < X-PachubeRequestId: 6d43ae2264d491e21b824e2f4d151a81b843599a
    < Cache-Control: no-cache
    < Content-Length: 1
    < Age: 0
    < 
    * Connection #0 to host api.pachube.com left intact
    * Closing connection #0

"""

import datetime
import json
import httplib
import urllib
import sys
import logging
import time
import re
import socket

logger = logging.getLogger('default')


def chunker(list_of_things, chunk_size):
    """
    Generator function that returns "chunks" of  the given list.

    :param list_of_things: the list it should work with
    :param chunk_size: maximum size of the returned chunk

    :returns: a list of the same things which is a part of the original list.
    """
    idx = 0
    while idx < len(list_of_things):
        yield list_of_things[idx:idx+chunk_size]
        idx += chunk_size


class PachubeFeed(object):

    def __init__(self, feed_id, key):
        self.feed_key = key
        self.feed_id = feed_id
        self.feed_url = "/v2/feeds/{0}".format(self.feed_id)

    def datastream_update(self, data):
        """
        Send data to pachube.

        :param data: a dictionary, key is feed name, value is current value
        """
        pachube_json = json.dumps(
            {
                'version':'1.0.0',
                'datastreams':
                    [{'id':k, 'current_value':float(v)}
                     for k,v in data.iteritems()]
                }
            )

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "X-PachubeApiKey": self.feed_key,
                   "Accept": "*/*"}
        try:
            conn = httplib.HTTPConnection("api.pachube.com")

            conn.request("PUT", self.feed_url, headers=headers, body=pachube_json)

            response = conn.getresponse()
            logger.info('Pachube update: response: %s %s' % (
                    response.status, response.reason))
            if response.status != 200:
                logger.error(response.read())

        except socket.error, e:
            logger.error('%s: Pachube socket error: %s' % (datetime.datetime.now(), e))
        except httplib.HTTPException, e:
            logger.error('%s: Pachube http error: %s' % (datetime.datetime.now(), e))

    def datapoint_create(self, datastream, data):
        """
        Send data to pachube.

        :param datastream: datastream name
        :param data: a list of datapoint dictionaries:

  [
    {"at":"2010-05-20T11:01:43Z","value":"294"},
    {"at":"2010-05-20T11:01:44Z","value":"295"},
    {"at":"2010-05-20T11:01:45Z","value":"296"},
    {"at":"2010-05-20T11:01:46Z","value":"297"}
  ]

        """
        pachube_json = json.dumps({'datapoints': data})
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "X-PachubeApiKey": self.feed_key,
                   "Accept": "*/*"}
        url = '{0}/datastreams/{1}/datapoints'.format(self.feed_url, datastream)
        try:
            conn = httplib.HTTPConnection("api.pachube.com")
            conn.request("POST", url, headers=headers, body=pachube_json)
            response = conn.getresponse()
            logger.info('Pachube update: response: %s %s' % (
                    response.status, response.reason))
            if response.status != 200:
                logger.error(response.read())
        except socket.error, e:
            logger.error('%s: Pachube socket error: %s' % (datetime.datetime.now(), e))


if __name__ == '__main__':
    """
    Just read file data_points.txt and create historical data points in the same feed

    """
    PACHUBE_FEED_ID = '55025'
    DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    log_format = '%(asctime)s %(process)d %(filename)s:%(lineno)d %(levelname)s %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        filemode='w')
    logger = logging.getLogger('default')

    pachube_feed = PachubeFeed(feed_id=PACHUBE_FEED_ID)

    data_list = []
    with open('data_points.txt', 'r') as f:
        for line in f:
            line = line.strip().split(' ')
            time_str = ' '.join(line[0:2])
            timestamp = time.mktime(
                time.strptime(time_str, DATE_TIME_FORMAT)) + time.altzone
            dt = datetime.datetime.fromtimestamp(timestamp)
            isodt = dt.isoformat()
            isodt = re.sub('\.[0-9]+$', '', isodt)
            data_list.append({'at': isodt, 'value': float(line[2])})


    chunk_num = 1
    chunk_generator = chunker(data_list, 5)
    for chunk in chunk_generator:
        print 'chunk #{0}: {1}'.format(chunk_num, chunk)
        pachube_feed.datapoint_create('Vbatt', chunk)
        chunk_num += 1
        time.sleep(1)

            
