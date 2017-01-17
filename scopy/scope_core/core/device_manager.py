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

class DeviceManager(object):
    """
    DeviceManager handles the creation of the device based on the type defined
    in the settings file.
    """

    def __init__(self):
        self._device_instance = None
        self.get_instance()

    def get_instance(self):
        """Returns the instance reference of the concrete device implementation"""
        if self._device_instance is None:
            if settings.CONNECTOR == 'modbus':
                from scope_core.device.modbus_device import ModbusDevice
                self._device_instance = ModbusDevice(settings.DEVICE_INFO['ID'])
            elif settings.CONNECTOR == 'fcsmysql':
                from scope_core.device.fcs_injection_db import FCSInjectionDevice_db
                self._device_instance = FCSInjectionDevice_db(settings.DEVICE_INFO['ID'])
            else:
                pass
        return self._device_instance

    def get_did(self):
        """Returns the device ID of the corresponding instance"""
        return self._device_instance.device_id()
