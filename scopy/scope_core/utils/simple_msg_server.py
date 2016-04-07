"""
Simple socket server using threads
"""
 
import socket
import sys
from thread import *
from threading import Thread
from scope_core.config import settings
from scope_core.utils import xmlparser

class SimpleMsgServer(Thread):
 
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
                    reply = 'false:errorAck'
                elif msgContent[0] == 'ServerMsg':
                    print '\033[93m' + '[ServerMessage] ' + msgContent[1] + '\033[0m'
                    reply = 'false:ok'
                else:
                    print 'Received unknown message: ' + msg
            elif xmlparser.isScopeXml(msg):
                print 'Received Scope message.'
                reply = 'false:ok'
            else:
                break
     
            conn.sendall(reply)
     
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
        super(SimpleMsgServer, self).__init__()
        self.daemon = True
        self.cancelled = False
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print 'Message socket created...'
 
        #Bind socket to local host and port
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.s.bind((settings.SIMPLE_MSG_SERVER['HOST'], settings.SIMPLE_MSG_SERVER['PORT']))
        except socket.error as msg:
            print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
            sys.exit()
     
        print 'Socket bind complete!'
 
        #Start listening on socket
        self.s.listen(5)