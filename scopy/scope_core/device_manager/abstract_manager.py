"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

abstract_manager.py
    All connection managers for the Scope device to support different protocols
    must extend from this abstract class to implement required methods
"""

import abc

class AbstractConnectionManager(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def connect(self):
        # Define neccessary actions for the concrete connection manager to establish a connection
        return

    @abc.abstractmethod
    def disconnect(self):
        # Define disconnection policies for the concrete connection manager
        return