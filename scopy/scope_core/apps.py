from __future__ import unicode_literals

import sys
from thread import *
from django.apps import AppConfig
from scope_core.config import settings

class ScopeCoreConfig(AppConfig):
    name = 'scope_core'
    verbose_name = 'Scope Device Adapter'

    def ready(self):
        """Post-init script for Django server"""
        import logging
        from .tasks import pollDeviceStatus
        from scope_core.core import job_control
        from scope_core.core.device_manager import DeviceManager
        from scope_core.core.socket_server import SocketServer

        logger = logging.getLogger('scopepi.debug')

        job_control.modelCheck()
        socket_server = SocketServer.getInstance()
        socket_server.start()
        scope_device = DeviceManager()
        if scope_device.get_instance().is_connected:
            job_control.setup(scope_device)
            pollDeviceStatus.delay()
        else:
            logger.critical("Unable to connect to device {}".format(scope_device.get_did()))
            print "!!! Unable to connect to device {} !!!".format(scope_device.get_did())
            job_control.processQueryResult('app', 'fail')
            if not settings.DEBUG:
                sys.exit(1)
