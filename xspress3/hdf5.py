# -*- coding: utf-8 -*-
import logging

import h5py
import numpy as np


class HDF5:

    def __init__(self, file, logger=None):
        self.logger = logger or logging.getLogger(__name__)

        self.logger.info('Loading {file}'.format(file=file))
        self._file = h5py.File(file, 'r')
        self._data = np.array(self._file.get('entry/instrument/detector/data'))

        self._frames = self._data.shape[0]
        self._channels = self._data.shape[1]
        self._bins = self._data.shape[2]

        self.logger.debug('Data is of size: {chans} channels, {frames} frames, {bins} bins per MCA'.format(chans=self._channels, frames=self._frames, bins=self._data.shape[2]))

        self._attrs = self._file.get('entry/instrument/detector/NDAttributes')


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.logger.debug('Closing file')
        self.close()


    def size(self):
        return {
            'channels': self._channels,
            'frames': self._frames,
            'bins': self._bins
        }


    def close(self):
        self._file.close()


    def mca(self, chan, frameno):
        assert chan < self._channels, 'Channel {chan} out of range of channels {chans}'.format(chan=chan, chans=self._channels)
        assert frameno < self._frames, 'Frame no {fr} out of range of frames {frs}'.format(fr=frameno, frs=self._frames)

        return self._data[frameno,chan,:].astype(int).tolist()


    # Scalars:
    #   0 = Time in ticks
    #   1 = ResetTicks
    #   2 = ResetCount
    #   3 = AllEvent
    #   4 = AllGood
    #   5 = InWindow 0
    #   6 = InWindow 1
    #   7 = PileUp
    #   
    def sca(self, chan, frameno, sca):
        assert chan < self._channels, 'Channel {chan} out of range of channels {chans}'.format(chan=chan, chans=self._channels)
        assert frameno < self._frames, 'Frame no {fr} out of range of frames {frs}'.format(fr=frameno, frs=self._frames)

        attrid = 'CHAN{chan}SCA{sca}'.format(chan=(chan+1), sca=sca)
        attr = np.array(self._attrs.get(attrid))

        assert attr is not None, 'No such attribute {attr}'.format(attr=attrid)
        return attr[frameno]


    def dtc(self, chan, frameno):
        assert chan < self._channels, 'Channel {chan} out of range of channels {chans}'.format(chan=chan, chans=self._channels)
        assert frameno < self._frames, 'Frame no {fr} out of range of frames {frs}'.format(fr=frameno, frs=self._frames)

        dtfid = 'CHAN{chan}DTFACTOR'.format(chan=(chan+1))
        dtf = np.array(self._attrs.get(dtfid))

        assert dtf is not None, 'No such attribute {attr}'.format(attr=attrid)

        dtpid = 'CHAN{chan}DTPERCENT'.format(chan=(chan+1))
        dtp = np.array(self._attrs.get(dtpid))

        assert dtf is not None, 'No such attribute {attr}'.format(attr=attrid)

        return [dtf[frameno], dtp[frameno]]

