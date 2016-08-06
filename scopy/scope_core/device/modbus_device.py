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
from datetime import datetime
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
    outpcs = 0
    mct = 0

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
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['ctrlRegAddr'], 30)
        if result is not None:
            if settings.DEBUG:
                print(result)
            machine = Machine.objects.first()
            jobserial = self.hextostr(result[10:16])
            moldid = self.hextostr(result[20:26])
            print('jobserial: ' + jobserial + ' moldid: ' + moldid)
            statuschange = False
            modechange = False
            
            modeval = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['alarmRegAddr'], 1)	   
 
            if result[0] == 2:
                self.status = const.CHG_MOLD
                self.outpcs = 0        
            elif result[0] == 3:
                self.status = const.CHG_MATERIAL
            elif result[0] == 4:
                self.status = const.SETUP
            else:
                self.status = const.RUNNING if result[0] == 1 else const.IDLE

            if machine.opstatus != self.status:
                machine.opstatus = self.status
                statuschange = True

            if modeval[0] == 1024:
                print('Device offline!')
                self.mode = const.OFFLINE
                if machine.opmode != 0:
                    machine.opmode = 0
                    machine.opstatus = 0
                    modechange = True
            elif modeval[0] == 2048:
                self.mode = const.MANUAL_MODE
                if machine.opmode != 1:
                    machine.opmode = 1
                    modechange = True
                    print('Device in manual mode.')
            elif modeval[0] == 4096:
                self.mode = const.SEMI_AUTO_MODE
                if machine.opmode != 2:
                    machine.opmode = 2
                    modechange = True
                    print('Device in semi-auto mode.')
            elif modeval[0] == 8192:
                self.mode = const.AUTO_MODE
                if machine.opmode != 3:
                    machine.opmode = 3
                    modechange = True
                    print('Device in auto mode.')
            else:
                pass
            
            if statuschange or modechange:
                machine.save()
                print (self.mode, self.status)
            return (self.mode, self.status, moldid)
        else:
            return "fail"
    
    def getAlarmStatus(self):
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['alarmRegAddr'], 4)
        print "{0:b}, {1:b}, {2:b}, {3:b}".format(result[0], result[1], result[2], result[3])
        if result is not None:
            errid_1 = int(result[2])
            errid_2 = int(result[3])
            if errid_1 != 0 or errid_2 != 0:
                for errtag, errcode in const.ERROR_LIST.iteritems():
                    if errid_1 == errcode or errid_2 == errcode:
                        return (errtag, True)
                return ('X2', True)
            else:
                return ('', False)
        else:
            return "fail"
            
    def getProductionStatus(self):
        result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 4)
        
        if result is not None:
            pcshex = [result[1], result[0]]
            if settings.SIMULATE:
                # For testing purpose
                self.outpcs = self.outpcs+1 if random.random() < 0.7 else self.outpcs
                if self.outpcs != self.lastOutput:
                    self.mct = self.getmct()
                    self.lastOutput = self.outpcs
            else:
                self.outpcs = self.hextoint32(pcshex)
                # Calc mct only if the output has changed
                if self.outpcs != self.lastOutput:
                    self.mct = self.getmct()
                    self.lastOutput = self.outpcs
            print (self.mct, self.outpcs)
            return (self.mct, self.outpcs)
        else:
            return "fail"

    def getmct(self):
        now = datetime.now()
        delta = now - self.tLastUpdate
        self.tLastUpdate = now
        return delta.seconds

    def hextostr(self, registers):
        #print registers
        result = ''
        for i in range(len(registers)):
            if registers[i] != 0:
                hexval = '%x' % registers[i]
                result += hexval.decode('hex')
        return result.strip(' \t\n\r')

    def hextoint32(self, registers):
	    if registers[0] != 0:
	        return registers[0] << 16 | registers[1]
	    else:
	        return registers[1]

    def __init__(self, id):
        self.id = id
        self.mode = const.OFFLINE
        self.status = const.IDLE
        self.lastOutput = 0
        self.tLastUpdate = datetime.now()
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