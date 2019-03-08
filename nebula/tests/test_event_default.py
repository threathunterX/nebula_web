#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import event_default
from nebula.dao.eventmeta_dao import EventMetaDefaultDao
from nebula.models import EventMeta
from base import WebTestCase, wsgi_safe, Auth_Code

with open('nebula/tests/data/event.json') as json_file:
    events = json.load(json_file)

# global application scope.  create Session class, engine
Session = sessionmaker()


@wsgi_safe
class TestDefaultEventListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/events", event_default.EventListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultEventListHandler, cls).setUpClass()
        cls.event_dao = EventMetaDefaultDao()
        cls.event_dao.clear()

    def tearDown(self):
        self.event_dao.clear()

    def test_add_events(self):
        url = "/default/events?auth={}".format(Auth_Code)
        post_args = json.dumps(events)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.event_dao.count(), 1)

    def test_get_events(self):
        for e in events:
            self.event_dao.add_meta(EventMeta.from_dict(e))

        url = "/default/events?auth={}".format(Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_events(self):
        for e in events:
            self.event_dao.add_meta(EventMeta.from_dict(e))

        url = "/default/events?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.event_dao.count(), 0)


class TestDefaultEventQueryHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/events/event/(.*)/(.*)", event_default.EventQueryHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultEventQueryHandler, cls).setUpClass()
        cls.event_dao = EventMetaDefaultDao()
        cls.event_dao.clear()

    def tearDown(self):
        self.event_dao.clear()

    def test_add_event(self):
        url = "/default/events/event/{}/{}?auth={}".format(
            events[0]['app'], events[0]['name'], Auth_Code)
        post_args = json.dumps(events[0])
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.event_dao.count(), 1)

    def test_get_event(self):
        for e in events:
            self.event_dao.add_meta(EventMeta.from_dict(e))

        url = "/default/events/event/{}/{}?auth={}".format(
            events[0]['app'], events[0]['name'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_event(self):
        for e in events:
            self.event_dao.add_meta(EventMeta.from_dict(e))

        url = "/default/events/event/{}/{}?auth={}".format(
            events[0]['app'], events[0]['name'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.event_dao.count(), 0)
