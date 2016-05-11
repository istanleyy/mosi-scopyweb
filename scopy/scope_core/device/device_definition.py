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
OFFLINE = 0
MANUAL_MODE = 1
SEMI_AUTO_MODE = 2
AUTO_MODE = 3

# Machine status definitions
RUNNING = 0
CHG_MOLD = 1
CHG_MATERIAL = 2
MOLD_ADJUST = 3