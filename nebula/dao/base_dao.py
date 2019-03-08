# -*- coding: utf-8 -*-
from __future__ import absolute_import

from ..models.engine import DB_Session, Default_DB_Session, Data_DB_Session

Global_Session = None
Global_Default_Session = None
Global_Data_Session = None


class BaseDao(object):

    def __init__(self, session=None):
        if session:
            self.session = session
            self.own_session = False
        elif Global_Session:
            self.session = Global_Session
            self.own_session = False
        else:
            # create its own session
            self.session = DB_Session()
            self.own_session = True

    def __del__(self):
        if self.own_session:
            self.session.close()


class BaseDefaultDao(object):

    def __init__(self, session=None):
        if session:
            self.session = session
            self.own_session = False
        elif Global_Default_Session:
            self.session = Global_Default_Session
            self.own_session = False
        else:
            # create its own session
            self.session = Default_DB_Session()
            self.own_session = True

    def __del__(self):
        if self.own_session:
            self.session.close()


class BaseDataDao(object):

    def __init__(self, session=None):
        if session:
            self.session = session
            self.own_session = False
        elif Global_Data_Session:
            self.session = Global_Data_Session
            self.own_session = False
        else:
            # create its own session
            self.session = Data_DB_Session()
            self.own_session = True

    def __del__(self):
        if self.own_session:
            self.session.close()