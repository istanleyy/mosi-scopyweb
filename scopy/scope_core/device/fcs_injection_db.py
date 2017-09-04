#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

fcs_injection_db.py
    This module implements Scope's abstract device, and uses MySqlConnectionManager
    to connect to FCS's injection mold machine data collector to query the production
    status/data of the machine with the machine ID given to the instance of a
    FCSInjectionDevice_db class
"""

import logging
import scope_core.device.device_definition as const
from scope_core.device.abstract_device import AbstractDevice
from scope_core.device_manager.mysql_manager import MySqlConnectionManager
from scope_core.models import Machine
from scope_core.config import settings

class FCSInjectionDevice_db(AbstractDevice):
    """FCS DB server mysql connector for ScopePi"""
    ##############################################
    # Define inherit properties and methods
    ##############################################

    @property
    def name(self):
        return 'FCS Injection/DB'

    @property
    def provider(self):
        return 'MOSi Technologies, LLC'

    @property
    def version(self):
        return '0.1.3'

    @property
    def description(self):
        return 'A device implementation to collect data from MWeb database for a single FCS injection mold machine.'

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
    def total_output(self, count):
        try:
            self._total_output = int(count)
        except ValueError, ex:
            print '"%s" cannot be converted to int: %s' % (count, ex)

    ##############################################
    # Module specific properties and methods
    ##############################################

    def connect(self):
        """Connects to FCS DB via a connection manager."""
        return self._connection_manager.connect()

    def disconnect(self):
        """Disconnect from a FCS DB server."""
        self._connection_manager.disconnect()
        self._is_connected = False

    @property
    def last_output(self):
        """Counter to track last seen output"""
        return self._last_output

    @last_output.setter
    def last_output(self, new_val):
        if new_val:
            try:
                val = int(new_val)
                self._last_output = val
            except ValueError:
                self._logger.error('Invalid value when updating last_output.')

    def check_device_exists(self):
        """Check if the FCS injection mold machine with the given device ID exists in remote DB."""
        query = ("SELECT ModNum FROM cal_data2 WHERE colmachinenum='{}' AND datetime=(select max(datetime) from cal_data2 where colmachinenum='{}')".format(self._did, self._did))
        result = self._connection_manager.query(query)
        if result is not None:
            self.last_output = result[0]
            print "Device found, setting adjustment factor={}...".format(self.last_output)
            return True
        else:
            return False

    def get_device_status(self):
        query = (
            "SELECT MachineStatus,ModNum,MO FROM cal_data2 WHERE colmachinenum='{}' AND datetime=(select max(datetime) from cal_data2 where colmachinenum='{}')".format(self._did, self._did)
            )
        result = self._connection_manager.query(query)
        if result is not None:
            if settings.DEBUG:
                print result
            machine = Machine.objects.first()
            modnum = result[1]
            moldid = result[2]
            statuschange = False
            modechange = False
            modestr = result[0].encode('utf-8', 'ignore')

            if machine.cooverride:
                if self._status != const.CHG_MOLD:
                    self._status = const.CHG_MOLD
                    self.last_output = modnum
            else:
                if self._status == const.CHG_MOLD:
                    self._status = const.IDLE

            if machine.opstatus != self._status:
                machine.opstatus = self._status
                statuschange = True

            if modestr[0] == '1':
                self.mode = const.MANUAL_MODE
                if machine.opmode != 1:
                    machine.opmode = 1
                    modechange = True
                    print 'Device in manual mode.'
            elif modestr[0] == '2':
                self.mode = const.SEMI_AUTO_MODE
                if machine.opmode != 2:
                    machine.opmode = 2
                    modechange = True
                    print 'Device in semi-auto mode.'
            elif modestr[0] == '3':
                self.mode = const.AUTO_MODE
                if machine.opmode != 3:
                    machine.opmode = 3
                    machine.opstatus = const.RUNNING
                    modechange = True
                    print 'Device in auto mode.'
            else:
                self.mode = const.OFFLINE
                if machine.opmode != 0:
                    machine.opmode = 0
                    machine.opstatus = const.IDLE
                    modechange = True
                    print 'Device is offline!'

            if statuschange or modechange:
                machine.save()
            return (self.mode, self._status, moldid)
        else:
            self._logger.error('Cannot query machine status.')
            return "fail"

    def get_alarm_status(self):
        query = (
            "SELECT alarmid,alarmstatus FROM a_alarm AS A INNER JOIN (SELECT DISTINCT injid FROM cal_data2 WHERE colmachinenum='{}') AS C ON A.injid=C.injid ORDER BY strtime DESC LIMIT 1".format(self._did)
            )
        result = self._connection_manager.query(query)
        if result is not None:
            if result[1] == 1:
                for errtag, errcode in const.ERROR_LIST.iteritems():
                    if result[0] == errcode:
                        return (errtag, True)
                return ('X2', True)
            else:
                return ('', False)
        else:
            self._logger.error('Cannot query alarm status.')
            return "fail"

    def get_production_status(self):
        query = (
            "SELECT CycleTime,ModNum FROM cal_data2 WHERE colmachinenum='{}' AND datetime=(select max(datetime) from cal_data2 where colmachinenum='{}')".format(self._did, self._did)
            )
        result = self._connection_manager.query(query)
        #print result
        if self.mode != const.OFFLINE:
            if result is not None:
                modnum = 0
                if result[1] is not None:
                    modnum = result[1]
                if self._status == const.CHG_MOLD:
                    self.total_output = 0
                    self.last_output = modnum
                if modnum != self.last_output:
                    # Update output counter when in semi-auto and auto mode.
                    # If in manual mode, just keep track of machine's last modnum.
                    if self.mode != const.MANUAL_MODE:
                        self.total_output = self.calc_output(modnum)
                    self.last_output = modnum
                # FCS server updates data every minute.
                return (60, self.total_output)
            else:
                self._logger.error('Cannot query production status.')
                return "fail"

    def calc_output(self, raw_data):
        """
        Calculates how many molds has the machine completed.
        Arguments:
        raw_data -- the counter value of completed molds obtained from FCS DB query.
        """
        if raw_data is None:
            raw_data = 0
        t_output = self.total_output
        if raw_data >= self.last_output:
            mod_diff = raw_data - self.last_output
            t_output += mod_diff
        else:
            t_output += raw_data
        return t_output

    def __init__(self, did):
        self._logger = logging.getLogger('scopepi.debug')
        self._connection_manager = MySqlConnectionManager()
        self._did = did
        self._is_connected = False
        self._status = const.IDLE
        self._total_output = 0
        self._last_output = 0

        self.mode = const.OFFLINE

        if self.connect():
            print "DB connected. Check device ID={}...".format(did)
            if self.check_device_exists():
                self._is_connected = True
                print "Device found. Ready to proceed..."
                print 'Device is {}, Module version {}\n'.format(self.name, self.version)
            else:
                print "Device doesn't exist!"
                self._logger.error("FCS machine doesn't exist.")
                self.disconnect()
        else:
            self._logger.error('Cannot connect to FCS server.')
            print "Connection failed!"
