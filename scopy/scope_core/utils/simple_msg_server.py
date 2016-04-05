'''
    Simple socket server using threads
'''
 
import socket
import sys
from thread import *
from threading import Thread
 
HOST = ''       # Symbolic name meaning all available interfaces
PORT = 26674    # Arbitrary non-privileged port

class SimpleMsgServer(Thread):
 
    # Function for handling connections. This will be used to create threads
    def clientthread(self, conn):
        # Sending message to connected client
        conn.send('Scopy Socket Test. Type something and hit enter:\n') #send only takes string
     
        #infinite loop so that function do not terminate and thread do not end.
        while True: 
            #Receiving from client
            data = conn.recv(1024)
            reply = 'OK...' + data
            if not data: 
                break
     
            conn.sendall(reply)
     
        #came out of loop
        conn.close()
        
    # Over-rides Thread.run
    def run(self):
        print 'Socket now listening...\n'
        while not self.cancelled:
            #wait to accept a connection - blocking call
            conn, addr = self.s.accept()
            print 'Connected with ' + addr[0] + ':' + str(addr[1])
     
            #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            start_new_thread(clientthread ,(conn,))
 
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
            self.s.bind((HOST, PORT))
        except socket.error as msg:
            print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]
            sys.exit()
     
        print 'Socket bind complete!'
 
        #Start listening on socket
        self.s.listen(10)