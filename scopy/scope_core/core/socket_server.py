"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

socket_server.py
    Simple socket server using threads to communicate with Scope server
"""

import socket, select
import sys
import logging
from thread import *
from threading import Thread
import job_control
from scope_core.config import settings
from . import xmlparser
from . import request_sender

class SocketServer(Thread):
    _instance = None
    _logger = None
    # For testing
    isCO = False
    isDT = False

    def clientthread(self, conn):
        """Function for handling connections. This will be used to create threads."""
        while True:
            # Receiving from client
            data = conn.recv(2048)
            msg = data.strip(' \t\n\r')
            if len(msg) > 0:
                print "Socket received:\n{0}".format(msg)
            reply = 'true:unknown message'
            if not data:
                break
            elif msg == 'bye':
                SocketServer._logger.info('Magic word received, closing connection.')
                break
            elif msg[0] != '<':
                msgContent = msg.split(':', 1)
                if msgContent[0] == 'ServerError':
                    #print '\033[91m' + '[ServerError] ' + msgContent[1] + '\033[0m'
                    SocketServer._logger.warning('[ServerError] {0}'.format(msgContent[1]))
                    if msgContent[1] == 'msg sync':
                        job_control.setMsgBlock()
                    reply = 'false:errorAck'
                elif msgContent[0] == 'ServerMsg':
                    #print '\033[93m' + '[ServerMessage] ' + msgContent[1] + '\033[0m'
                    SocketServer._logger.info('[ServerMessage] {0}'.format(msgContent[1]))
                    if msgContent[1] == 'alive check':
                        job_control.sendUpdateMsg()
                    elif msgContent[1] == 'sync ok':
                        job_control.sendMsgBuffer()
                    reply = 'false:ok'
                elif msgContent[0] == 'ScanManager':
                    #print '\033[93m' + '[BarcodeActivity] ' + msgContent[1] + '\033[0m'
                    SocketServer._logger.warning('[BarcodeActivity] {0}'.format(msgContent[1]))
                    if msgContent[1] == 'initiate':
                        reply = job_control.getCurrentJobName()
                    else:
                        reply = job_control.processBarcodeActivity(msgContent[1])
                elif msgContent[0] == 'ServerAction':
                    #print '\033[93m' + '[ServerAction] ' + msgContent[1] + '\033[0m'
                    SocketServer._logger.warning('[ServerAction] {0}'.format(msgContent[1]))
                    if job_control.processServerAction(msgContent[1]):
                        reply = 'false:ok'
                    else:
                        reply = 'true:cannot perform server action'
                elif msgContent[0] == 'test-toggleco':
                    # For testing, should remove this elif block in production!
                    if not self.isCO:
                        # Send job-terminating change-over msg
                        job_control.sendEventMsg(6, 'NJ')
                    self.isCO = not self.isCO
                    reply = 'false:test'
                elif msgContent[0] == 'test-toggledt':
                    # For testing, should remove this elif block in production!
                    if not self.isDT:
                        # Downtime begins
                        job_control.sendEventMsg(4)
                    else:
                        # Downtime ends
                        job_control.sendEventMsg(1, 'X2')
                    self.isDT = not self.isDT
                    reply = 'false:test'
                elif msgContent[0] == 'test-jobstart':
                    # For testing, should remove this elif block in production!
                    # Send job start message
                    job_control.sendEventMsg(1)
                    reply = 'false:test'
                else:
                    #print 'Received unknown message: ' + msg
                    SocketServer._logger.error('Socket server received unknown message: {0}'.format(msg))
            elif xmlparser.isScopeXml(msg):
                #print 'Received Scope message.'
                SocketServer._logger.info('Received Scope message.')
                reply = 'false:ok'
            else:
                break

            conn.sendall(reply)
            #print 'Local reply: ' + reply

    def listen_bcast(self, sock):
        """Listen for and handle broadcast messages."""
        print 'Broadcast listener created...'
        while True:
            bmsg = select.select([sock], [], [])
            msg = bmsg[0][0].recv(1024)
            msg = msg.strip(' \t\n\r')
            if msg == 'ServerMsg:alive check':
                request_sender.sendBcastReply()
            elif msg[:7] == 'PeerMsg':
                msgdecode = msg.split(':')
                header = msgdecode[0]
                body = msgdecode[1]
                sender = header.split('-')[1]
                if sender != settings.DEVICE_INFO['ID']:
                    job_control.processBarcodeActivity(body)
            else:
                print 'Received broadcast message: {0}'.format(msg)
                #self.logger.info('Received broadcast message: ' + msg)

    def send_bcast(self, msg):
        """Send broadcast message."""
        self.bcast_sock.sendto(
            msg,
            (settings.SOCKET_SERVER['BCAST_ADDR'], settings.SOCKET_SERVER['BCAST_PORT'])
            )
        print 'Send notification to peers: {}'.format(msg)

    # Over-rides Thread.run
    def run(self):
        print 'Socket now listening...\n'
        while not self.cancelled:
            # wait to accept a connection - blocking call
            (conn, addr) = self.msg_sock.accept()
            print '\nConnected with ' + addr[0] + ':' + str(addr[1])
            # start new thread takes 1st argument as a function name to be run,
            # second is the tuple of arguments to the function.
            start_new_thread(self.clientthread, (conn,))

    # Ends the running server thread
    def cancel(self):
        """Set listener thread running status cancelled to True, and close the sockets."""
        self.cancelled = True
        self.msg_sock.close()
        self.bcast_sock.close()

    @staticmethod
    def get_instance():
        """Returns a singleton module instance"""
        if SocketServer._instance is None:
            SocketServer()
        return SocketServer._instance

    def __init__(self):
        super(SocketServer, self).__init__()
        if SocketServer._instance is not None:
            # Throw exception maybe?
            pass
        else:
            SocketServer._instance = self
            SocketServer._logger = logging.getLogger('scopepi.messaging')
            self.daemon = True
            self.cancelled = False

            self.bcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.bcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.bcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.bcast_sock.setblocking(0)

            self.msg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.msg_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                self.bcast_sock.bind((settings.SOCKET_SERVER['BCAST_ADDR'], settings.SOCKET_SERVER['BCAST_PORT']))
                self.msg_sock.bind((settings.SOCKET_SERVER['HOST'], settings.SOCKET_SERVER['PORT']))
            except socket.error as msg:
                if msg[0] != 48 and msg[0] != 98:
                    errmsg = 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
                    print errmsg
                    SocketServer._logger.exception(errmsg)
                    sys.exit()

            print 'Socket bind complete!'
            # Start listening on SocketServers
            start_new_thread(self.listen_bcast, (self.bcast_sock,))
            self.msg_sock.listen(5)
            self.start()
