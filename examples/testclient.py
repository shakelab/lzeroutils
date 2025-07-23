#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for LZEROClient to request POS data from LZEROServer.

Author: Valerio Poggi
Date: 2025-07-07
"""

from lzeroutils import LZEROClient, convert_wgs_to_utm

# Initialize client with server IP and port
l0c = LZEROClient('158.110.30.115', port=5000)

# Request data for station FLEE and time interval
data = l0c.get_data(
    station='FLEE',
    starttime='2025-06-30T10:45:11',
    endtime='2025-06-30T10:49:11'
)

data_streams = convert_wgs_to_utm(data)