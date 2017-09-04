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
    """Modbus device connector for ScopePi"""
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
        return '0.2.0'

    @property
    def description(self):
        return 'A device implementation to collect data from a device using Modbus protocol.'

    @property
    def connection_manager(self):
        return self._connection_manager

    @connection_manager.setter
    def connection_manager(self, newObj):
        self._connection_manager = newObj

    @property
    def device_id(self):
        return self._did

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
        """Property to track machine cycle time"""
        return self._mct

    @mct.setter
    def mct(self, new_val):
        self._mct = new_val

    @property
    def last_output(self):
        """Counter to track last seen output"""
        return self._last_output

    @last_output.setter
    def last_output(self, new_val):
        self._last_output = new_val

    def connect(self):
        """Connects to the device data source via connectionManager"""
        connected = self._connection_manager.connect()
        if connected:
            self.endpoint_available = True
        return connected

    def disconnect(self):
        """Disconnects from the data source via connectionManager"""
        self._connection_manager.disconnect()
        self.endpoint_available = False

    def check_device_exists(self):
        """Check if target device with given ID exists"""
        try:
            result = self._connection_manager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 2)
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

    def get_device_status(self):
        if not self.endpoint_available:
            print "Device was not available. Retry connection..."
            self.connect()
        else:
            try:
                # Control registers map: [opmode, chovrsw, chmatsw, moldid]
                #result = self._connection_manager.readHoldingReg(settings.MODBUS_CONFIG['ctrlRegAddr'], 30)
                if settings.MODBUS_CONFIG["vendor"] == "kwt":
                    modeval = self._connection_manager.readHoldingReg(settings.MODBUS_CONFIG['alarmRegAddr'], 1)
                else:
                    modeval = self._connection_manager.readCoil(settings.MODBUS_CONFIG['statusRegAddr'], 4)
            except socket_error:
                return 'fail'

            if modeval is not None:
                if settings.DEBUG:
                    print modeval
                machine = Machine.objects.first()
                #jobserial = self.hextostr(result[10:16])
                #moldid = self.hextostr(result[20:26])
                statuschange = False
                modechange = False
                
                if machine.cooverride:
                    if self._status != const.CHG_MOLD:
                        self._status = const.CHG_MOLD
                        self.last_output = self.total_output
                else:
                    if self._status == const.CHG_MOLD:
                        self._status = const.IDLE

                if machine.opstatus != self._status:
                    machine.opstatus = self._status
                    statuschange = True

                if settings.MODBUS_CONFIG["vendor"] == "kwt":
                    if 1024 <= modeval[0] < 2048:
                        self.mode = const.OFFLINE
                        if machine.opmode != 0:
                            machine.opmode = 0
                            machine.opstatus = const.IDLE
                            modechange = True
                            print 'Device offline!'
                    elif 2048 <= modeval[0] < 4096:
                        self.mode = const.MANUAL_MODE
                        if machine.opmode != 1:
                            machine.opmode = 1
                            modechange = True
                            print 'Device in manual mode.'
                    elif 4096 <= modeval[0] < 8192:
                        self.mode = const.SEMI_AUTO_MODE
                        if machine.opmode != 2:
                            machine.opmode = 2
                            machine.opstatus = const.RUNNING
                            modechange = True
                            print 'Device in semi-auto mode.'
                    elif modeval[0] >= 8192:
                        self.mode = const.AUTO_MODE
                        if machine.opmode != 3:
                            machine.opmode = 3
                            machine.opstatus = const.RUNNING
                            modechange = True
                            self.tLastUpdate = datetime.now()
                            print 'Device in auto mode.'
                    else:
                        pass
                else:
                    # Vendor=CH
                    # modeval[1] - 0:semi-auto, 1:auto
                    # modeval[2] - 0:manual off, 1:manual on
                    if modeval[2] == 1:
                        self.mode = const.MANUAL_MODE
                        if machine.opmode != 1:
                            machine.opmode = 1
                            modechange = True
                            print 'Device in manual mode.'
                    else:
                        if modeval[1] == 0:
                            self.mode = const.SEMI_AUTO_MODE
                            if machine.opmode != 2:
                                machine.opmode = 2
                                machine.opstatus = const.RUNNING
                                modechange = True
                                print 'Device in semi-auto mode.'
                        else:
                            self.mode = const.AUTO_MODE
                            if machine.opmode != 3:
                                machine.opmode = 3
                                machine.opstatus = const.RUNNING
                                modechange = True
                                self.tLastUpdate = datetime.now()
                                print 'Device in auto mode.'

                if statuschange or modechange:
                    machine.save()
                    #print (self.mode, self._status)
                return (self.mode, self._status, 'moldid')
            else:
                return "fail"

    def get_alarm_status(self):
        if self.endpoint_available:
            try:
                result = self._connection_manager.readHoldingReg(settings.MODBUS_CONFIG['alarmRegAddr'], 4)
            except socket_error:
                return 'fail'

            #print "{0:b}, {1:b}, {2:b}, {3:b}".format(result[0], result[1], result[2], result[3])
            if result is not None:
                if settings.MODBUS_CONFIG["vendor"] == "kwt":
                    errid_1 = int(result[2])
                    errid_2 = int(result[3])
                    if errid_1 != 0 or errid_2 != 0:
                        for errtag, errcode in const.ERROR_LIST.iteritems():
                            if errid_1 == errcode or errid_2 == errcode:
                                return (errtag, True)
                return ('', False)
            else:
                return "fail"

    def get_production_status(self):
        if self.endpoint_available:
            try:
                result = self._connection_manager.readHoldingReg(settings.MODBUS_CONFIG['dataRegAddr'], 4)
            except socket_error:
                return 'fail'

            if self.mode != const.OFFLINE:
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
                        #print 'TASK raw_data:{} {}'.format(raw_data, self.total_output)
                        if raw_data != self.last_output:
                            if self.mode != const.MANUAL_MODE:
                                self.mct = self.getmct()
                                self.total_output = self.calc_output(raw_data)
                            self.last_output = raw_data
                    #print 'total_output<{}> {}'.format(id(self.total_output), self.total_output)
                    return (self.mct, self.total_output)
                else:
                    return "fail"

    def resetMbCounter(self):
        if self.endpoint_available:
            try:
                result = self._connection_manager.writeCoil(settings.MODBUS_CONFIG['ctrlRegAddr'], 1)
            except socket_error:
                return 'fail'

    def calc_output(self, val):
        """
        Calculates how many molds has the machine completed.
        Arguments:
        val -- the counter value of completed molds obtained from modbus query.
        """
        print 'CALC IN total_output:{} last_output:{}'.format(self.total_output, self.last_output)
        t_output = self.total_output
        if val >= self.last_output:
            mod_diff = val - self.last_output
            t_output += mod_diff
        else:
            t_output += val
        print 'CALC OUT total_output:{}'.format(t_output)
        return t_output

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
        self._connection_manager = ModbusConnectionManager('tcp')
        self._did = did
        self._is_connected = True
        self._status = const.IDLE
        self._total_output = 0
        self._mct = 0
        self._last_output = 0

        self.mode = const.OFFLINE
        self.tLastUpdate = datetime.now()
        self.endpoint_available = False

        if self.connect():
            print "Host connected. Check device ID={}...".format(did)
            if self.check_device_exists():
                print "Device is {}, Module version {}\n".format(self.name, self.version)
            else:
                print "Device not found!"
                self.disconnect()
        else:
            print "Connection failed!"
