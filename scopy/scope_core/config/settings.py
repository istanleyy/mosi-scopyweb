"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

settings.py
    Settings for the Scope_Core modules
"""

import os
from scopy.settings import BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_config.xml')

JOBLIST_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_joblist.xml')

UNSYNC_MSG_PATH = os.path.join(BASE_DIR, 'scope_core/config/scope_msglog.xml')

QUEUE_MODE = 'bag'

# Valid connector types: fcsmysql, modbus
CONNECTOR = 'modbus'

DEVICE_INFO = {
    'ID': 'CCBRCS05',
    'NAME': 'Test Device'
}

SOCKET_SERVER = {
    'HOST': '',
    'PORT': 26674
};

SCOPE_SERVER = {
    'IP': 'http://192.168.2.28:3001/',
    'PATH': 'hmi-connection/hmi-messages'
}

DEBUG_SERVER = {
    'IP': 'http://requestb.in/',
    'PATH': '1fia5ul1'
}

MYSQL_CONFIG = {
    'user': 'Sniper',
    'password': 'MOSi0916',
    'host': '127.0.0.1',
    'port': '3307',
    'database': 'FCSTEST',
    'charset': 'utf8',
    'connection_timeout': 30
}

MODBUS_CONFIG = {
    'protocol': 'tcp',
    'slaveAddr': '127.0.0.1',
    'port': 1502,
    'ctrlRegAddr': 40001,
    'alarmRegAddr': 0,
    'dataRegAddr': 40011
}