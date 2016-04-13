"""
Settings for the Scope_Core modules
"""

import os
from scopy.settings import BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_config.xml')

JOBLIST_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_joblist.xml')

DEVICE_INFO = {
    'ID': 'XYZ000000',
    'NAME': 'Test Device'
}

SOCKET_SERVER = {
    'HOST': '',
    'PORT': 26674
};

SCOPE_SERVER = {
    'IP': 'http://requestb.in/',
    'PATH': '14qlwtd1'
}

MYSQL_CONFIG = {
    'user': 'Sniper',
    'password': 'MOSi0916',
    'host': '172.19.16.66',
    'port': '3307',
    'database': 'FCSTEST',
    'connection_timeout': 30,
    'raise_on_warnings': True,
}