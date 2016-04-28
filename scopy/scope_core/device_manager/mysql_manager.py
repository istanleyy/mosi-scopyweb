import mysql.connector
from mysql.connector import errorcode
from abstract_manager import AbstractConnectionManager
from scope_core.config import settings

class MySqlConnectionManager(AbstractConnectionManager):
    
    connection = None
    
    def connect(self):
        result = False
        try:
            self.connection = mysql.connector.connect(**settings.MYSQL_CONFIG)
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
        self.connection.close()
        
    def query(self, queryString):
        try:
            cursor = self.connection.cursor()
        except mysql.connector.Error:
            self.connection = mysql.connector.connect(**settings.MYSQL_CONFIG)
            cursor = self.connection.cursor()
        
        cursor.execute(queryString)
        result = cursor.fetchall()
        cursor.close()
        return result
        