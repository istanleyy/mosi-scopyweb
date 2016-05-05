from abstract_device import AbstractDevice
from scope_core.device_manager.mysql_manager import MySqlConnectionManager


class FCSInjectionDevice_db(AbstractDevice):

    ##############################################
    # Define inherit properties and moethods
    ##############################################

    @property
    def name(self):
        return 'FCS Injection/DB'

    @property
    def provider(self):
        return 'MOSi Technologies, LLC'

    @property
    def version(self):
        return '0.1.0'

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
        query = ("SELECT COUNT(*) FROM cal_data2 WHERE colmachinenum='{}'".format(self.id))
        result = self._connectionManager.query(query)
        if result is not None and result[0] > 0:
            return True
        else:
            return False

    def getDeviceStatus(self):
        query = (
            "SELECT MachineStatus FROM cal_data2 WHERE colmachinenum='{}' ORDER BY DateTime DESC LIMIT 1".format(self.id)
            )
        result = self._connectionManager.query(query)
        if result is not None:
            print(result)
            return result
        else:
            return "fail"
    
    def getAlarmStatus(self):
        query = (
            "SELECT strtime,alarmid,alarmstatus FROM a_alarm AS A INNER JOIN (SELECT DISTINCT injid FROM cal_data2 WHERE colmachinenum='{}') AS C ON A.injid=C.injid ORDER BY strtime DESC LIMIT 1".format(self.id)
            )
        result = self._connectionManager.query(query)
        if result is not None:
            print(result)
            return result
        else:
            return "fail"
            
    def getProductionStatus(self):
        query = (
            "SELECT CycleTime,CurrBoxNum,ModName FROM cal_data2 WHERE colmachinenum='{}' ORDER BY DateTime DESC LIMIT 1".format(self.id)
            )
        result = self._connectionManager.query(query)
        if result is not None:
            print(result)
            return result
        else:
            return "fail"

    def __init__(self, id):
        self.id = id
        if self.connect():
            print("DB connected. Check device ID={}...".format(id))
            if self.checkDeviceExists():
                self.isConnected = True
                FCSInjectionDevice_db.activeDevice = self
                print("Device found. Ready to proceed...")
                print('Device is {}, Module version {}\n'.format(self.name, self.version))
            else:
                print("Device doesn't exist!")
                self.disconnect()
        else:
            print("Connection failed!")
        