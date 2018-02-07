# python-xspress3-epics

A couple of simple classes to aid acquisition and data processing for the [Xspress 3 EPICS IOC](https://github.com/quantumdetectors/xspress3-epics/tree/qd-prod)

## Documentation
https://quantumdetectors.github.io/python-xspress3-epics/

### Acquiring

```python
x3 = Xspress3('XSPRESS3-EXAMPLE')
x3.set(trigger_mode='Internal', num_images=10, exposure_time=0.5)
x3.acquire()

while x3.acquiring():
    print 'Acquiring ... {num}/{tot}'.format(num=x3.num_acquired(), tot=x3.get('num_images'))
    time.sleep(1)
    
```

### Reading hdf5

```python
with HDF5(file) as h5:
    size = h5.size()
    print 'File Dimensions:', size

    for f in range(size['frames']):
        print 'Frame {f}'.format(f=f)

        for c in range(size['channels']):
            print 'Ch {c}: Time {t} Events {e}'.format(c=c, t=h5.sca(c,f,0), e=h5.sca(c,f,3))
            print '   MCA Counts {cts}'.format(cts=sum(h5.mca(c,f)))
```
