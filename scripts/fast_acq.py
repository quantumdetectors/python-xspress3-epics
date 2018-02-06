#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import logging
import time
from xspress3 import Xspress3, HDF5

logging.basicConfig(level=logging.DEBUG)


# Create device
x3 = Xspress3('XSPRESS3-EXAMPLE')

# Set trigger mode to internal
x3.set(trigger_mode='Internal')

# Get current configuration
print 'Device Config', x3.get()

# Enable file saving
file = x3.file_saving(True)
print file


# Start acquiring
print 'Starting Acquisition'
x3.acquire()

# Wait for finish
while x3.acquiring():
    try:
        print 'Acquiring ... {num}/{tot}'.format(num=x3.num_acquired(), tot=x3.get('num_images'))
        time.sleep(1)
    except KeyboardInterrupt:
            x3.stop()

print 'Acquisition Finished'


# Read resulting hdf5
with HDF5(file) as h5:
    print h5.size()
