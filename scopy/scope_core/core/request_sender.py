import requests
from scope_core.config import settings

def sendHttpRequest(msg):
    url = settings.SCOPE_SERVER['IP'] + settings.SCOPE_SERVER['PATH']
    headers = {'Content-Type': 'application/xml'}
    r = requests.post(url, data={'data': msg}, headers=headers)
    print '<----- received: ' + r.content