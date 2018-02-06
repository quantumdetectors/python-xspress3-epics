# -*- coding: utf-8 -*-

import logging
from epics import PV

class MonitorPV:
    _value = None
    _pv = None
    _pv_string = None
    _is_string = False

    def __init__(self, pv, is_string=False, logger=None):
        self.logger = logger or logging.getLogger(__name__)

        self._is_string = is_string
        self._pv_string = pv
        self._pv = PV(pv, self._update_callback, auto_monitor=True)


    def _update_callback(self, **kwargs):
        self.logger.debug('PV Changed {pv}: {val}'.format(pv=kwargs['pvname'], val=kwargs['value']))
        self._value = kwargs['value'] if not self._is_string else kwargs['char_value']


    def value(self):
        return self._value
