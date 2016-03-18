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