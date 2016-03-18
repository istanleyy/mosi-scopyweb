import abc

class AbstractDevice(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        # Provide name of the concrete device implementation
        return

    @abc.abstractproperty
    def provider(self):
        # Provide the name of the provider for the device implementation
        return

    @abc.abstractproperty
    def version(self):
        # Provide the version of the device implementation
        return

    @abc.abstractproperty
    def description(self):
        # Provide a brief description about the concrete device implementation
        return

    @abc.abstractproperty
    def connectionManager(self):
        # Get the connection manager for the concrete device
        return

    @connectionManager.setter
    def connectionManager(self, newObj):
        # Sets the connection manager for the concrete device
        return
