"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

mysql_manager.py
    A connection manager to query a MySQL server using Oracle's python connector
"""

import logging
import mysql.connector
import mysql.connector.pooling
from mysql.connector import errorcode
from abstract_manager import AbstractConnectionManager
from scope_core.config import settings

class MySqlConnectionManager(AbstractConnectionManager):
    """The conneciton manager maintains a connection pool to execute queries from other modules."""
    logger = None
    cnxpool = None
    connection = None

    def __init__(self):
        self.logger = logging.getLogger('scopepi.debug')
        self.create_cxnpool()

    def create_cxnpool(self):
        try:
            self.cnxpool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="fcsdb",
                pool_size=3,
                pool_reset_session=True,
                **settings.MYSQL_CONFIG)
        except mysql.connector.Error as err:
            self.logger.exception(err.message)

    def connect(self):
        result = False
        try:
            if self.cnxpool:
                self.connection = self.cnxpool.get_connection()
                cursor = self.connection.cursor()
                #self.connection.set_character_set('utf8')
                cursor.execute('SET NAMES utf8;')
                cursor.execute('SET CHARACTER SET utf8;')
                cursor.execute('SET character_set_connection=utf8;')
                cursor.close()
                result = True
            return result
        except mysql.connector.Error as err:
            self.logger.exception(err.message)
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print "Invalid username or password!"
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print "Database doesn't exist!"
            else:
                print err
        finally:
            self.disconnect()

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def query(self, queryString):
        """Executes the query defined by queryString."""
        result = None
        try:
            self.connection = self.cnxpool.get_connection()
            cursor = self.connection.cursor()
            if cursor:
                cursor.execute(queryString)
                result = cursor.fetchone()
                cursor.close()
            return result
        except mysql.connector.Error:
            print "MySQL connection error in query."
        finally:
            self.disconnect()
