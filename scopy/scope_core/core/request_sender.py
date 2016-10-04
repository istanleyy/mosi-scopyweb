"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

request_sender.py
    Handles http reqeusts using the request module
"""

import requests
import logging
from scope_core.config import settings

logger = logging.getLogger('scopepi.messaging')

def sendPostRequest(msg, errHandle=False):
    global logger
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
        logger.info('-----> sending request to {0}'.foramt(url))
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        logger.info('<----- remote response: {0}'.format(r.content))
        if r.content == 'ServerMsg:no' or r.content == 'ServerMsg:fail' or r.content[:11] == 'ServerError':
            return (False, r.content)
        else:
            return (True, r.content)
    except requests.exceptions.RequestException as e:
        logger.exception('request_handler cannot send POST request to server.\n{0}'.format(msg))
        #print '\033[91m' + '[Scopy] Cannot send request to server!' + '\033[0m'
        return (None, 'RequestException')

def sendGetRequest():
    global logger
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        url = settings.SCOPE_SERVER['MSG_REPLY'] + settings.SCOPE_SERVER['PATH']
    
    param = {'station': settings.DEVICE_INFO['NAME']}
    try:
        logger.info('-----> sending request to {0}'.format(url))
        r = requests.get(url, params=param, timeout=15)
        logger.info('<----- remote response: {0}'.format(r.content))
        return r.content
    except requests.exceptions.RequestException as e:
        logger.exception('request_handler cannot send GET request to server.')
        return None

def sendBcastReply():
    global logger
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        url = settings.SCOPE_SERVER['BCAST_REPLY']
    
    try:
        logger.info('-----> sending request to {0}'.format(url))
        r = requests.get(url, timeout=15)
        logger.info('<----- remote response: {0}'.format(r.content))
        return r.content
    except requests.exceptions.RequestException as e:
        logger.exception('request_handler cannot reply to broadcast.')
        return None