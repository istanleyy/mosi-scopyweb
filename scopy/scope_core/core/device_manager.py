from scope_core.config import settings
from scope_core.device.modbus_device import ModbusDevice
from scope_core.device.fcs_injection_db import FCSInjectionDevice_db

def getDeviceInstance():
    if settings.CONNECTOR == 'modbus':
        return ModbusDevice(settings.DEVICE_INFO['ID'])
    elif settings.CONNECTOR == 'fcsmysql':
        return FCSInjectionDevice_db(settings.DEVICE_INFO['ID'])
    else:
        return None