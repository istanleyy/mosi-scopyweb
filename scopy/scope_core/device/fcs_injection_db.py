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

import platform
import device_definition as const
from abstract_device import AbstractDevice
from scope_core.device_manager.mysql_manager import MySqlConnectionManager
from scope_core.models import Machine

#if platform.system() != 'Darwin':
#    import RPi.GPIO as GPIO

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

    _connectionManager = MySqlConnectionManager()

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

    # Setup RPi GPIO
    #if platform.system() != 'Darwin':
    #    GPIO.setmode(GPIO.BCM)
    #    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def connect(self):
        return self._connectionManager.connect()
    
    def disconnect(self):
        self._connectionManager.disconnect()
        self.isConnected = False
        
    def checkDeviceExists(self):
        query = ("SELECT COUNT(*) FROM cal_data2 WHERE colmachinenum='{}'".format(self.id))
        result = self._connectionManager.query(query)
        if result is not None and result[0] > 0:
            return True
        else:
            return False

    def getDeviceStatus(self):
        query = (
            "SELECT MachineStatus,MO FROM cal_data2 WHERE colmachinenum='{}' ORDER BY DateTime DESC LIMIT 1".format(self.id)
            )
        result = self._connectionManager.query(query)
        if result is not None:
            if settings.DEBUG:
                print(result)
            machine = Machine.objects.first()
            moldid = result[1]
            statuschange = False
            modechange = False
            """
            if platform.system() != 'Darwin':
                coswitch = GPIO.input(23)
            else:
                # Testing on OSX
                coswitch = True

            if not coswitch:
                status = const.CHG_MOLD
                if not machine.moldAdjustStatus:
                    machine.moldAdjustStatus = True
                    statuschange = True
            else:
                status = const.RUNNING if result[0] != 0 else const.IDLE
                if machine.moldAdjustStatus:
                    machine.moldAdjustStatus = False
                    statuschange = True
            """
            modestr = result[0].encode('utf-8', 'ignore')
            if modestr[0] == '1':
                self.mode = const.MANUAL_MODE
                if machine.opmode != 1:
                    machine.opmode = 1
                    modechange = True
                    print('Device in manual mode.')
            elif modestr[0] == '2':
                self.mode = const.SEMI_AUTO_MODE
                if machine.opmode != 2:
                    machine.opmode = 2
                    modechange = True
                    print('Device in semi-auto mode.')
            elif modestr[0] == '3':
                self.mode = const.AUTO_MODE
                if machine.opmode != 3:
                    machine.opmode = 3
                    machine.opstatus = const.RUNNING
                    modechange = True
                    print('Device in auto mode.')
            else:
                print('Device is offline!')
                self.mode = const.OFFLINE
                if machine.opmode != 0:
                    machine.opmode = 0
                    machine.opstatus = const.IDLE
                    modechange = True

            if statuschange or modechange:
                machine.save()
            return (self.mode, self.status, moldid)
        else:
            return "fail"
    
    def getAlarmStatus(self):
        query = (
            "SELECT alarmid,alarmstatus FROM a_alarm AS A INNER JOIN (SELECT DISTINCT injid FROM cal_data2 WHERE colmachinenum='{}') AS C ON A.injid=C.injid ORDER BY strtime DESC LIMIT 1".format(self.id)
            )
        result = self._connectionManager.query(query)
        if result is not None and result[0] in const.ERROR_LIST:
            print(result)
            if result[1] == 1:
                for errtag, errcode in const.ERROR_LIST.iteritems():
                    if result[0] == errcode:
		                return (errtag, True)
                return ('X2', True)
            else:
                return ('', False)
        else:
            return "fail"
            
    def getProductionStatus(self):
        query = (
            "SELECT CycleTime,ModNum FROM cal_data2 WHERE colmachinenum='{}' ORDER BY DateTime DESC LIMIT 1".format(self.id)
            )
        result = self._connectionManager.query(query)
        print(result)
        if result is not None:
            return result
        else:
            return "fail"

    def __init__(self, id):
        self.id = id
        self.mode = const.OFFLINE
        self.status = const.IDLE
        if self.connect():
            print("DB connected. Check device ID={}...".format(id))
            if self.checkDeviceExists():
                self.isConnected = True
                print("Device found. Ready to proceed...")
                print('Device is {}, Module version {}\n'.format(self.name, self.version))
            else:
                print("Device doesn't exist!")
                self.disconnect()
        else:
            print("Connection failed!")
