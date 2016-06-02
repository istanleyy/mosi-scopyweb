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
    outpcs = 0

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
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['ctrlRegAddr'], 10)
        if result is not None:
        
            if settings.DEBUG:
                print(result)        
            machine = Machine.objects.first()
            status = const.RUNNING
            mode = const.OFFLINE
            moldid = self.hextostr(result[3:9])
            #print('moldid: ' + moldid)
            statuschange = False
            modechange = False
            
            if result[1] == 1:
                status = const.CHG_MOLD
                if not machine.moldAdjustStatus:
                    machine.moldAdjustStatus = True
                    statuschange = True
                
            else:
                status = const.RUNNING
                if machine.moldAdjustStatus:
                    machine.moldAdjustStatus = False
                    statuschange = True

                if result[2] == 1:
                    status = const.CHG_MATERIAL
                    if not machine.cleaningStatus:
                        machine.cleaningStatus = True
                        statuschange = True
                    
                else:
                    if machine.cleaningStatus:
                        machine.cleaningStatus = False
                        statuschange = True
            
            if result[0] == 0:
                print('Device is offline!')
                mode = const.OFFLINE
                if machine.opmode != 0:
                    machine.opmode = 0
                    modechange = True
            elif result[0] == 1:
                mode = const.MANUAL_MODE
                if machine.opmode != 1:
                    machine.opmode = 1
                    modechange = True
                    print('Device in manual mode.')
            elif result[0] == 2:
                mode = const.SEMI_AUTO_MODE
                if machine.opmode != 2:
                    machine.opmode = 2
                    modechange = True
                    print('Device in semi-auto mode.')
            elif result[0] == 3:
                mode = const.AUTO_MODE
                if machine.opmode != 3:
                    machine.opmode = 3
                    modechange = True
                    print('Device in auto mode.')
            else:
                pass
            
            if statuschange or modechange:
                machine.save()
                return (mode, status, moldid)
                
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
        
        if result is not None:
            if settings.SIMULATE:
                # For testing purpose
                self.outpcs = self.outpcs+1 if random.random() < 0.7 else self.outpcs
                return (result[0], self.outpcs)
            else:
                return (result[0], result[1])
        else:
            return "fail"
            
    def hextostr(self, registers):
        #print registers
        result = ''
        for i in range(len(registers)):
            if registers[i] != 0:
                hexval = '%x' % registers[i]
                result += hexval.decode('hex')
        return result.strip(' \t\n\r')

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
        