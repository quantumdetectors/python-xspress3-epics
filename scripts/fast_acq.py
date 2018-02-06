#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import logging
import pprint
import time
from xspress3 import Xspress3, HDF5

logging.basicConfig(level=logging.INFO)


# Create device
x3 = Xspress3('XSPRESS3-EXAMPLE')

# Set trigger mode to internal
#   num images 10
#   exposure time 0.01s
x3.set(trigger_mode='Internal', num_images=10, exposure_time=0.01)

# Get current configuration
print 'Device Config'
pprint.pprint(x3.get())

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
    size = h5.size()
    print 'File Dimensions:', size

    for f in range(size['frames']):
        print 'Frame {f}'.format(f=f)

        for c in range(size['channels']):
            print 'Ch {c}: Time {t} Events {e}'.format(c=c, t=h5.sca(c,f,0), e=h5.sca(c,f,3))
            print '   MCA Counts {cts}'.format(cts=sum(h5.mca(c,f)))

