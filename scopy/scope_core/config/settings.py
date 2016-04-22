"""
Settings for the Scope_Core modules
"""

import os
from scopy.settings import BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_config.xml')

JOBLIST_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_joblist.xml')

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
    'PATH': '1kmeiw61'
}

MYSQL_CONFIG = {
    'user': 'Sniper',
    'password': 'MOSi0916',
    'host': '192.168.1.111',
    'port': '3307',
    'database': 'FCSTEST',
    'charset': 'utf8',
    'use_unicode': False,
    'connection_timeout': 30,
    'raise_on_warnings': True,
}