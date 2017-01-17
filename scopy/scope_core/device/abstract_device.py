"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

abstract_device.py
    Any device implementation for Scope must extend from this class to provide
    required methods
"""

import abc

class AbstractDevice(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        """Provide name of the concrete device implementation"""
        return

    @abc.abstractproperty
    def provider(self):
        """Provide the name of the provider for the device implementation"""
        return

    @abc.abstractproperty
    def version(self):
        """Provide the version of the device implementation"""
        return

    @abc.abstractproperty
    def description(self):
        """Provide a brief description about the concrete device implementation"""
        return

    @abc.abstractproperty
    def connectionManager(self):
        """Get the connection manager for the concrete device"""
        return

    @connectionManager.setter
    def connectionManager(self, newObj):
        """Sets the connection manager for the concrete device"""
        return

    @abc.abstractproperty
    def is_connected(self):
        """The connection status of the concrete device"""
        return

    @abc.abstractmethod
    def getDeviceStatus(self):
        """Retrieve device's operating status"""
        return

    @abc.abstractmethod
    def getAlarmStatus(self):
        """Retrieve device's alarm status"""
        return

    @abc.abstractmethod
    def getProductionStatus(self):
        """Retrieve device's production status"""
        return

    @abc.abstractmethod
    def device_id(self):
        """Returns device id of the corresponding instance"""
        return

    @abc.abstractmethod
    def calc_output(self, raw_data):
        """Calculates the total output according to device setup"""
        return

    @abc.abstractmethod
    def get_output(self):
        """Returns total output counter value"""
        return

    @abc.abstractmethod
    def update_output(self, new_val):
        """Updates total output counter to new_val"""
        return

    @abc.abstractmethod
    def reset_output(self):
        """Resets the total output counter"""
        return
