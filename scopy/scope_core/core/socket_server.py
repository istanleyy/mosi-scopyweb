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
from scope_core.config import settings
from . import xmlparser
from . import job_control
from . import request_sender

class SocketServer(Thread):
    logger = logging.getLogger('scopepi.messaging')

    # For testing
    isCO = False
    isDT = False
    
    # Function for handling connections. This will be used to create threads
    def clientthread(self, conn):
        # Infinite loop so that function do not terminate and thread do not end.
        while True: 
            # Receiving from client
            data = conn.recv(2048)
            msg = data.strip(' \t\n\r')
            reply = 'true:unknown message'
            if not data:
                break
            elif msg == 'bye':
                self.logger.info('Magic word received, closing connection.')
                break
            elif msg[0] != '<':
                msgContent = msg.split(':', 1)
                if msgContent[0] == 'ServerError':
                    #print '\033[91m' + '[ServerError] ' + msgContent[1] + '\033[0m'
                    self.logger.warning('[ServerError] {0}'.format(msgContent[1]))
                    if msgContent[1] == 'msg sync':
                        job_control.setMsgBlock()
                    reply = 'false:errorAck'
                elif msgContent[0] == 'ServerMsg':
                    #print '\033[93m' + '[ServerMessage] ' + msgContent[1] + '\033[0m'
                    self.logger.info('[ServerMessage] {0}'.format(msgContent[1]))
                    if msgContent[1] == 'alive check':
                        job_control.sendUpdateMsg()
                    elif msgContent[1] == 'sync ok':
                        job_control.sendMsgBuffer()
                    reply = 'false:ok'
                elif msgContent[0] == 'ScanManager':
                    #print '\033[93m' + '[BarcodeActivity] ' + msgContent[1] + '\033[0m'
                    self.logger.info('[BarcodeActivity] {0}'.format(msgContent[1]))
                    if msgContent[1] == 'initiate':
                        reply = 'scan'
                    if job_control.processBarcodeActivity(msgContent[1]):
                        reply = 'ok'
                    else:
                        reply = 'fail'
                elif msgContent[0] == 'ServerAction':
                    #print '\033[93m' + '[ServerAction] ' + msgContent[1] + '\033[0m'
                    self.logger.warning('[ServerAction] {0}'.format(msgContent[1]))
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
                    self.logger.error('Socket server received unknown message: {0}'.format(msg))
            elif xmlparser.isScopeXml(msg):
                #print 'Received Scope message.'
                self.logger.info('Received Scope message.')
                reply = 'false:ok'
            else:
                break
     
            conn.sendall(reply)
            #print 'Local reply: ' + reply

    def listen_bcast(self, sock):
        print 'Broadcast listener created...'
        while True:
            result = select.select([sock],[],[])
            msg = result[0][0].recv(1024)
            msg = msg.strip(' \t\n\r')
            if msg == 'ServerMsg:alive check':
                request_sender.sendBcastReply()
            else:
                #print 'Received broadcast message: {0}'.format(msg)
                self.logger.info('Received broadcast message: ' + msg)

    # Over-rides Thread.run
    def run(self):
        print 'Socket now listening...\n'
        while not self.cancelled:
            # wait to accept a connection - blocking call
            (conn, addr) = self.s.accept()
            print '\nConnected with ' + addr[0] + ':' + str(addr[1])
     
            # start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            start_new_thread(self.clientthread, (conn,))
 
        self.s.close()
        self.bs.close()
        
    # Ends the running server thread
    def cancel(self):
        self.cancelled = True

    def __init__(self):
        super(SocketServer, self).__init__()
        self.daemon = True
        self.cancelled = False
        
        self.bs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bs.bind((settings.SOCKET_SERVER['BCAST_ADDR'], settings.SOCKET_SERVER['BCAST_PORT']))
        self.bs.setblocking(0)
        start_new_thread(self.listen_bcast, (self.bs,))

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print 'Message socket created...'
        #Bind socket to local host and port
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.s.bind((settings.SOCKET_SERVER['HOST'], settings.SOCKET_SERVER['PORT']))
        except socket.error as msg:
            if msg[0] != 48 and msg[0] != 98:
                print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
                self.logger.exception('Bind failed. Error Code: {0} Message: {1}'.format(msg[0], msg[1]))
                sys.exit()
     
        print 'Socket bind complete!'
 
        #Start listening on socket
        self.s.listen(5)