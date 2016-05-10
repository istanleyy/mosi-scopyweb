from abstract_device import AbstractDevice
from scope_core.device_manager.modbus_manager import ModbusConnectionManager


class ModbusDevice(AbstractDevice):

    ##############################################
    # Define inherit properties and moethods
    ##############################################

    @property
    def name(self):
        return 'Generic Modbus Device'

    @property
    def provider(self):
        return 'MOSi Technologies, LLC'

    @property
    def version(self):
        return '0.1.0'

    @property
    def description(self):
        return 'A device implementation to collect data from a device using Modbus protocol.'

    _connectionManager = ModbusConnectionManager('tcp')

    @property
    def connectionManager(self):
        return self._connectionManager

    @connectionManager.setter
    def connectionManager(self, newObj):
        self._connectionManager = newObj

    ##############################################
    # Module specific properties and moethods
    ##############################################

    id = 'not_set'
    isConnected = False
    activeDevice = None

    def connect(self):
        return self._connectionManager.connect()
    
    def disconnect(self):
        self._connectionManager.disconnect()
        self.isConnected = False
        
    def checkDeviceExists(self):
        result = self._connectionManager.readHoldingReg(40000, 1)
        if result is not None:
            return True
        else:
            return False

    def getDeviceStatus(self):
        result = self._connectionManager.readHoldingReg(40001, 1)
        if result is not None:
            return '3'
        else:
            return "fail"
    
    def getAlarmStatus(self):
        result = self._connectionManager.readCoil(0, 5)
        if result is not None:
            return ('timestamp', 999, result[0])
        else:
            return "fail"
            
    def getProductionStatus(self):
        result = self._connectionManager.readHoldingReg(40009, 5)
        if result is not None:
            return (18, 101, 'TESTMOLD')
        else:
            return "fail"

    def __init__(self, id):
        self.id = id
        if self.connect():
            print("Host connected. Check device ID={}...".format(id))
            if self.checkDeviceExists():
                self.isConnected = True
                self.activeDevice = self
                print("Device found. Ready to proceed...")
                print('Device is {}, Module version {}\n'.format(self.name, self.version))
            else:
                print("Device doesn't exist!")
                self.disconnect()
        else:
            print("Connection failed!")
        