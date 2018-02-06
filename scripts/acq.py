#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from xspress3 import Xspress3, HDF5

logging.basicConfig(level=logging.INFO)


# Create device
x3 = Xspress3('XSPRESS3-EXAMPLE')

# Get a callback on each new frame
def frame_callback(frame):
    global x3
    print 'Frame {f}'.format(f=frame)
    for c in range(x3.channels()):
        print '  Ch {ch} Time {t} Events {e} Reset {r}'.format(ch=c, t=x3.sca(c,0)/80e6, e=x3.sca(c,3), r=x3.sca(c,2))
        print '    MCA', x3.mca(c)

x3.add_frame_callback(frame_callback)


# Set trigger mode to internal
#   num images 10
#   exp time 0.5s
x3.set(trigger_mode='Internal', num_images=10, exposure_time=0.5)

# Get current configuration
print 'Device Config', x3.get()


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
