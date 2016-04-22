import requests
from scope_core.config import settings

def sendHttpRequest(msg, contenttype='xml'):
    url = settings.SCOPE_SERVER['IP'] + settings.SCOPE_SERVER['PATH']
    if contenttype == 'xml':
        headers = {'Content-Type': 'application/xml'}
    else:
        headers = {'Content-Type': 'text/plain'}
    
    try:
        print '-----> sending request...'
        r = requests.post(url, data={'data': msg}, headers=headers)
        print '<----- remote response: ' + r.content
    except requests.exceptions.RequestException as e:
        print e