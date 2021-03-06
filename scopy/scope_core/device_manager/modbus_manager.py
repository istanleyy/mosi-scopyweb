"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

modbus_manager.py
    A connection manager for the Modbus protocol implemented using Modbus-tk project
"""

import modbus_tk
import modbus_tk.defines as const
from modbus_tk import modbus_tcp
from abstract_manager import AbstractConnectionManager
from scope_core.config import settings

class ModbusConnectionManager(AbstractConnectionManager):
    logger = None
    protocol = None
    mbmaster = None
    lastError = None

    # Valid protocol are 'tcp', 'rtu'
    def __init__(self, prtcl):
        self.logger = modbus_tk.utils.create_logger("console")
        self.protocol = prtcl

    def connect(self):
        try:
            self.mbmaster = modbus_tcp.TcpMaster(host=settings.MODBUS_CONFIG['slaveAddr'], port=settings.MODBUS_CONFIG['port'])
            self.mbmaster.set_timeout(5.0)
            return True
        except modbus_tk.modbus.ModbusError as error:
            if error.get_exception_code() != self.lastError:
                self.lastError = error.get_exception_code()
                self.logger.error("%s- Code=%d", error, error.get_exception_code())
            return False

    def disconnect(self):
        pass

    def readHoldingReg(self, startadd, quantity):
        try:
            result = self.mbmaster.execute(51, const.READ_HOLDING_REGISTERS, startadd, quantity)
            return result
        except modbus_tk.modbus.ModbusError as error:
            if error.get_exception_code() != self.lastError:
                self.lastError = error.get_exception_code()
                self.logger.error("%s- Code=%d", error, error.get_exception_code())
            return None
        except Exception as e:
            if e != self.lastError:
                self.lastError = e
            return None

    def readInputReg(self, startadd, quantity):
        try:
            result = self.mbmaster.execute(51, const.READ_INPUT_REGISTERS, startadd, quantity)
            return result
        except modbus_tk.modbus.ModbusError as error:
            if error.get_exception_code() != self.lastError:
                self.lastError = error.get_exception_code()
                self.logger.error("%s- Code=%d", error, error.get_exception_code())
            return None
        except Exception as e:
            if e != self.lastError:
                self.lastError = e
            return None

    def readCoil(self, startadd, quantity):
        try:
            result = self.mbmaster.execute(51, const.READ_COILS, startadd, quantity)
            return result
        except modbus_tk.modbus.ModbusError as error:
            if error.get_exception_code() != self.lastError:
                self.lastError = error.get_exception_code()
                self.logger.error("%s- Code=%d", error, error.get_exception_code())
            return None
        except Exception as e:
            if e != self.lastError:
                self.lastError = e
            return None

    def writeCoil(self, addr, val):
        try:
            result = self.mbmaster.execute(51, const.WRITE_SINGLE_COIL, addr, output_value=val)
            return result
        except modbus_tk.modbus.ModbusError as error:
            if error.get_exception_code() != self.lastError:
                self.lastError = error.get_exception_code()
                self.logger.error("%s- Code=%d", error, error.get_exception_code())
            return None
        except Exception as e:
            if e != self.lastError:
                self.lastError = e
            return None
