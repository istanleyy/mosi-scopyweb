from __future__ import unicode_literals

import sys
from thread import *
from django.apps import AppConfig
from scope_core.config import settings

class ScopeCoreConfig(AppConfig):
    name = 'scope_core'
    verbose_name = 'Scope Device Adapter'

    def ready(self):
        import logging
        from .tasks import pollDeviceStatus
        from scope_core.core import job_control
        from scope_core.core.device_manager import DeviceManager
        from scope_core.core.socket_server import SocketServer

        logger = logging.getLogger('scopepi.debug')

        job_control.modelCheck()
        socketServer = SocketServer.getInstance()
        socketServer.start()
        scopeDevice = DeviceManager()
        if scopeDevice.get_instance().is_connected:
            job_control.init(scopeDevice)
            pollDeviceStatus.delay()
        else:
            logger.critical("Unable to connect to device {}".format(scopeDevice.get_did()))
            print "!!! Unable to connect to device {} !!!".format(scopeDevice.get_did())
            job_control.processQueryResult('app', 'fail')
            if not settings.DEBUG:
                sys.exit(1)
