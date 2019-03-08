#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some functionality for unittest
"""

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


class DBEnvironment(object):
    """
    测试数据库相关
    """

    def __init__(self):
        self.connect_string = None
        self.data_connect_string = None
        self.default_connect_string = None

        self.engine = None
        self.data_engine = None
        self.default_engine = None

        self.connection = None
        self.data_connection = None
        self.default_connection = None

        self.transaction = None
        self.data_transaction = None
        self.default_transaction = None

    def update_connect_string(self, connect_string, data_connect_string, default_connect_string):
        self.connect_string = connect_string
        self.data_connect_string = data_connect_string
        self.default_connect_string = default_connect_string

    def init(self):
        self.engine = create_engine(self.connect_string)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        import nebula.models
        nebula.models.BaseModel.metadata.create_all(self.connection)

        self.data_engine = create_engine(self.data_connect_string)
        self.data_connection = self.data_engine.connect()
        self.data_transaction = self.data_connection.begin()
        import nebula.models.data
        nebula.models.data.BaseModel.metadata.create_all(self.data_connection)

        self.default_engine = create_engine(self.default_connect_string)
        self.default_connection = self.default_engine.connect()
        self.default_transaction = self.default_connection.begin()
        import nebula.models.default
        nebula.models.default.BaseModel.metadata.create_all(self.default_connection)

    def clear(self):
        import nebula.models
        nebula.models.BaseModel.metadata.drop_all(self.connection)
        import nebula.models.data
        nebula.models.data.BaseModel.metadata.drop_all(self.data_connection)
        import nebula.models.default
        nebula.models.default.BaseModel.metadata.drop_all(self.default_connection)

        if self.transaction:
            self.transaction.rollback()
            self.transaction = None
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

        if self.data_transaction:
            self.data_transaction.rollback()
            self.data_transaction = None
        if self.data_connection:
            self.data_connection.close()
            self.data_connection = None
        if self.data_engine:
            self.data_engine.dispose()
            self.data_engine = None

        if self.default_transaction:
            self.default_transaction.rollback()
            self.default_transaction = None
        if self.default_connection:
            self.default_connection.close()
            self.default_connection = None
        if self.default_engine:
            self.default_engine.dispose()
            self.default_engine = None


db_env = DBEnvironment()


class TestClassDBUtil(object):
    """
    每个单元测试可以是用该类来建立session
    """

    def __init__(self):
        self.transaction = self.data_transaction = self.default_transaction = None
        self.session = self.data_session = self.default_session = None

    def setup(self):
        self.transaction = db_env.connection.begin_nested()
        self.data_transaction = db_env.data_connection.begin_nested()
        self.default_transaction = db_env.default_connection.begin_nested()

        self.session = Session(db_env.connection)
        self.data_session = Session(db_env.data_connection)
        self.default_session = Session(db_env.default_connection)

    def teardown(self):
        self.session.close()
        self.data_session.close()
        self.default_session.close()

        self.transaction.rollback()
        self.data_transaction.rollback()
        self.default_transaction.rollback()

    def get_session(self):
        return self.session

    def get_data_session(self):
        return self.data_session

    def get_default_session(self):
        return self.default_session

