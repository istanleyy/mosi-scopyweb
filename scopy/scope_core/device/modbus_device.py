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
from socket import error as socket_error
from datetime import datetime
from scope_core.device import device_definition as const
from scope_core.device.abstract_device import AbstractDevice
from scope_core.device_manager.modbus_manager import ModbusConnectionManager
from scope_core.models import Machine
from scope_core.config import settings

class ModbusDevice(AbstractDevice):
    """Modbus device driver for ScopePi"""
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
        return '0.1.2'

    @property
    def description(self):
        return 'A device implementation to collect data from a device using Modbus protocol.'

    @property
    def connectionManager(self):
        return self._connectionManager

    @connectionManager.setter
    def connectionManager(self, newObj):
        self._connectionManager = newObj

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def total_output(self):
        return self._total_output

    @total_output.setter
    def total_output(self, new_val):
        self._total_output = new_val
        print 'UPDATED output counter<{}>, val={}'.format(
            id(self._total_output),
            self._total_output)

    ##############################################
    # Module specific properties and methods
    ##############################################

    @property
    def mct(self):
        """Alias for the machine cycle time component of _counter_param"""
        return self._mct

    @mct.setter
    def mct(self, new_val):
        self._mct = new_val

    @property
    def last_output(self):
        """Alias for the last output component of _counter_param"""
        return self._last_output

    @last_output.setter
    def last_output(self, new_val):
        self._last_output = new_val

    def device_id(self):
        return self._did

    def connect(self):
        """Connects to the device data source via connectionManager"""
        return self._connectionManager.connect()

    def disconnect(self):
        """Disconnects from the data source via connectionManager"""
        self._connectionManager.disconnect()
        self._is_connected = False

    def checkDeviceExists(self):
        """Check if target device with given ID exists"""
        try:
            result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 2)
            if result is not None:
                numhex = [result[1], result[0]]
                self.last_output = self.hextoint32(numhex)
                print "Device found, setting adjustment factor={}...".format(self.last_output)
                return True
            else:
                return False
        except socket_error:
            print 'Cannot connect to device!'
            return False

    def getDeviceStatus(self):
        try:
            # Control registers map: [opmode, chovrsw, chmatsw, moldid]
            result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['ctrlRegAddr'], 30)
        except socket_error:
            return 'fail'

        if result is not None:
            if settings.DEBUG:
                print result
            machine = Machine.objects.first()
            jobserial = self.hextostr(result[10:16])
            moldid = self.hextostr(result[20:26])
            print 'jobserial: ' + jobserial + ' moldid: ' + moldid
            statuschange = False
            modechange = False

            modeval = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['alarmRegAddr'], 1)	   

            if result[0] == 2:
                self._status = const.CHG_MOLD
                self.total_output = 0
            elif result[0] == 3:
                self._status = const.CHG_MATERIAL
            elif result[0] == 4:
                self._status = const.SETUP
            else:
                self._status = const.RUNNING if result[0] == 1 else const.IDLE

            if machine.opstatus != self._status:
                machine.opstatus = self._status
                statuschange = True

            if modeval[0] == 1024:
                print 'Device offline!'
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
                    print 'Device in manual mode.'
            elif modeval[0] == 4096:
                self.mode = const.SEMI_AUTO_MODE
                if machine.opmode != 2:
                    machine.opmode = 2
                    modechange = True
                    print 'Device in semi-auto mode.'
            elif modeval[0] == 8192:
                self.mode = const.AUTO_MODE
                if machine.opmode != 3:
                    machine.opmode = 3
                    modechange = True
                    self.tLastUpdate = datetime.now()
                    print 'Device in auto mode.'
            else:
                pass

            if statuschange or modechange:
                machine.save()
                print (self.mode, self._status)
            return (self.mode, self._status, moldid)
        else:
            return "fail"

    def getAlarmStatus(self):
        try:
            result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['alarmRegAddr'], 4)
        except socket_error:
            return 'fail'

        print "{0:b}, {1:b}, {2:b}, {3:b}".format(result[0], result[1], result[2], result[3])
        if result is not None:
            errid_1 = int(result[2])
            errid_2 = int(result[3])
            if errid_1 != 0 or errid_2 != 0:
                for errtag, errcode in const.ERROR_LIST.iteritems():
                    if errid_1 == errcode or errid_2 == errcode:
                        return (errtag, True)
            return ('', False)
        else:
            return "fail"

    def getProductionStatus(self):
        try:
            result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 4)
        except socket_error:
            return 'fail'

        if result is not None:
            pcshex = [result[1], result[0]]
            if settings.SIMULATE and self.mode == const.AUTO_MODE:
                # For testing purpose
                self.total_output += 1 if random.random() < 0.8 else 0
                if self.total_output != self.last_output:
                    self.mct = self.getmct()
                    self.last_output = self.total_output
            else:
                raw_data = self.hextoint32(pcshex)
                if self._status == const.CHG_MOLD:
                    self.total_output = 0
                    self.last_output = raw_data
                # Calc mct only if the output has changed
                print 'TASK raw_data:{} {}'.format(raw_data, self.total_output)
                if raw_data != self.last_output:
                    self.mct = self.getmct()
                    self.total_output = self.calc_output(raw_data)
            print ('total_output<{}> {}'.format(id(self.total_output), self.total_output))
            return (self.mct, self.total_output)
        else:
            return "fail"

    def calc_output(self, val):
        """
        Calculates how many molds has the machine completed.
        Arguments:
        val -- the counter value of completed molds obtained from modbus query.
        """
        print 'CALC IN total_output:{}'.format(self.total_output)
        result = self.total_output
        if val >= self.last_output:
            mod_diff = val - self.last_output
            result += mod_diff
        else:
            result += val
        self.last_output = val
        print 'CALC OUT total_output:{}'.format(result)
        return result

    def getmct(self):
        """Calculates machine cycle time"""
        now = datetime.now()
        delta = now - self.tLastUpdate
        self.tLastUpdate = now
        return delta.seconds

    def hextostr(self, registers):
        """Decodes hex in an array and join them to form a string"""
        #print registers
        result = ''
        for i in range(len(registers)):
            if registers[i] != 0:
                hexval = '%x' % registers[i]
                result += hexval.decode('hex')
        return result.strip(' \t\n\r')

    def hextoint32(self, registers):
        """Converts and joins hex values in an array to form an integer number"""
        if registers[0] != 0:
            return registers[0] << 16 | registers[1]
        else:
            return registers[1]

    def __init__(self, did):
        self._connectionManager = ModbusConnectionManager('tcp')
        self._did = did
        self._is_connected = False
        self._status = const.IDLE
        self._total_output = 0
        self._mct = 0
        self._last_output = 0

        self.mode = const.OFFLINE
        self.tLastUpdate = datetime.now()

        if self.connect():
            print "Host connected. Check device ID={}...".format(did)
            if self.checkDeviceExists():
                self._is_connected = True
                print "Device is {}, Module version {}\n".format(self.name, self.version)
            else:
                print "Device doesn't exist!"
                self.disconnect()
        else:
            print "Connection failed!"
