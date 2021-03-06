from __future__ import unicode_literals

import sys
from django.apps import AppConfig
from scope_core.config import settings

class ScopeCoreConfig(AppConfig):
    name = 'scope_core'
    verbose_name = 'Scope Device Adapter'

    def ready(self):
        """Post-init script for Django server"""
        import logging
        from . import tasks
        from scope_core.core import job_control
        from scope_core.core.device_manager import DeviceManager
        from scope_core.core.socket_server import SocketServer

        logger = logging.getLogger('scopepi.debug')

        job_control.modelCheck()
        scope_device = DeviceManager()
        if scope_device.get_instance().is_connected:
            job_control.setup(scope_device)
            SocketServer.get_instance()
            tasks.init_tasks()
        else:
            logger.critical("Unable to connect to device {}".format(scope_device.get_did()))
            print "!!! Unable to connect to device {} !!!".format(scope_device.get_did())
            job_control.processQueryResult('app', 'fail')
            if not settings.DEBUG:
                sys.exit(1)
