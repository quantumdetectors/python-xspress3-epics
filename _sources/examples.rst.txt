.. _examples:

Examples
========

Sources for these examples can be found in the `scripts <https://github.com/quantumdetectors/python-xspress3-epics/tree/master/scripts>`_ source folder

Basic acqusition
----------------

This type of script will work up to around 100-200Hz where EPICS can keep up with the PV changes.
At faster frame rates data must be saved to file

.. code-block:: python

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
    print 'Device Config'
    pprint.pprint(x3.get())


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


Fast Acquisition
----------------

For high frame rates save to hdf5 and readback scalar / mca values

.. code-block:: python

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

