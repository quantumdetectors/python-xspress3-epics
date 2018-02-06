#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging

from xspress3 import HDF5


logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('file', help='hdf5 file to convert to csv')

args = parser.parse_args()


binsperkv = 10
tickspers = 80e6


root = args.file.replace('.hdf5', '')

scalars = {
    'counts': 3,
    'time': 0,
}



with HDF5(args.file) as h5:
    size = h5.size()

    for f in range(size['frames']):
        lines = []

        # Header
        line = ['channel']
        for c in range(size['channels']):
            line.append(str(c))

        lines.append(','.join(line))  
        
        for scn,sca in scalars.iteritems():
            line = [scn]
            for c in range(size['channels']):
                v = h5.sca(c, f, sca)

                if scn == 'time':
                    v = v/tickspers

                line.append(str(v))

            lines.append(','.join(line))


        # Deadtime %
        line = ['dt']
        for c in range(size['channels']):
            line.append(str(h5.dtc(c, f)[1]))

        lines.append(','.join(line))


        # MCA
        for e in range(size['bins']):
            line = [str(e*binsperkv)]

            for c in range(size['channels']):
                line.append(str(h5.mca(c, f)[e]))

            lines.append(','.join(line))

        with open('{root}_frame{f}.csv'.format(root=root, f=f), 'w') as csv:
            csv.write("\n".join(lines)+"\n")
