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
import threading
import device_definition as const
from socket import error as socket_error
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
    def device_id(self):
        return self._did

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def total_output(self):
        with self.lock:
            return self._total_output

    @total_output.setter
    def total_output(self, count):
        with self.lock:
            try:
                self._total_output = int(count)
            except ValueError, ex:
                print '"%s" cannot be converted to int: %s' % (count, ex)

    ##############################################
    # Module specific properties and methods
    ##############################################

    def connect(self):
        return self._connectionManager.connect()

    def disconnect(self):
        self._connectionManager.disconnect()
        self._is_connected = False

    def checkDeviceExists(self):
        try:
            result = self._connectionManager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 2)
            if result is not None:
                numhex = [result[1], result[0]]
                self.lastOutput = self.hextoint32(numhex)
                print "Device found, setting adjustment factor={}...".format(self.lastOutput)
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
                    self.tLastUpdate = datetime.now()
                    print('Device in auto mode.')
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
                inc_val = 1 if random.random() < 0.8 else 0
                self.inc_output(inc_val)
                if self.total_output != self.lastOutput:
                    self.mct = self.getmct()
                    self.lastOutput = self.total_output
            else:
                raw_data = self.hextoint32(pcshex)
                if self._status == const.CHG_MOLD or self.fco_reset:
                    self.lastOutput = raw_data
                    self.total_output = 0
                    self.fco_reset = False
                    print 'RESET done.'
                # Calc mct only if the output has changed
                print 'TASK raw_data:{} lastOutput:{} total_output:{}'.format(raw_data, self.lastOutput, self.total_output)
                print self.__dict__
                if raw_data != self.lastOutput:
                    self.mct = self.getmct()
                    self.calc_output(raw_data)
            print ('device<{}>'.format(id(self)), self.mct, self.total_output)
            return (self.mct, self.total_output)
        else:
            return "fail"

    def reset_output(self):
        """Sets the force CO reset flag to True"""
        self.fco_reset = True
        print 'RESET total_output counter. (flag={})'.format(self.fco_reset)
        print self.__dict__

    def inc_output(self, inc_val):
        """Increments _total_output by inc_val"""
        with self.lock:
            output = self.total_output
            self.total_output = output + inc_val

    def calc_output(self, val):
        """
        Calculates how many molds has the machine completed.
        Arguments:
        val -- the counter value of completed molds obtained from modbus query.
        """
        print 'CALC IN total_output:{} lastOutput:{}'.format(self.total_output, self.lastOutput)
        if val >= self.lastOutput:
            mod_diff = val - self.lastOutput
            self.inc_output(mod_diff)
        else:
            self.inc_output(val)
        self.lastOutput = val
        print 'CALC OUT total_output:{} lastOutput:{}'.format(self.total_output, self.lastOutput)
        return self.total_output

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

    def __init__(self, did):
        self._connectionManager = ModbusConnectionManager('tcp')
        self._did = did
        self._is_connected = False
        self._total_output = 0
        self._status = const.IDLE

        self.lock = threading.RLock()
        self.mode = const.OFFLINE
        self.mct = 0
        self.lastOutput = 0
        self.tLastUpdate = datetime.now()
        self.fco_reset = False

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
