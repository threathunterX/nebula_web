#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from nebula.dao.event_model_dao import EventModelDefaultDao
from nebula.dao.event_model_dao import EventModelCustDao
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


def prepare_events(event_dao):
    event_dao.add_model(SAMPLE_EVENT)

    # add with new app
    new_event = SAMPLE_EVENT.copy()
    new_event.app = 'new_app'
    new_event.name = 'event1'
    event_dao.add_model(new_event)

    # add with new type
    new_event = SAMPLE_EVENT.copy()
    new_event.type = 'new_type'
    new_event.name = 'event2'
    event_dao.add_model(new_event)


def clear_events(event_dao):
    event_dao.clear()


class TestDefaultEventModelListHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import event_model_default, event_model
        return [(r"/default/event_models", event_model_default.EventModelListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultEventModelListHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestDefaultEventModelListHandler, cls).tearDownClass()

    def setUp(self):
        super(TestDefaultEventModelListHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.event_dao = EventModelDefaultDao()

    def tearDown(self):
        self.db_util.teardown()
        super(TestDefaultEventModelListHandler, self).tearDown()

    def test_get_events(self):
        prepare_events(self.event_dao)

        url = "/default/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(self.event_dao.count(), 3)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 3)
        return_events = res['values']
        return_event = [_ for _ in return_events if _['name'] == SAMPLE_EVENT.name][0]
        self.assertEqual(EventModel.from_dict(return_event), SAMPLE_EVENT)

        # check get by app
        response = self.fetch(url + '?app=new_app')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

        # check get by type
        response = self.fetch(url + '?type=new_type')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

    def test_delete_events(self):
        prepare_events(self.event_dao)

        url = "/default/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 3)

        # 1 delete by type
        # 1.1 get
        url = "/default/event_models?type=new_type"
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
        url = "/default/event_models?app=new_app"
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

        clear_events(self.event_dao)
        prepare_events(self.event_dao)

        # 3. delete all
        # 3.1 get
        url = "/default/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 3)
        # 3.2 delete
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        # 3.3 verify
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 0)

    def test_modify_events(self):
        prepare_events(self.event_dao)

        # use test event in 'new_app' to check
        new_app_event = SAMPLE_EVENT.copy()
        new_app_event.app = 'new_app'
        new_app_event.name = 'event1'

        # first check
        url = "/default/event_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(new_app_event, get_event)

        # 1. modify event and test
        # 1.1 modify test event, so it is doesn't equal now
        new_app_event.remark = 'new_remark'
        self.assertNotEquals(new_app_event, get_event)

        # 1.2 post the modified event
        url = "/default/event_models"
        response = self.fetch(url, method='POST', body='[%s]' % new_app_event.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 1.3 verify again
        url = "/default/event_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        # now equal again
        self.assertEqual(new_app_event, get_event)

        # 2. add an event with post
        # 2.1 now there are 3 events
        url = "/default/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 3)

        # 2.2 add one
        added_event = SAMPLE_EVENT.copy()
        added_event.name = 'added_event'
        response = self.fetch(url, method='POST', body='[%s]' % added_event.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 now there are 4
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)

    def test_add_events(self):
        event1_dict = {
            'name': 'event1',
        }

        event2_dict = {
            'name': 'event2',
            'source': [
                {
                    'app': '',
                    'name': 'event1'
                }
            ]
        }

        url = "/default/event_models"
        request_content = json.dumps([event1_dict, event2_dict])
        response = self.fetch(url, method='POST', body=request_content)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')


class TestDefaultEventQueryHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import event_model_default, event_model
        return [(r"/default/event_models/event/(.*)/(.*)", event_model_default.EventQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultEventQueryHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestDefaultEventQueryHandler, cls).tearDownClass()

    def setUp(self):
        super(TestDefaultEventQueryHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.event_dao = EventModelDefaultDao()

    def tearDown(self):
        self.db_util.teardown()
        super(TestDefaultEventQueryHandler, self).tearDown()

    def test_get_event(self):
        prepare_events(self.event_dao)
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(EventModel.from_dict(res['values'][0]), SAMPLE_EVENT)

        # get not exist
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, 'not_exist')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

    def test_delete_event(self):
        prepare_events(self.event_dao)
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(EventModel.from_dict(res['values'][0]), SAMPLE_EVENT)

        # delete
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

    def tests_modify_event(self):
        prepare_events(self.event_dao)
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(get_event, SAMPLE_EVENT)

        # 1. modify SAMPLE_EVENT
        # 1.1 first not equal
        new_sample = SAMPLE_EVENT.copy()
        new_sample.remark = 'modified'
        self.assertNotEquals(get_event, new_sample)

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
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(get_event, new_sample)

        # 2. add a new one
        # 2.1 get 404
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, 'event_to_be_add')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # 2.2 add one
        event_to_be_add = SAMPLE_EVENT.copy()
        event_to_be_add.name = 'event_to_be_add'
        response = self.fetch(url, method='POST', body=event_to_be_add.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(get_event, event_to_be_add)


class TestEventModelListHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import event_model_default, event_model
        return [(r"/platform/event_models", event_model.EventListHandler),
                (r"/default/event_models", event_model_default.EventModelListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestEventModelListHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestEventModelListHandler, cls).tearDownClass()

    def setUp(self):
        super(TestEventModelListHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.default_dao = EventModelDefaultDao()
        self.cust_dao = EventModelCustDao()

    def tearDown(self):
        self.db_util.teardown()
        super(TestEventModelListHandler, self).tearDown()

    def test_get_events(self):
        prepare_events(self.cust_dao)

        # default 0, cust 3
        url = "/default/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(self.default_dao.count(), 0)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 0)

        url = '/platform/event_models'
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(self.cust_dao.count(), 3)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 3)
        return_events = res['values']
        return_event = [_ for _ in return_events if _['name'] == SAMPLE_EVENT.name][0]
        self.assertEqual(EventModel.from_dict(return_event), SAMPLE_EVENT)

        # check get by app
        response = self.fetch(url + '?app=new_app')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

        # check get by type
        response = self.fetch(url + '?type=new_type')
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)

    def test_delete_events(self):
        prepare_events(self.cust_dao)

        url = "/platform/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 3)

        # 1 delete by type
        # 1.1 get
        url = "/platform/event_models?type=new_type"
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
        url = "/platform/event_models?app=new_app"
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

        clear_events(self.cust_dao)
        prepare_events(self.cust_dao)

        # 3. delete all
        # 3.1 get
        url = "/platform/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 3)
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
        # 4.1 add event in both table
        clear_events(self.default_dao)
        clear_events(self.cust_dao)
        prepare_events(self.default_dao)
        prepare_events(self.cust_dao)

        # 4.2 each has 3
        self.assertEqual(self.default_dao.count(), 3)
        self.assertEqual(self.cust_dao.count(), 3)

        # 4.3 delete all
        url = '/platform/event_models'
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 4.4 now cust is empty
        self.assertEqual(self.default_dao.count(), 3)
        self.assertEqual(self.cust_dao.count(), 0)

    def test_modify_events(self):
        prepare_events(self.cust_dao)

        # use test event in 'new_app' to check
        new_app_event = SAMPLE_EVENT.copy()
        new_app_event.app = 'new_app'
        new_app_event.name = 'event1'

        # first check
        url = "/platform/event_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(new_app_event, get_event)

        # 1. modify event and test
        # 1.1 modify test event, so it is doesn't equal now
        new_app_event.remark = 'new_remark'
        self.assertNotEquals(new_app_event, get_event)

        # 1.2 post the modified event
        url = "/platform/event_models"
        response = self.fetch(url, method='POST', body='[%s]' % new_app_event.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 1.3 verify again
        url = "/platform/event_models?app=new_app"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        # now equal again
        self.assertEqual(new_app_event, get_event)

        # 2. add an event with post
        # 2.1 now there are 3 events
        url = "/platform/event_models"
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 3)

        # 2.2 add one
        added_event = SAMPLE_EVENT.copy()
        added_event.name = 'added_event'
        response = self.fetch(url, method='POST', body='[%s]' % added_event.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 now there are 4
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(len(res['values']), 4)

        # 3. modify only affect cust table
        clear_events(self.default_dao)
        clear_events(self.cust_dao)
        prepare_events(self.default_dao)

        modified_event = SAMPLE_EVENT.copy()
        modified_event.remark = 'modified'
        response = self.fetch(url, method='POST', body='[%s]' % modified_event.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 4. default keeps the same, cust is updated
        self.assertEqual(self.cust_dao.get_model_by_app_name(SAMPLE_EVENT.app, SAMPLE_EVENT.name), modified_event)
        self.assertNotEqual(self.default_dao.get_model_by_app_name(SAMPLE_EVENT.app, SAMPLE_EVENT.name), modified_event)

    def test_add_events(self):
        event1_dict = {
            'name': 'event1',
        }

        event2_dict = {
            'name': 'event2',
            'source': [
                {
                    'app': '',
                    'name': 'event1'
                }
            ]
        }

        url = "/platform/event_models"
        request_content = json.dumps([event1_dict, event2_dict])
        response = self.fetch(url, method='POST', body=request_content)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')


class TestEventQueryHandler(WebTestCase):

    def get_handlers(self):
        from nebula.views import event_model_default, event_model
        return [(r"/default/event_models/event/(.*)/(.*)", event_model_default.EventQueryHandler),
                (r"/platform/event_models/event/(.*)/(.*)", event_model.EventQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestEventQueryHandler, cls).setUpClass()
        connection_string = 'mysql://%s:%s@%s:%s' % ('nebula', 'ThreathunterNebula', '127.0.0.1', '3306')
        db_env.update_connect_string('%s/%s?charset=utf8' % (connection_string, 'nebula'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_data'),
                                     '%s/%s?charset=utf8' % (connection_string, 'nebula_default'))
        db_env.init()

    @classmethod
    def tearDownClass(cls):
        db_env.clear()
        super(TestEventQueryHandler, cls).tearDownClass()

    def setUp(self):
        super(TestEventQueryHandler, self).setUp()
        self.db_util = TestClassDBUtil()
        self.db_util.setup()
        import nebula.dao.base_dao
        nebula.dao.base_dao.Global_Data_Session = self.db_util.get_data_session()
        nebula.dao.base_dao.Global_Default_Session = self.db_util.get_default_session()
        nebula.dao.base_dao.Global_Session = self.db_util.get_session()
        self.default_dao = EventModelDefaultDao()
        self.cust_dao = EventModelCustDao()

    def tearDown(self):
        self.db_util.teardown()
        super(TestEventQueryHandler, self).tearDown()

    def test_get_event(self):
        prepare_events(self.cust_dao)
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(EventModel.from_dict(res['values'][0]), SAMPLE_EVENT)

        # not in default
        url = "/default/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # get not exist
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, 'not_exist')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

    def test_delete_event(self):
        prepare_events(self.cust_dao)
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        self.assertEqual(EventModel.from_dict(res['values'][0]), SAMPLE_EVENT)

        # delete
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # can not delete default
        clear_events(self.cust_dao)
        prepare_events(self.default_dao)
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)

    def tests_modify_event(self):
        prepare_events(self.cust_dao)
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, SAMPLE_EVENT.name)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(get_event, SAMPLE_EVENT)

        # 1. modify SAMPLE_EVENT
        # 1.1 first not equal
        new_sample = SAMPLE_EVENT.copy()
        new_sample.remark = 'modified'
        self.assertNotEquals(get_event, new_sample)

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
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(get_event, new_sample)

        # 2. add a new one
        # 2.1 get 404
        url = "/platform/event_models/event/{}/{}".format(SAMPLE_EVENT.app, 'event_to_be_add')
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 404)

        # 2.2 add one
        event_to_be_add = SAMPLE_EVENT.copy()
        event_to_be_add.name = 'event_to_be_add'
        response = self.fetch(url, method='POST', body=event_to_be_add.get_json())
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')

        # 2.3 check
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
        get_event = EventModel.from_dict(res['values'][0])
        self.assertEqual(get_event, event_to_be_add)
