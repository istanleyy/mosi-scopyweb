"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

socket_server.py
    Simple socket server using threads to communicate with Scope server
"""
 
import socket
import sys
from thread import *
from threading import Thread
from scope_core.config import settings
from . import xmlparser
from . import job_control

class SocketServer(Thread):
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
                print 'Magic word received, closing connection...'
                break
            elif msg[0] != '<':
                msgContent = msg.split(':', 1)
                if msgContent[0] == 'ServerError':
                    print '\033[91m' + '[ServerError] ' + msgContent[1] + '\033[0m'
                    if msgContent[1] == 'msg sync':
                        job_control.sendMsgBuffer()
                    reply = 'false:errorAck'
                elif msgContent[0] == 'ServerMsg':
                    print '\033[93m' + '[ServerMessage] ' + msgContent[1] + '\033[0m'
                    if msgContent[1] == 'alive check':
                        job_control.sendUpdateMsg()
                    reply = 'false:ok'
                elif msgContent[0] == 'test-toggleco':
                    # For testing, should remove this elif block in production!
                    if not self.isCO:
                        # Begin change-over
                        job_control.sendEventMsg(6, 'BG')
                    else:
                        # Change-over ends
                        job_control.sendEventMsg(6, 'ED')
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
                    print 'Received unknown message: ' + msg
            elif xmlparser.isScopeXml(msg):
                print 'Received Scope message.'
                reply = 'false:ok'
            else:
                break
     
            conn.sendall(reply)
            print 'Local reply: ' + reply
     
        # Close socket when done
        conn.close()
        
    # Over-rides Thread.run
    def run(self):
        print 'Socket now listening...\n'
        while not self.cancelled:
            # wait to accept a connection - blocking call
            (conn, addr) = self.s.accept()
            print '\nConnected with ' + addr[0] + ':' + str(addr[1])
     
            # start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            start_new_thread(self.clientthread ,(conn,))
 
        self.s.close()
        
    # Ends the running server thread
    def cancel(self):
        self.cancelled = True

    def __init__(self):
        super(SocketServer, self).__init__()
        self.daemon = True
        self.cancelled = False
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print 'Message socket created...'
 
        #Bind socket to local host and port
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.s.bind((settings.SOCKET_SERVER['HOST'], settings.SOCKET_SERVER['PORT']))
        except socket.error as msg:
            if msg[0] != 48:
                print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
                sys.exit()
     
        print 'Socket bind complete!'
 
        #Start listening on socket
        self.s.listen(5)