#!/usr/bin/env python

"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

barcode.py
    Implements barcode scanner compatibility to enable data input.
"""

from evdev import *
from select import select
import threading, time

keys = {
    # evdev scancodes are ASCII codes
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
    20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT',
}

scannerInstance = None

def getScannerInstance(operatorio):
    global scannerInstance
    if scannerInstance is None:
        scannerInstance = Scanner(operatorio)
    return scannerInstance

class Scanner(threading.Thread):

    def run(self):
        print "Initializing barcode scanner..."
        self.device = self.getScanner()
        while True:
            select([self.device], [], [])
            self.getBarcode()

    def getScanner(self):
        print "##### ANCHOR #####"
        dev_found = False
        while not dev_found:
            #try:
            scanner = InputDevice('/dev/input/event0')
            print scanner
            dev_found = True
            return scanner
            #except OSError:
            #    print "Scanner not found, retrying..."
            #    time.sleep(3)
    
    def getBarcode(self):
        try:
            for event in self.device.read():
                if event.type == ecodes.EV_KEY:
                    data = categorize(event)
                    if event.type == 1 and event.value == 1 and data.scancode != 42 and data.scancode < 54:
                        if data.scancode == 28:
                            print barcode
                            self.operatorio.update_display(barcode)
                            barcode = ''
                        else:
                            barcode += keys[data.scancode]
        except AttributeError:
            print "error parsing barcode stream"
        except IOError:
            print "error capturing input event"
            self.device = self.getScanner()

    def __init__(self, operatorio):
        threading.Thread.__init__(self)
        self.daemon = True
        self.operatorio = operatorio
        self.barcode = ''
