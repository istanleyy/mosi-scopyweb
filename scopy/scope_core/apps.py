from __future__ import unicode_literals

from django.apps import AppConfig

# from device.fcs_injection_db import FCSInjectionDevice_db


class ScopeCoreConfig(AppConfig):
    name = 'scope_core'
    verbose_name = 'Scope Device Adapter'
    
"""
fcsDevice = FCSInjectionDevice_db('B0750018')

if fcsDevice.connect():
    print("Connection success! Check device ID={}...".format(fcsDevice.id))
    if fcsDevice.checkDeviceExists():
        print("Device found. Ready to proceed...")
        print 'Device is {}, Module version {}\n'.format(fcsDevice.name, fcsDevice.version)
        fcsDevice.disconnect()
    else:
        print("Device doesn't exist!")
        fcsDevice.disconnect()
else:
    print("Connection failed!")
"""