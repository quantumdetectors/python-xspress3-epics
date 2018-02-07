#!/usr/bin/env python
from setuptools import setup

setup(
    name             = 'xspress3',
    version          = '1.0.0',
    author           = 'Quantum Detectors',
    author_email     = 'info@quantumdetectors.com',
    url              = 'https://github.com/quantumdetectors/python-xspress3-epics',
    download_url     = 'https://github.com/quantumdetectors/python-xspress3-epics',
    license          = 'GPL',
    description      = "Xspress 3 EPICS Device",
    packages         = ['xspress3'],
    platforms        = ['Windows', 'Linux', 'Mac OS X'],
    install_requires = [
        'h5py',
        'numpy'
    ],
    classifiers      = [
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering'
    ],
)
