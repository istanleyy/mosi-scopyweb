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

def sendPostRequest(msg, contenttype='xml'):
    #url = settings.DEBUG_SERVER['IP'] + settings.DEBUG_SERVER['PATH']
    url = settings.SCOPE_SERVER['IP'] + settings.SCOPE_SERVER['PATH']
    if contenttype == 'xml':
        headers = {'Content-Type': 'text/xml'}
    else:
        headers = {'Content-Type': 'text/plain'}
    
    try:
        print '-----> sending request...'
        r = requests.post(url, data=msg, headers=headers)
        print '<----- remote response: ' + r.content
        return True
    except requests.exceptions.RequestException as e:
        print e
        print '\033[91m' + '[Scopy] Cannot send request to server!' + '\033[0m'
        return False

def sendGetRequest():
    url = settings.SCOPE_SERVER['IP'] + settings.SCOPE_SERVER['PATH']
    try:
        print '-----> sending request...'
        r = requests.get(url)
        print '<----- remote response: ' + r.content
        return r.content
    except requests.exceptions.RequestException as e:
        print e
        return None