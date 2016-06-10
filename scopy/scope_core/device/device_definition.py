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
IDLE = 's0'
RUNNING = 's1'
CHG_MOLD = 's2'
CHG_MATERIAL = 's3'
MOLD_ADJUST = 's4'