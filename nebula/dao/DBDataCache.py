#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import traceback

from threathunter_common.util import millis_now

from .strategy_dao import StrategyCustDao
from .variable_model_dao import VariableModelCustDao
from .event_model_dao import EventModelCustDao


class DBDataContext(object):

    def __init__(self, interval=5000):
        self._interval = interval
        # variables defined for nebula app
        self._nebula_variables = []
        self._nebula_variables_dict = dict()
        # events defined for nebula app
        self._nebula_events = []
        self._nebula_events_dict = dict()
        # strategies defined for nebula app
        self._nebula_strategies = []
        # events used in nebula ui, it is from platform variable
        self._nebula_ui_events = []
        self._nebula_ui_events_dict = []
        # variables used in nebula ui, it is from platform variable
        self._nebula_ui_variables = []
        self._nebula_ui_variables_dict = []
        # whether error in background
        self._error = None

        self._last_modified = 0

    def check(self, force=False):
        current = millis_now()
        if (not force) and self._last_modified > 0:
            if (current - self._last_modified) < self._interval:
                # don't get data too frequently
                if self._error:
                    raise RuntimeError("the server is invalid: {}".format(self._error))
                else:
                    return

        try:
            self._nebula_variables = VariableModelCustDao().list_all_models()
            self._nebula_events = EventModelCustDao().list_all_models()
            self._nebula_strategies = StrategyCustDao().list_all_strategies_by_app("nebula")

            # get nebula ui events and variables
            eventvariables = filter(lambda v: v.type == "event", self._nebula_variables)
            events = eventvariables[:]

            self._nebula_ui_events = filter(lambda event: not event.name.startswith("_"), events)
            self._nebula_ui_variables = [_ for _ in self._nebula_variables if not _.name.startswith("_")]

            self._nebula_events_dict = {(e.app, e.name): e for e in self._nebula_events}
            self._nebula_variables_dict = {(v.app, v.name): v for v in self._nebula_variables}
            self._nebula_ui_events_dict = {(e.app, e.name): e for e in self._nebula_ui_events}
            self._nebula_ui_variables_dict = {(v.app, v.name): v for v in self._nebula_ui_variables}

            self._last_modified = millis_now()

        except Exception as err:
            traceback.print_exc()
            self._error = err.message
            raise RuntimeError("the server is invalid: {}".format(self._error))

    @property
    def nebula_ui_events(self):
        self.check()
        return self._nebula_ui_events

    @property
    def nebula_ui_events_dict(self):
        self.check()
        return self._nebula_ui_events_dict

    @property
    def nebula_ui_variables_dict(self):
        self.check()
        return self._nebula_ui_variables_dict

    @property
    def nebula_ui_variables(self):
        self.check()
        return self._nebula_ui_variables

    @property
    def nebula_variables(self):
        self.check()
        return self._nebula_variables

    @property
    def nebula_variables_dict(self):
        self.check()
        return self._nebula_variables_dict

    @property
    def nebula_events(self):
        self.check()
        return self._nebula_events

    @property
    def nebula_events_dict(self):
        self.check()
        return self._nebula_events_dict

    @property
    def nebula_strategies(self):
        self.check()
        return self._nebula_strategies

    def init(self):
        self.check()


dbcontext = DBDataContext(5000)
