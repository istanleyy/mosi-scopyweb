"""
Settings for the Scope_Core modules
"""

import os
from scopy.settings import BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_config.xml')

JOBLIST_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_joblist.xml')

UNSYNC_MSG_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_msglog.xml')

QUEUE_MODE = 'bag'

DEVICE_INFO = {
    'ID': 'CCBRCS05',
    'NAME': 'Test Device'
}

SOCKET_SERVER = {
    'HOST': '',
    'PORT': 26674
};

SCOPE_SERVER = {
    'IP': 'http://requestb.in/',
    'PATH': '1n8wlw31'
}

MYSQL_CONFIG = {
    'user': 'Sniper',
    'password': 'MOSi0916',
    'host': '127.0.0.1',
    'port': '3307',
    'database': 'FCSTEST',
    'charset': 'utf8',
    'connection_timeout': 30,
}