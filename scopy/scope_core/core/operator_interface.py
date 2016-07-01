"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

operator_interface.py
    Facilitates input and output devices to enable operator interactions
    with the system.
"""

from . import i2c_lcd_driver
from . import barcode

class OperatorIO:

    def __init__(self):
        self.lcd = i2c_lcd_driver.lcd()
        self.barcodeScanner = barcode.getScannerInstance(self)
        self.barcodeScanner.start()
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("MOSi ScopePi", 1)

    def update_display(self, newstr):
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("Got barcode:", 1)
        self.lcd.lcd_display_string(newstr, 2)
