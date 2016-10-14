#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw
"""

# Machine mode definitions
OFFLINE = 'm0'
MANUAL_MODE = 'm1'
SEMI_AUTO_MODE = 'm2'
AUTO_MODE = 'm3'

# Machine status definitions
IDLE = 0
RUNNING = 1
CHG_MOLD = 2
CHG_MATERIAL = 3
SETUP = 4
NOJOB = 5

# Machine error code definitions
ERROR_LIST = {
    'X2': 999,
    'X5': 100,
    'X6': 200,
    'X7': 300,
    'X8': 400,
    'X9': 500,
}