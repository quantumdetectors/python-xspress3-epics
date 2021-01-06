# -*- coding: utf-8 -*-
import time
import logging

from .monitorpv import MonitorPV
from epics import caget, caput, PV

from . import hdf5
HDF5 = hdf5.HDF5


class Xspress3:
    """Xspress 3 Device

    A class encapsulating an Xspress 3 Device

    Example:
      >>> x3 = Xspres3(pv_prefix)  # create an x3 object with pv_prefix
      >>> x3.set(
      >>>     exposure_time=1,
      >>>     num_images=10
      >>> )
      >>> x3.acquire()
    """

    _sca_count = 7
    _mcas = []
    _scalars = []
    _params = {}

    _num_acquired = None
    _acquired_iter = 0

    _frame_callbacks = []

    _parameters = {
        'exposure_time': ['AcquireTime', 'AcquireTime_RBV', False, {}],
        'num_images': ['NumImages', 'NumImages_RBV', False, {}],
        'trigger_mode': ['TriggerMode', 'TriggerMode_RBV', False, { 0: 'Software', 1: 'Internal', 3: 'External' }],
        'file_path': ['HDF5:FilePath', 'HDF5:FilePath_RBV', True, {}],
        'file_name': ['HDF5:FileName', 'HDF5:FileName_RBV', True, {}],
        'file_capture': ['HDF5:Capture', 'HDF5:Capture_RBV', False, {}],
        'file_number': ['HDF5:FileNumber', 'HDF5:FileNumber', False, {}],
    }

    _sf_parameters = {
        'subframe_rate': ['SUBFRAME_RATE', 'SUBFRAME_RATE', False, {}],
        'subframe_cycles': ['SUBFRAME_CYCLES', 'SUBFRAME_CYCLES', False, {}],
        'subframe_resolution': ['SUBFRAME_RESOLUTION', 'SUBFRAME_RESOLUTION', False, {}],
        'num_subframes': [None, 'NUM_SUBFRAMES_RBV', False, {}],
    }


    def __init__(self, prefix, logger=None, subframes=False):
        """ Create an Xspress 3 device instance

        Args:
            prefix (string): the PV prefix of the device, eg. XSPRESS3-EXAMPLE

        Kwargs:
            subframes (bool): enable subframe parmeters (special IOC required)

        """
        self.logger = logger or logging.getLogger(__name__)

        self._prefix = prefix
        self._channels = caget(self._pv('NUM_CHANNELS_RBV'))

        assert self._channels is not None, 'Could not get number of channels. Is the Xspress 3 IOC running?'

        self.logger.info('System has {chans} channels'.format(chans=self._channels))


        # Disable built in DTC
        caput(self._pv('CTRL_DTC'), False)


        # MCAs + SCAs
        for c in range(self._channels):
            cid = c+1
            caput(self._pv('C{c}_PluginControlVal').format(c=cid), 1)
            self._mcas.append(MonitorPV(self._pv('ARR{c}:ArrayData'.format(c=cid))))

            scalars = []
            for s in range(self._sca_count):
                scalars.append(MonitorPV(self._pv('C{c}_SCA{s}:Value_RBV'.format(c=cid, s=s))))

            self._scalars.append(scalars)


        if subframes == True:
            self._parameters = dict(self._parameters, **self._sf_parameters)

        # Acq Params
        for k,p in self._parameters.items():
            if p[1] is not None:
                self._params[k] = MonitorPV(self._pv(p[1]), p[2])


        self._nfr_acq = PV(self._pv('ArrayCounter_RBV'), self._frame_change)
        self._acq_status = MonitorPV(self._pv('Acquire_RBV'))
        self._file_name = MonitorPV(self._pv('HDF5:FullFileName_RBV'), is_string=True)

        # Short delay to wait for PV readbacks
        time.sleep(0.2)


    def channels(self):
        """ Get the number of channels on the Xspress 3 system

        Returns:
            no_channels (int): The number of channels on the system
        """
        return self._channels


    def add_frame_callback(self, callback):
        """ Add a frame change callback

        Adds a callback to the list of callbacks called when a frame change occurs
        during an acquisition. The callback recieves the frame number as an argument

        >>> def callback(frame_number):
        >>>     print 'New frame {f}'.format(frame_number)
        >>> x3.add_frame_callback(callback)

        Args:
            callback (callable): the callback to add to the list of frame callbacks

        """
        assert not callback in self._frame_callbacks, 'Callback already registered'
        self._frame_callbacks.append(callback)


    def _pv(self, pv):
        return '{prefix}:{pv}'.format(prefix=self._prefix, pv=pv)



    def _frame_change(self, **kwargs):
        self._num_acquired = kwargs['value']
        self.logger.debug('Frame Changed: {frame}'.format(frame=kwargs['value']))
        for c in range(self._channels):
            self.logger.debug('  Ch {ch} Time {t} Events {e} Reset {r}'.format(ch=c, t=self.sca(c, 0), e=self.sca(c,3), r=self.sca(c,2)))
            self.logger.debug('    MCA Counts {cts}'.format(cts=sum(self._mcas[c].value())))

        if self.acquiring():
            for c in self._frame_callbacks:
                c(self._num_acquired)

        self._acquired_iter += 1


    def dropped_frames(self):
        """ Return the number of dropped frames in the last acquisition

        At high frames rates EPICS cannot keep up with PVs changing quickly,
        in these situations use file saving and read the hdf5 with the hdf5 
        module. Tests shows this occurs above around 100Hz

        This value will tell you how many frames were dropped
    
        Returns:
            dropped_frames (int): the number of dropped frames in the last acquisition

        """
        return self._num_acquired - self._acquired_iter


    def set(self, **kwargs):
        """ Set an attribute on the device

        Kwargs:
            exposure_time (float): per image exposure time in seconds

            num_images (int): number of images to acquire

            trigger_mode (string): trigger mode (Internal, External)

            file_path (string): path to save hdf5 files to

            file_name (string): file template for hdf5

            file_number (int): file number ({file_path}/{file_name}{file_number}.hdf5)

            file_capture (bool): enable hdf5 saving

        """

        for p,v in kwargs.items():
            assert p in self._parameters, 'No such parameter {param}'.format(param=p)
            assert self._parameters[p][0] is not None, 'Parameter {param} is read only'.format(param=p)

            if len(self._parameters[p][3]):
                val = None
                for k,va in self._parameters[p][3].items():
                    if v == va:
                        val = k

                assert val is not None, 'Invalid value {val} for parameter {param}. Available values are: {vals}'.format(
                    val=v, param=p, vals=','.join(self._parameters[p][3].values()))
                caput(self._pv(self._parameters[p][0]), val)

            else:
                caput(self._pv(self._parameters[p][0]), v)

        time.sleep(0.2)


    def get(self, param=None):
        """ Get the value of an attribute

        Args:
            param (string): parameter to return the value of

        Returns:
            value (mixed): the value of the parameter

        """

        if param is None:
            vals = {}
            for p,pv in self._params.items():
                if len(self._parameters[p][3]):
                    val = pv.value()
                    vals[p] = self._parameters[p][3][val]
                else:
                    vals[p] = pv.value()
            return vals

        else:
            assert param in self._parameters, 'No such parameter {param}'.format(param=param)
            assert self._parameters[param][1] is not None, 'Parameter {param} is write only'.format(param=param)

            return self._params[param].value()


    def setup_file_saving(self, dirn, template):
        """ Setup hdf5 file saving

        >>> x3.setup_file_saving('/home/test/data', 'test')
        >>> '/home/test/data/test{number}.hdf5'

        Args:
            dirn (string): directory to save hdf5 files to

            template (string): file template of hdf5 files

        Returns:
            filename (string): the filename of the last hdf5 captured

        """
        self.set(
            file_path=dirn,
            file_name=template,
        )

        self.file_saving(True)

        return self.filename()


    def file_saving(self, enable):
        """ Enable file saving

        File saving is disabled after each acquisition, renable or disable it

        Args:
            enable (bool): enable or disable file saving

        """
        self.set(file_capture=1 if enable else 0)

        return self.filename()


    def filename(self):
        """ Returns the current/last hdf5 filename

        Returns:
            filename (string): the current hdf5 filename

        """
        return self._file_name.value()


    def acquire(self):
        """ Starts an acquisition """

        self._acquired_iter = 0
        self._num_acquired = 0

        caput(self._pv('Acquire'), 0)
        caput(self._pv('ERASE'), 1)
        time.sleep(0.2)
        caput(self._pv('Acquire'), 1)

        while self._acq_status.value() != 1:
            self.logger.info('Preparing Acquisition')
            time.sleep(0.5)

        self.logger.info('Acquiring')

    def stop(self):
        """ Stops an acquisiton """

        self.logger.info('Aborting Acquisition')
        caput(self._pv('Acquire'), 0)

    def acquiring(self):
        """ Returns the acquisition status

        Returns:
            acquiring (bool): the acquisition status of the device

        """
        return self._acq_status.value()

    def num_acquired(self):
        """ Returns the number of frames acquired

        Returns:
            num_acquired (int): the number of frames acquired

        """
        return self._num_acquired


    def mca(self, chan):
        """ Returns the MCA for the specified channel

        This value will be automatically updated whenever the PV changes

        Args:
            chan (int): channel number to return MCA for, zero offset

        Returns:
            mca (list[int]): return a list of mca values (usually 4096 values)

        """
        assert chan < len(self._mcas), 'Chan {chan} > number of channels {chans}'.format(chan=chan, channels=self._channels)

        return self._mcas[chan].value()

    def sca(self, chan, sca):
        """ Returns the specified scalar for the specified channel

        Args:
            chan (int): channel number to return scalar for, zero offset

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
        assert chan < len(self._scalars), 'Chan {chan} > number of channels {chans}'.format(chan=chan, channels=self._channels)
        assert sca < len(self._scalars[chan]), 'Scalar {sca} > number of scalars {scalars}'.format(chan=sca, channels=self._channels)

        return self._scalars[chan][sca].value()
