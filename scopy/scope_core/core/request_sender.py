"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

request_sender.py
    Handles http reqeusts using the request module
"""

import logging
import requests
from scope_core.config import settings

logger = logging.getLogger('scopepi.messaging')

def rawGet(dest="", **kwargs):
    """rawGet function is used to send generic get request to server.

    dest - where to send the request.
    kwargs - provided key value pairs will be the parameters of the request.
    """
    url = dest
    param = {}
    for key in kwargs:
        param[key] = kwargs[key]

    try:
        logger.info('-----> sending request to {0}'.format(url))
        r = requests.get(url, params=param, timeout=15)
        logger.info('<----- remote response: {0}'.format(r.content))
        if r.status_code == 404:
            return r.status_code
        return r.content
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
        logger.exception('request_handler cannot send GET request to server.')
        return None

def sendPostRequest(msg, errHandle=False):
    """Sends a POST message to the server. Used for Scope job event and update messages."""
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        if errHandle:
            url = settings.SCOPE_SERVER['MSG_REPLY'] + settings.SCOPE_SERVER['ERR_HANDLE']
        else:
            url = settings.SCOPE_SERVER['MSG_REPLY'] + settings.SCOPE_SERVER['PATH']

    headers = {'Content-Type': 'application/json'}
    payload = {
        'station': settings.DEVICE_INFO['NAME'],
        'message': msg
    }
    try:
        logger.info('-----> sending request to {0}'.format(url))
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        logger.info('<----- remote response: {0}'.format(r.content))
        if r.content == 'ServerMsg:no' or r.content == 'ServerMsg:fail' or r.content[:11] == 'ServerError':
            return (False, r.content)
        else:
            return (True, r.content)
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
        logger.exception('request_handler cannot send POST request to server.')
        #print '\033[91m' + '[Scopy] Cannot send request to server!' + '\033[0m'
        return (None, 'RequestException')

def sendGetRequest(job="", user=""):
    """Get request is used to get job information from server.

    job - the serial number of the job that we want the information for.
    user - the id of the user initiated this request.
    """
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        url = settings.SCOPE_SERVER['MSG_REPLY'] + settings.SCOPE_SERVER['PATH']

    param = {
        'station': settings.DEVICE_INFO['NAME'],
        'job': job,
        'user': user
    }
    try:
        logger.info('-----> sending request to {0}'.format(url))
        r = requests.get(url, params=param, timeout=15)
        logger.info('<----- remote response: {0}'.format(r.content))
        return r.content
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
        logger.exception('request_handler cannot send GET request to server.')
        return None

def sendBcastReply():
    """Send reply as a broadcast message."""
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        url = settings.SCOPE_SERVER['BCAST_REPLY']

    try:
        logger.info('-----> sending request to {0}'.format(url))
        r = requests.get(url, timeout=30)
        logger.info('<----- remote response: {0}'.format(r.content))
        return r.content
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
        logger.exception('request_handler cannot reply to broadcast.')
        return None
