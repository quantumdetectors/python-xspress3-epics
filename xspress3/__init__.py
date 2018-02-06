# -*- coding: utf-8 -*-
import time
import logging

from monitorpv import MonitorPV
from epics import caget, caput, PV

from . import hdf5
HDF5 = hdf5.HDF5


class Xspress3:
    """Xspress 3 Device

    A class encapsulating an Xspress 3 Device
      >>> x3 = Xspres3(pv_prefix)  # create an x3 object with pv_prefix
      >>> x3.set(
      >>>     exposure_time=1,
      >>>     num_images=10
      >>> })
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
        'subframe_rate': ['SUBFRAME_RATE', 'SUBFRAME_RATE', False],
        'subframe_cycles': ['SUBFRAME_CYCLES', 'SUBFRAME_CYCLES', False],
        'subframe_resolution': ['SUBFRAME_RESOLUTION', 'SUBFRAME_RESOLUTION', False],
        'num_subframes': ['NUM_SUBFRAMES_RBV', 'NUM_SUBFRAMES_RBV', False],
    }


    def __init__(self, prefix, logger=None, subframes=False):
        self.logger = logger or logging.getLogger(__name__)

        self._prefix = prefix
        self._channels = caget(self._pv('NUM_CHANNELS_RBV'))

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


        # Acq Params
        for k,p in self._parameters.iteritems():
            self._params[k] = MonitorPV(self._pv(p[1]), p[2])

        if subframes == True:
            for k,p in self._sf_parameters.iteritems():
                self._params[k] = MonitorPV(self._pv(p[1]), p[2])


        self._nfr_acq = PV(self._pv('ArrayCounter_RBV'), self._frame_change)
        self._acq_status = MonitorPV(self._pv('Acquire_RBV'))
        self._file_name = MonitorPV(self._pv('HDF5:FullFileName_RBV'), is_string=True)

        # Short delay to wait for PV readbacks
        time.sleep(0.2)

    def channels(self):
        return self._channels


    def add_frame_callback(self, callback):
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
        return self._num_acquired - self._acquired_iter


    def set(self, **kwargs):
        """set an attribute on the device

        Arguments
        =========
        exposure_time    (float) per image exposure time in seconds
        num_images       (int) number of images to acquire
        trigger_mode     (string) trigger mode (Internal, External)

        file_path        (string) path to save hdf5 files to
        file_name        (string) file template for hdf5
        file_number      (int) file number ({file_path}/{file_name}{file_number}.hdf5)
        file_capture     (boolean / int) enable hdf5 saving
        """

        for p,v in kwargs.iteritems():
            assert p in self._parameters, 'No such parameter {param}'.format(param=p)

            if len(self._parameters[p][3]):
                val = None
                for k,va in self._parameters[p][3].iteritems():
                    if v == va:
                        val = k

                assert val is not None, 'Invalid value {val} for parameter {param}. Available values are: {vals}'.format(
                    val=v, param=p, vals=','.join(self._parameters[p][3].values()))
                caput(self._pv(self._parameters[p][0]), val)
            else:
                caput(self._pv(self._parameters[p][0]), v)

        time.sleep(0.2)


    def get(self, param=None):
        """get the value of an attribute

        Arguments
        =========
        param    (string) parameter to get
        """

        if param is None:
            vals = {}
            for p,pv in self._params.iteritems():
                if len(self._parameters[p][3]):
                    val = pv.value()
                    vals[p] = self._parameters[p][3][val]
                else:
                    vals[p] = pv.value()
            return vals

        else:
            assert param in self._parameters, 'No such parameter {param}'.format(param=param)
            return self._params[param].value()


    def setup_file_saving(self, dirn, template):
        self.set(
            file_path=dirn,
            file_name=template,
        )

        self.file_saving(True)

        return self.filename()

    def file_saving(self, enable):
        self.set(file_capture=1 if enable else 0)

        return self.filename()


    def filename(self):
        return self._file_name.value()


    def acquire(self):
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
        self.logger.info('Aborting Acquisition')
        caput(self._pv('Acquire'), 0)

    def acquiring(self):
        return self._acq_status.value()

    def num_acquired(self):
        return self._num_acquired


    def mca(self, chan):
        assert chan < len(self._mcas), 'Chan {chan} > number of channels {chans}'.format(chan=chan, channels=self._channels)

        return self._mcas[chan].value()

    def sca(self, chan, sca):
        assert chan < len(self._scalars), 'Chan {chan} > number of channels {chans}'.format(chan=chan, channels=self._channels)
        assert sca < len(self._scalars[chan]), 'Scalar {sca} > number of scalars {scalars}'.format(chan=sca, channels=self._channels)

        return self._scalars[chan][sca].value()
