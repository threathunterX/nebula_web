#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import event
from nebula.dao.eventmeta_dao import EventMetaDefaultDao, EventMetaCustDao
from nebula.models import EventMeta
from base import WebTestCase, wsgi_safe, Auth_Code

with open('nebula/tests/data/event.json') as json_file:
    events = json.load(json_file)

# global application scope.  create Session class, engine
Session = sessionmaker()


@wsgi_safe
class TestCustomEventListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/events", event.EventListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestCustomEventListHandler, cls).setUpClass()
        cls.default_dao = EventMetaDefaultDao()
        cls.custom_dao = EventMetaCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_events(self):
        for e in events:
            self.default_dao.add_meta(EventMeta.from_dict(e))

        url = "/platform/events?auth={}".format(Auth_Code)
        post_args = json.dumps(events)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_events(self):
        for e in events:
            self.default_dao.add_meta(EventMeta.from_dict(e))
            self.custom_dao.add_meta(EventMeta.from_dict(e))

        url = "/platform/events?auth={}".format(Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_events(self):
        for e in events:
            self.default_dao.add_meta(EventMeta.from_dict(e))
            self.custom_dao.add_meta(EventMeta.from_dict(e))

        url = "/platform/events?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)


class TestCustomEventQueryHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/events/event/(.*)/(.*)", event.EventQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestCustomEventQueryHandler, cls).setUpClass()
        cls.default_dao = EventMetaDefaultDao()
        cls.custom_dao = EventMetaCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_event(self):
        url = "/platform/events/event/{}/{}?auth={}".format(
            events[0]['app'], events[0]['name'], Auth_Code)
        post_args = json.dumps(events[0])
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_event(self):
        for e in events:
            self.default_dao.add_meta(EventMeta.from_dict(e))
            self.custom_dao.add_meta(EventMeta.from_dict(e))

        url = "/platform/events/event/{}/{}?auth={}".format(
            events[0]['app'], events[0]['name'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_event(self):
        for e in events:
            self.custom_dao.add_meta(EventMeta.from_dict(e))

        url = "/platform/events/event/{}/{}?auth={}".format(
            events[0]['app'], events[0]['name'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)
