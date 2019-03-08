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


def get_standard_realtime_variables():
    with open('nebula/tests/data/standard_realtime_variable.json') as json_file:
        return json_file.read()


def get_standard_profile_variables():
    with open('nebula/tests/data/standard_profile_variable.json') as json_file:
        return json_file.read()


def get_strategies():
    with open('nebula/tests/data/all_strategy.json') as json_file:
        return json_file.read()


class TestNebulaConfig(WebTestCase):

    def get_handlers(self):
        from nebula.views import nebula_config, variable_model, event_model
        from nebula.views import strategy
        from nebula.models import GroupModel
        strategy.StrategyListHandler.group = GroupModel(id=2)
        return [(r"/nebula/config", nebula_config.NebulaUIEventsHandler),
                (r"/nebula/online/events", nebula_config.NebulaOnlineEventsHandler),
                (r"/nebula/online/variables", nebula_config.NebulaOnlineVariablesHandler),
                (r"/platform/variable_models", variable_model.VariableModelListHandler),
                (r"/platform/event_models", event_model.EventListHandler),
                (r"/nebula/glossary", nebula_config.VariableGlossaryHandler),
                (r"/nebula/events", nebula_config.NebulaUIEventsHandler),
                (r"/nebula/variables", nebula_config.NebulaUIVariablesHandler),
                (r"/nebula/strategies", strategy.StrategyListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestNebulaConfig, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestNebulaConfig, cls).tearDownClass()

    def setUp(self):
        super(TestNebulaConfig, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()

    def tearDown(self):
        self.db_util.teardown()
        super(TestNebulaConfig, self).tearDown()

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

        url = "/nebula/config"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print json.dumps(res['values'])

    def test_get_events(self):
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

        url = "/nebula/online/events"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print json.dumps(res['values'])

    def test_get_variables(self):
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

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_profile_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/nebula/strategies"
        response = self.fetch(url, method='POST', body=get_strategies())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')

        url = "/nebula/online/variables"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print json.dumps(res['values'])

    def test_get_glossary(self):
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

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_profile_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/nebula/glossary"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print json.dumps(res['values'])

    def test_get_ui_events(self):
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

        url = "/nebula/events"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print json.dumps(res['values'])

    def test_get_ui_variables(self):
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

        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=get_standard_profile_variables())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        url = "/nebula/variables"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        print json.dumps(res['values'])
