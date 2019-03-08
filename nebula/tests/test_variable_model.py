#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from nebula.dao.variable_model_dao import VariableModelDefaultDao, VariableModelCustDao
from nebula.dao.event_model_dao import EventModelCustDao
from nebula_meta.variable_model import VariableModel, add_variable_to_registry
from nebula_meta.event_model import EventModel, add_event_to_registry

from base import WebTestCase
from .unittest_util import TestClassDBUtil, db_env


with open('nebula/tests/data/event_model.json') as json_file:
    SAMPLE_EVENTS = json.load(json_file)
    new_events = list()
    for _ in SAMPLE_EVENTS:
        new_event = EventModel.from_dict(_)
        add_event_to_registry(new_event)
        new_events.append(new_event)

    SAMPLE_EVENTS = new_events
    SAMPLE_EVENT = SAMPLE_EVENTS[0]


with open('nebula/tests/data/variable_model.json') as json_file:
    SAMPLE_VARIABLES = json.load(json_file)
    new_variables = list()
    for _ in SAMPLE_VARIABLES:
        new_variable = VariableModel.from_dict(_)
        add_variable_to_registry(new_variable)
        new_variables.append(new_variable)
    SAMPLE_VARIABLES = new_variables
    SAMPLE_VARIABLE = SAMPLE_VARIABLES[-1]  # did变量


def prepare_events(event_dao):
    for _ in SAMPLE_EVENTS:
        event_dao.add_model(_)


def prepare_variables(variable_dao):
    variable_dao.add_model(SAMPLE_VARIABLES[0])
    variable_dao.add_model(SAMPLE_VARIABLES[1])

    # add with new app
    new_variable = SAMPLE_VARIABLE.copy()
    new_variable.app = 'new_app'
    new_variable.name = 'var1'
    variable_dao.add_model(new_variable)

    # add with new type
    new_variable = SAMPLE_VARIABLE.copy()
    new_variable.type = 'new_type'
    new_variable.name = 'var2'
    variable_dao.add_model(new_variable)


def clear_variables(variable_dao):
    variable_dao.clear()


class TestDefaultVariableModelListHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import variable_model_default, variable_model
        return [(r"/default/variable_models", variable_model_default.VariableModelListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultVariableModelListHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestDefaultVariableModelListHandler, cls).tearDownClass()

    def setUp(self):
        super(TestDefaultVariableModelListHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.variable_dao = VariableModelDefaultDao()
        self.event_dao = EventModelCustDao()
        prepare_events(self.event_dao)

    def tearDown(self):
        self.db_util.teardown()
        super(TestDefaultVariableModelListHandler, self).tearDown()

    def test_get_variables(self):
        prepare_variables(self.variable_dao)

        url = "/default/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(self.variable_dao.count(), 4)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 4)
        return_variables = res['values']
        return_variable = [_ for _ in return_variables if _['name'] == SAMPLE_VARIABLE.name][0]
        self.assertEqual(VariableModel.from_dict(return_variable), SAMPLE_VARIABLE)

        # check get by app
        response = self.fetch(url + '?app=new_app')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

        # check get by type
        response = self.fetch(url + '?type=new_type')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

    def test_delete_variables(self):
        prepare_variables(self.variable_dao)

        url = "/default/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)

        # 1 delete by type
        # 1.1 get
        url = "/default/variable_models?type=new_type"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        # 1.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 1.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

        # 2 delete by app
        # 2.1 get
        url = "/default/variable_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        # 2.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 2.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

        clear_variables(self.variable_dao)
        prepare_variables(self.variable_dao)

        # 3. delete all
        # 3.1 get
        url = "/default/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)
        # 3.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 3.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

    def test_modify_variables(self):
        prepare_variables(self.variable_dao)

        # use test variable in 'new_app' to check
        new_app_variable = SAMPLE_VARIABLE.copy()
        new_app_variable.app = 'new_app'
        new_app_variable.name = 'var1'

        # first check
        url = "/default/variable_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(new_app_variable, get_variable)

        # 1. modify variable and test
        # 1.1 modify test variable, so it is doesn't equal now
        new_app_variable.remark = 'new_remark'
        self.assertNotEquals(new_app_variable, get_variable)

        # 1.2 post the modified variable
        url = "/default/variable_models"
        response = self.fetch(url, method='POST', body='[%s]' % new_app_variable.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 1.3 verify again
        url = "/default/variable_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        # now equal again
        self.assertEqual(new_app_variable, get_variable)

        # 2. add an variable with post
        # 2.1 now there are 4 variables
        url = "/default/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)

        # 2.2 add one
        added_variable = SAMPLE_VARIABLE.copy()
        added_variable.name = 'added_variable'
        response = self.fetch(url, method='POST', body='[%s]' % added_variable.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 now there are 5
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 5)

    def test_add_multiple_variables(self):
        prepare_events(self.event_dao)
        prepare_variables(self.variable_dao)

        # 两个级联的变量
        filter_dict_1 = {
            'module': 'base',
            'app': 'nebula',
            'name': 'filter1',
            'status': 'enable',
            'type': 'filter',
            'source': [
                {
                    'app': 'nebula',
                    'name': 'HTTP_DYNAMIC'
                }
            ]
        }
        filter_dict_2 = {
            'module': 'base',
            'app': 'nebula',
            'name': 'filter2',
            'status': 'enable',
            'type': 'filter',
            'source': [
                {
                    'app': 'nebula',
                    'name': 'filter1'
                }
            ]
        }

        json_content = json.dumps([filter_dict_1, filter_dict_2])
        url = "/default/variable_models"
        response = self.fetch(url, method='POST', body=json_content)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0, res['msg'])
        self.assertEqual(res['msg'], 'ok')


class TestDefaultVariableQueryHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import variable_model_default, variable_model
        return [(r"/default/variable_models/variable/(.*)/(.*)", variable_model_default.VariableModelQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultVariableQueryHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestDefaultVariableQueryHandler, cls).tearDownClass()

    def setUp(self):
        super(TestDefaultVariableQueryHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.variable_dao = VariableModelDefaultDao()
        self.event_dao = EventModelCustDao()
        prepare_events(self.event_dao)

    def tearDown(self):
        self.db_util.teardown()
        super(TestDefaultVariableQueryHandler, self).tearDown()

    def test_get_variable(self):
        prepare_variables(self.variable_dao)
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(VariableModel.from_dict(res['values'][0]), SAMPLE_VARIABLE)

        # get not exist
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, 'not_exist')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

    def test_delete_variable(self):
        prepare_variables(self.variable_dao)
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(VariableModel.from_dict(res['values'][0]), SAMPLE_VARIABLE)

        # delete
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

    def tests_modify_variable(self):
        prepare_variables(self.variable_dao)
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(get_variable, SAMPLE_VARIABLE)

        # 1. modify SAMPLE_VARIABLE
        # 1.1 first not equal
        new_sample = SAMPLE_VARIABLE.copy()
        new_sample.remark = 'modified'
        self.assertNotEquals(get_variable, new_sample)

        # 1.2 second modify
        response = self.fetch(url, method='POST', body=new_sample.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 1.3 third  check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(get_variable, new_sample)

        # 2. add a new one
        # 2.1 get 404
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, 'variable_to_be_add')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # 2.2 add one
        variable_to_be_add = SAMPLE_VARIABLE.copy()
        variable_to_be_add.name = 'variable_to_be_add'
        response = self.fetch(url, method='POST', body=variable_to_be_add.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(get_variable, variable_to_be_add)


class TestVariableModelListHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import variable_model_default, variable_model
        return [(r"/platform/variable_models", variable_model.VariableModelListHandler),
                (r"/default/variable_models", variable_model_default.VariableModelListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestVariableModelListHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestVariableModelListHandler, cls).tearDownClass()

    def setUp(self):
        super(TestVariableModelListHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.default_dao = VariableModelDefaultDao()
        self.cust_dao = VariableModelCustDao()
        self.event_dao = EventModelCustDao()
        prepare_events(self.event_dao)

    def tearDown(self):
        self.db_util.teardown()
        super(TestVariableModelListHandler, self).tearDown()

    def test_get_variables(self):
        prepare_variables(self.cust_dao)

        # default 0, cust 3
        url = "/default/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(self.default_dao.count(), 0)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 0)

        url = '/platform/variable_models'
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(self.cust_dao.count(), 4)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 4)
        return_variables = res['values']
        return_variable = [_ for _ in return_variables if _['name'] == SAMPLE_VARIABLE.name][0]
        self.assertEqual(VariableModel.from_dict(return_variable), SAMPLE_VARIABLE)

        # check get by app
        response = self.fetch(url + '?app=new_app')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

        # check get by type
        response = self.fetch(url + '?type=new_type')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

    def test_delete_variables(self):
        prepare_variables(self.cust_dao)

        url = "/platform/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)

        # 1 delete by type
        # 1.1 get
        url = "/platform/variable_models?type=new_type"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        # 1.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 1.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

        # 2 delete by app
        # 2.1 get
        url = "/platform/variable_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        # 2.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 2.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

        clear_variables(self.cust_dao)
        prepare_variables(self.cust_dao)

        # 3. delete all
        # 3.1 get
        url = "/platform/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)
        # 3.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 3.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

        # 4. check only affect cust dao
        # 4.1 add variable in both table
        clear_variables(self.default_dao)
        clear_variables(self.cust_dao)
        prepare_variables(self.default_dao)
        prepare_variables(self.cust_dao)

        # 4.2 each has 3
        self.assertEqual(self.default_dao.count(), 4)
        self.assertEqual(self.cust_dao.count(), 4)

        # 4.3 delete all
        url = '/platform/variable_models'
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 4.4 now cust is empty
        self.assertEqual(self.default_dao.count(), 4)
        self.assertEqual(self.cust_dao.count(), 0)

    def test_modify_variables(self):
        prepare_variables(self.cust_dao)

        # use test variable in 'new_app' to check
        new_app_variable = SAMPLE_VARIABLE.copy()
        new_app_variable.app = 'new_app'
        new_app_variable.name = 'var1'

        # first check
        url = "/platform/variable_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(new_app_variable, get_variable)

        # 1. modify variable and test
        # 1.1 modify test variable, so it is doesn't equal now
        new_app_variable.remark = 'new_remark'
        self.assertNotEquals(new_app_variable, get_variable)

        # 1.2 post the modified variable
        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body='[%s]' % new_app_variable.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 1.3 verify again
        url = "/platform/variable_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        # now equal again
        self.assertEqual(new_app_variable, get_variable)

        # 2. add an variable with post
        # 2.1 now there are 4 variables
        url = "/platform/variable_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)

        # 2.2 add one
        added_variable = SAMPLE_VARIABLE.copy()
        added_variable.name = 'added_variable'
        response = self.fetch(url, method='POST', body='[%s]' % added_variable.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 now there are 5
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 5)

        # 3. modify only affect cust table
        clear_variables(self.default_dao)
        clear_variables(self.cust_dao)
        prepare_variables(self.default_dao)

        modified_variable = SAMPLE_VARIABLE.copy()
        modified_variable.remark = 'modified'
        response = self.fetch(url, method='POST', body='[%s]' % modified_variable.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 4. default keeps the same, cust is updated
        self.assertEqual(self.cust_dao.get_model_by_app_name(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name), modified_variable)
        self.assertNotEqual(self.default_dao.get_model_by_app_name(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name), modified_variable)

    def test_add_multiple_variables(self):
        prepare_variables(self.cust_dao)

        # 两个级联的变量
        filter_dict_1 = {
            'module': 'base',
            'app': 'nebula',
            'name': 'filter1',
            'status': 'enable',
            'type': 'filter',
            'source': [
                {
                    'app': 'nebula',
                    'name': 'HTTP_DYNAMIC'
                }
            ]
        }
        filter_dict_2 = {
            'module': 'base',
            'app': 'nebula',
            'name': 'filter2',
            'status': 'enable',
            'type': 'filter',
            'source': [
                {
                    'app': 'nebula',
                    'name': 'filter1'
                }
            ]
        }

        json_content = json.dumps([filter_dict_1, filter_dict_2])
        url = "/platform/variable_models"
        response = self.fetch(url, method='POST', body=json_content)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0, res['msg'])
        self.assertEqual(res['msg'], 'ok')


class TestVariableQueryHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import variable_model_default, variable_model
        return [(r"/default/variable_models/variable/(.*)/(.*)", variable_model_default.VariableModelQueryHandler),
                (r"/platform/variable_models/variable/(.*)/(.*)", variable_model.VariableModelQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestVariableQueryHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestVariableQueryHandler, cls).tearDownClass()

    def setUp(self):
        super(TestVariableQueryHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.default_dao = VariableModelDefaultDao()
        self.cust_dao = VariableModelCustDao()
        self.event_dao = EventModelCustDao()
        prepare_events(self.event_dao)

    def tearDown(self):
        self.db_util.teardown()
        super(TestVariableQueryHandler, self).tearDown()

    def test_get_variable(self):
        prepare_variables(self.cust_dao)
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(VariableModel.from_dict(res['values'][0]), SAMPLE_VARIABLE)

        # not in default
        url = "/default/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # get not exist
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, 'not_exist')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

    def test_delete_variable(self):
        prepare_variables(self.cust_dao)
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(VariableModel.from_dict(res['values'][0]), SAMPLE_VARIABLE)

        # delete
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # can not delete default
        clear_variables(self.cust_dao)
        prepare_variables(self.default_dao)
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)

    def tests_modify_variable(self):
        prepare_variables(self.cust_dao)
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, SAMPLE_VARIABLE.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(get_variable, SAMPLE_VARIABLE)

        # 1. modify SAMPLE_VARIABLE
        # 1.1 first not equal
        new_sample = SAMPLE_VARIABLE.copy()
        new_sample.remark = 'modified'
        self.assertNotEquals(get_variable, new_sample)

        # 1.2 second modify
        response = self.fetch(url, method='POST', body=new_sample.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 1.3 third  check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(get_variable, new_sample)

        # 2. add a new one
        # 2.1 get 404
        url = "/platform/variable_models/variable/{}/{}".format(SAMPLE_VARIABLE.app, 'variable_to_be_add')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # 2.2 add one
        variable_to_be_add = SAMPLE_VARIABLE.copy()
        variable_to_be_add.name = 'variable_to_be_add'
        response = self.fetch(url, method='POST', body=variable_to_be_add.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_variable = VariableModel.from_dict(res['values'][0])
        self.assertEqual(get_variable, variable_to_be_add)
