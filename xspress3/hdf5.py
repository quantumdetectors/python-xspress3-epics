# -*- coding: utf-8 -*-
import logging

import h5py
import numpy as np


class HDF5:
    """Xspress 3 HDF5 Parser

    A class for parsing Xspress 3 HDF5 files.
    Is context managed so files are automatically closed when done

    Example:
      >>> with HDF5(file) as h5:
      >>>     h5.size()
      >>>     h5.mca(0,0)
      >>>
      >>> {'channels': 1, 'frames': 4, 'bins': 4096}
      >>> [0,0,0....0]
    """

    def __init__(self, file, logger=None):
        """ Create an Xspress 3 HDF5 parser instance

        Args:
            file (string): the hdf5 file to open

        """
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
        """ Returns the dimensions of the HDF5 file

        Returns:
            size (dict): the hdf5 file dimensions
            
                * channels (int): number of channels in the file
                * frames (int): number of frames in the file
                * bins (int): number of bins per mca in the file

        """
        return {
            'channels': self._channels,
            'frames': self._frames,
            'bins': self._bins
        }


    def close(self):
        """ Manually close the hdf5 file """

        self._file.close()


    def mca(self, chan, frameno):
        """ Returns the specified MCA

        Args:
            chan (int): the channel to return an MCA for

            frameno (int): the frame number to return an MCA for

        Returns:
            mca (list[int]): the MCA as a list (usually with 4096 elements)

        """
        assert chan < self._channels, 'Channel {chan} out of range of channels {chans}'.format(chan=chan, chans=self._channels)
        assert frameno < self._frames, 'Frame no {fr} out of range of frames {frs}'.format(fr=frameno, frs=self._frames)

        return self._data[frameno,chan,:].astype(int).tolist()


    def sca(self, chan, frameno, sca):
        """ Returns the specified scalar

        Aargs:
            chan (int): channel number to return scalar for, zero offset

            frameno (int): the frame number to return scalar for, zero offset

            sca (int): scalar to return

        Returns:
            scalar (int): the specified scalar value

    
        Available scalars:
            0. Time in ticks
            1. ResetTicks
            2. ResetCount
            3. AllEvent
            4. AllGood
            5. InWindow 0
            6. InWindow 1
            7. PileUp

        """
        assert chan < self._channels, 'Channel {chan} out of range of channels {chans}'.format(chan=chan, chans=self._channels)
        assert frameno < self._frames, 'Frame no {fr} out of range of frames {frs}'.format(fr=frameno, frs=self._frames)

        attrid = 'CHAN{chan}SCA{sca}'.format(chan=(chan+1), sca=sca)
        attr = np.array(self._attrs.get(attrid))

        assert attr is not None, 'No such attribute {attr}'.format(attr=attrid)
        return attr[frameno]


    def dtc(self, chan, frameno):
        """ Returns the specified deadtime correction parameters

        Args:
            chan (int): channel number to return scalar for, zero offset

            frameno (int): the frame number to return scalar for, zero offset

        Returns:
            dtc_params (list): returns a list of two dead time correction params:
                0. dead time correction factor
                1. dead time percentage

        """
        assert chan < self._channels, 'Channel {chan} out of range of channels {chans}'.format(chan=chan, chans=self._channels)
        assert frameno < self._frames, 'Frame no {fr} out of range of frames {frs}'.format(fr=frameno, frs=self._frames)

        dtfid = 'CHAN{chan}DTFACTOR'.format(chan=(chan+1))
        dtf = np.array(self._attrs.get(dtfid))

        assert dtf is not None, 'No such attribute {attr}'.format(attr=dtfid)

        dtpid = 'CHAN{chan}DTPERCENT'.format(chan=(chan+1))
        dtp = np.array(self._attrs.get(dtpid))

        assert dtf is not None, 'No such attribute {attr}'.format(attr=dtpid)

        return [dtf[frameno], dtp[frameno]]

