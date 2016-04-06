import mysql.connector
from mysql.connector import errorcode
from abstract_manager import AbstractConnectionManager
from scope_core.config import settings

class MySqlConnectionManager(AbstractConnectionManager):

    def connect(self):
        result = False
        try:
            global _connection
            global _cursor
            _connection = mysql.connector.connect(**settings.MYSQL_CONFIG)
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
        