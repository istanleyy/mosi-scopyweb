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
from scope_core.config import settings

def sendPostRequest(msg):
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        url = settings.SCOPE_SERVER['IP'] + settings.SCOPE_SERVER['PATH']
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        'station': settings.DEVICE_INFO['NAME'],
        'message': msg
    }
    try:
        print '-----> sending request...'
        r = requests.post(url, json=payload, headers=headers)
        print '<----- remote response: ' + r.content
        return True
    except requests.exceptions.RequestException as e:
        print e
        print '\033[91m' + '[Scopy] Cannot send request to server!' + '\033[0m'
        return False

def sendGetRequest():
    if settings.DEBUG:
        url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    else:
        url = settings.SCOPE_SERVER['IP'] + settings.SCOPE_SERVER['PATH']
    
    param = {'station': settings.DEVICE_INFO['NAME']}
    try:
        print '-----> sending request...'
        r = requests.get(url, params=param)
        print '<----- remote response: ' + r.content
        return r.content
    except requests.exceptions.RequestException as e:
        print e
        return None