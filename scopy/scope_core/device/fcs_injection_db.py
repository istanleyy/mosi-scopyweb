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
import device_definition as const
from abstract_device import AbstractDevice
from scope_core.device_manager.mysql_manager import MySqlConnectionManager
from scope_core.models import Machine
from scope_core.config import settings

class FCSInjectionDevice_db(AbstractDevice):

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
        return '0.1.1'

    @property
    def description(self):
        return 'A device implementation to collect data from MWeb database for a single FCS injection mold machine.'

    _connection_manager = MySqlConnectionManager()

    @property
    def connectionManager(self):
        return self._connection_manager

    @connectionManager.setter
    def connectionManager(self, newObj):
        self._connection_manager = newObj

    ##############################################
    # Module specific properties and methods
    ##############################################

    logger = None
    _did = 'not_set'
    _isConnected = False

    def connect(self):
        """Connects to FCS DB via a connection manager."""
        return self._connection_manager.connect()

    def disconnect(self):
        """Disconnect from a FCS DB server."""
        self._connection_manager.disconnect()
        self._isConnected = False

    def check_device_exists(self):
        """Check if the FCS injection mold machine with the given device ID exists in remote DB."""
        query = ("SELECT COUNT(*) FROM cal_data2 WHERE colmachinenum='{}'".format(self._did))
        result = self._connection_manager.query(query)
        if result is not None and result[0] > 0:
            return True
        else:
            return False

    def getDeviceStatus(self):
        query = (
            "SELECT MachineStatus,ModNum,MO FROM cal_data2 WHERE colmachinenum='{}' ORDER BY DateTime DESC LIMIT 1".format(self._did)
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

            if machine.opstatus == const.CHG_MOLD:
                self.last_modnum = modnum
                self.total_modnum = 0

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
                print 'Device is offline!'
                self.mode = const.OFFLINE
                if machine.opmode != 0:
                    machine.opmode = 0
                    machine.opstatus = const.IDLE
                    modechange = True

            if statuschange or modechange:
                machine.save()
            return (self.mode, self.status, moldid)
        else:
            self.logger.error('Cannot query machine status.')
            return "fail"

    def getAlarmStatus(self):
        query = (
            "SELECT alarmid,alarmstatus FROM a_alarm AS A INNER JOIN (SELECT DISTINCT injid FROM cal_data2 WHERE colmachinenum='{}') AS C ON A.injid=C.injid ORDER BY strtime DESC LIMIT 1".format(self._did)
            )
        result = self._connection_manager.query(query)
        if result is not None:
            print result
            if result[1] == 1:
                for errtag, errcode in const.ERROR_LIST.iteritems():
                    if result[0] == errcode:
                        return (errtag, True)
                return ('X2', True)
            else:
                return ('', False)
        else:
            self.logger.error('Cannot query alarm status.')
            return "fail"

    def getProductionStatus(self):
        query = (
            "SELECT CycleTime,ModNum FROM cal_data2 WHERE colmachinenum='{}' ORDER BY DateTime DESC LIMIT 1".format(self._did)
            )
        result = self._connection_manager.query(query)
        print result
        if result is not None:
            # FCS server updates data every minute.
            return (60, self.calc_mod_num(result[1]))
        else:
            self.logger.error('Cannot query production status.')
            return "fail"

    def calc_mod_num(self, raw_data):
        """
        Calculates how many molds has the machine completed.
        Arguments:
        raw_data -- the counter value of completed molds obtained from FCS DB query.
        """
        if raw_data > self.last_modnum:
            mod_diff = raw_data - self.last_modnum
            self.total_modnum += mod_diff
        else:
            self.total_modnum += raw_data
        self.last_modnum = raw_data
        return self.total_modnum

    def __init__(self, did):
        self.logger = logging.getLogger('scopepi.debug')
        self._did = did
        self.mode = const.OFFLINE
        self.status = const.IDLE
        self.last_modnum = 0
        self.total_modnum = 0

        if self.connect():
            print "DB connected. Check device ID={}...".format(did)
            if self.check_device_exists():
                self._isConnected = True
                print "Device found. Ready to proceed..."
                print 'Device is {}, Module version {}\n'.format(self.name, self.version)
            else:
                print "Device doesn't exist!"
                self.logger.error("FCS machine doesn't exist.")
                self.disconnect()
        else:
            self.logger.error('Cannot connect to FCS server.')
            print "Connection failed!"
