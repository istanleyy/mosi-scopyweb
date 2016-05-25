"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

modbus_device.py
    Implements a Modbus device to communicate with Scope server using a
    ModbusConnectionManager
"""

import random
import device_definition as const
from abstract_device import AbstractDevice
from scope_core.device_manager.modbus_manager import ModbusConnectionManager
from scope_core.models import Machine
from scope_core.config import settings

class ModbusDevice(AbstractDevice):

    ##############################################
    # Define inherit properties and methods
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
    # Module specific properties and methods
    ##############################################

    id = 'not_set'
    isConnected = False
    
    # For testing purpose
    outpcs = 5

    def connect(self):
        return self._connectionManager.connect()
    
    def disconnect(self):
        self._connectionManager.disconnect()
        self.isConnected = False
        
    def checkDeviceExists(self):
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['ctrlRegAddr'], 1)
        if result is not None:
            return True
        else:
            return False

    def getDeviceStatus(self):
        # Control registers map: [opmode, chovrsw, chmatsw, moldid] 
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['ctrlRegAddr'], 4)
        if result is not None:
            #print(result)
            machine = Machine.objects.first()
            status = const.RUNNING
            moldid = str(result[3])
            
            if result[1] == 1:
                status = const.CHG_MOLD
            else:
                if result[2] == 1:
                    status = const.CHG_MATERIAL
            
            if result[0] == 0:
                print('Device is offline!')
                if machine.opmode != 0:
                    machine.opmode = 0
                    machine.save()
                    return (const.OFFLINE, status, moldid)
            elif result[0] == 1:
                if machine.opmode != 1:
                    machine.opmode = 1
                    machine.save()
                    print('Device in manual mode.')
                    return (const.MANUAL_MODE, status, moldid)
            elif result[0] == 2:
                if machine.opmode != 2:
                    machine.opmode = 2
                    machine.save()
                    print('Device in semi-auto mode.')
                    return (const.SEMI_AUTO_MODE, status, moldid)
            elif result[0] == 3:
                if machine.opmode != 3:
                    machine.opmode = 3
                    machine.save()
                    print('Device in auto mode.')
                    return (const.AUTO_MODE, status, moldid)
            else:
                pass
        else:
            return "fail"
    
    def getAlarmStatus(self):
        result = self._connectionManager.readCoil(settings.MODBUS_CONFIG['alarmRegAddr'], 5)
        if result is not None:
            return (999, result[0])
        else:
            return "fail"
            
    def getProductionStatus(self):
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 5)
        
        # For testing purpose
        #self.outpcs = random.randint(self.outpcs, self.outpcs+1)
        self.outpcs = self.outpcs+1 if random.random() < 0.7 else self.outpcs
        
        if result is not None:
            #return (result[0], result[1], '20150823ABC')
            return (result[0], self.outpcs)
        else:
            return "fail"

    def __init__(self, id):
        self.id = id
        if self.connect():
            print("Host connected. Check device ID={}...".format(id))
            if self.checkDeviceExists():
                self.isConnected = True
                print("Device found. Ready to proceed...")
                print('Device is {}, Module version {}\n'.format(self.name, self.version))
            else:
                print("Device doesn't exist!")
                self.disconnect()
        else:
            print("Connection failed!")
        