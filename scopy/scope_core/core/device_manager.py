"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

device_manager.py
    Managing device instance to provide abstraction for other
    modules to disregard the actual class type of the device
"""

from scope_core.config import settings

deviceInstance = None

def getDeviceInstance():
    global deviceInstance
    if deviceInstance is None:
        if settings.CONNECTOR == 'modbus':
	    from scope_core.device.modbus_device import ModbusDevice
            deviceInstance = ModbusDevice(settings.DEVICE_INFO['ID'])
        elif settings.CONNECTOR == 'fcsmysql':
	    from scope_core.device.fcs_injection_db import FCSInjectionDevice_db
            deviceInstance = FCSInjectionDevice_db(settings.DEVICE_INFO['ID'])
        else:
            pass
    return deviceInstance
