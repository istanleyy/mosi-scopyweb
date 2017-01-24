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
    """Device interface to define common properties and methods for ScopePi compatible connectors"""
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
    def connection_manager(self):
        """Get the connection manager for the concrete device"""
        return

    @connection_manager.setter
    def connection_manager(self, conn_obj):
        """Sets the connection manager for the concrete device"""
        return

    @abc.abstractproperty
    def is_connected(self):
        """The connection status of the concrete device"""
        return

    @abc.abstractproperty
    def total_output(self):
        """Total output counter"""
        return

    @total_output.setter
    def total_output(self, new_val):
        """Sets the total output counter value to new_val"""
        return

    @abc.abstractmethod
    def get_device_status(self):
        """Retrieve device's operating status"""
        return

    @abc.abstractmethod
    def get_alarm_status(self):
        """Retrieve device's alarm status"""
        return

    @abc.abstractmethod
    def get_production_status(self):
        """Retrieve device's production status"""
        return

    @abc.abstractmethod
    def device_id(self):
        """Returns device id of the corresponding instance"""
        return
