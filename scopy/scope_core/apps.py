from __future__ import unicode_literals

from thread import *
from django.apps import AppConfig

class ScopeCoreConfig(AppConfig):
    name = 'scope_core'
    verbose_name = 'Scope Device Adapter'
    
    def ready(self):
        from core.socket_server import SocketServer
        from .tasks import pollDeviceStatus
        from device.fcs_injection_db import FCSInjectionDevice_db

        socketServer = SocketServer()
        socketServer.start()
        fcsDevice = FCSInjectionDevice_db('B0750018')
        if fcsDevice.isConnected:
            pollDeviceStatus.delay()
        else:
            print "!!! Unable to connect to device {} !!!".format(fcsDevice.id)