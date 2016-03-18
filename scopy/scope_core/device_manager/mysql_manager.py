import mysql.connector
from mysql.connector import errorcode
from abstract_manager import AbstractConnectionManager

class MySqlConnectionManager(AbstractConnectionManager):
    config = {
        'user': 'Sniper',
        'password': 'MOSi0916',
        'host': '192.168.2.210',
        'port': '3307',
        'database': 'FCSTEST',
        'connection_timeout': 30,
        'raise_on_warnings': True,
    }

    def connect(self):
        result = False
        try:
            global _connection
            global _cursor
            _connection = mysql.connector.connect(**self.config)
            _cursor = _connection.cursor()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Invalid username or password!")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database doesn't exist!")
            else:
                print(err)
        else:
            result = True
            return result
            
    def disconnect(self):
        _cursor.close()
        _connection.close()
        
    def query(self, queryString):
        _cursor.execute(queryString)
        result = _cursor.fetchall()
        return result
        