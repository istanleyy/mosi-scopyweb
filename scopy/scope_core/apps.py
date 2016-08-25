from __future__ import unicode_literals

import sys
from thread import *
from django.apps import AppConfig
from scope_core.config import settings

class ScopeCoreConfig(AppConfig):
    name = 'scope_core'
    verbose_name = 'Scope Device Adapter'
    
    def ready(self):
        from .tasks import pollDeviceStatus
        from core import job_control
        from core import device_manager as device
        from core.socket_server import SocketServer

        job_control.modelCheck()
        socketServer = SocketServer()
        socketServer.start()
        scopeDevice = device.getDeviceInstance()
        if scopeDevice.isConnected:
	    job_control.init()
            pollDeviceStatus.delay()
        else:
            print "!!! Unable to connect to device {} !!!".format(scopeDevice.id)
            job_control.processQueryResult('app', 'fail')
            if not settings.DEBUG:
                sys.exit(1)
