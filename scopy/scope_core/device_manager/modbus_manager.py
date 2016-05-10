import modbus_tk
import modbus_tk.defines as const
from modbus_tk import modbus_tcp
from abstract_manager import AbstractConnectionManager
from scope_core.config import settings

class ModbusConnectionManager(AbstractConnectionManager):
    logger = None
    protocol = None
    mbmaster = None

    # Valid protocol are 'tcp', 'rtu'
    def __init__(self, prtcl):
        self.logger = modbus_tk.utils.create_logger("console")
        self.protocol = prtcl
        
    def connect(self):
        try:
            self.mbmaster = modbus_tcp.TcpMaster(port=settings.MODBUS_CONFIG['port'])
            self.mbmaster.set_timeout(5.0)
            return True
        except modbus_tk.modbus.ModbusError as error:
            logger.error("%s- Code=%d", error, error.get_exception_code())
            
    def disconnect(self):
        pass
        
    def readHoldingReg(self, startadd, quantity):
        try:
            result = self.mbmaster.execute(1, const.READ_HOLDING_REGISTERS, startadd, quantity)
            return result
        except modbus_tk.modbus.ModbusError as error:
            logger.error("%s- Code=%d", error, error.get_exception_code())
    
    def readCoil(self, startadd, quantity):
        try:
            result = self.mbmaster.execute(1, const.READ_COILS, startadd, quantity)
            return result
        except modbus_tk.modbus.ModbusError as error:
            logger.error("%s- Code=%d", error, error.get_exception_code())
    