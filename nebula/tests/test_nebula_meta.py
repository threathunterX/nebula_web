#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from base import WebTestCase
from nebula.tests.unittest_util import TestClassDBUtil, db_env


def get_standard_event():
    with open('nebula/tests/data/standard_event.json') as json_file:
        return json_file.read()


def get_standard_common_variables():
    with open('nebula/tests/data/standard_common_variable.json') as json_file:
        return json_file.read()


def get_standard_profile_variables():
    with open('nebula/tests/data/standard_profile_variable.json') as json_file:
        return json_file.read()


def get_standard_slot_variables():
    with open('nebula/tests/data/standard_slot_variable.json') as json_file:
        return json_file.read()


def get_standard_realtime_variables():
    with open('nebula/tests/data/standard_realtime_variable.json') as json_file:
        return json_file.read()


class TestNebulaMeta(WebTestCase):

    def get_handlers(self):
        from nebula.views import variable_model, event_model
        return [(r"/platform/variable_models", variable_model.VariableModelListHandler),
                (r"/platform/event_models", event_model.EventListHandler),
                (r"/platform/variable_models/variable/(.*)/(.*)", variable_model.VariableModelQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestNebulaMeta, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestNebulaMeta, cls).tearDownClass()

    def setUp(self):
        super(TestNebulaMeta, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()

    def tearDown(self):
        self.db_util.teardown()
        super(TestNebulaMeta, self).tearDown()

    def test_add_events(self):
        url = "/platform/event_models"
        response = self.fetch(url, method='POST', body=get_standard_event())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/event_models?simple=true"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print response.body

    def test_add_events_variable(self):
        url = "/platform/event_models"
        response = self.fetch(url, method='POST', body=get_standard_event())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_common_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models?modules=base&simple=true"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print response.body

    def test_add_profile_variable(self):
        url = "/platform/event_models"
        response = self.fetch(url, method='POST', body=get_standard_event())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_common_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_profile_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models?modules=profile&simple=true"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        result = res['values']
        print response.body

    def test_add_slot_variable(self):
        url = "/platform/event_models"
        response = self.fetch(url, method='POST', body=get_standard_event())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_common_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_slot_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models?modules=slot&simple=false"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        result = res['values']
        print response.body

    def test_add_realtime_variable(self):
        url = "/platform/event_models"
        response = self.fetch(url, method='POST', body=get_standard_event())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_common_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_realtime_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/platform/variable_models?modules=realtime&simple=true"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        result = res['values']
        print response.body
