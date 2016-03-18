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

    def connect(self):
        return self._connectionManager.connect()
    
    def disconnect(self):
        self._connectionManager.disconnect()
        
    def checkDeviceExists(self):
        query = ("SELECT COUNT(*) FROM cal_data2 WHERE colmachinenum='{}'".format(self.id))
        result = self._connectionManager.query(query)
        if result is not None and result[0][0] > 0:
            return True
        else:
            return False

    def __init__(self, id):
        self.id = id
        