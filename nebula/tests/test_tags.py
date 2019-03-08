#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import strategy
from nebula.dao.tag import TagDao
from base import WebTestCase, wsgi_safe, Auth_Code


tags = [
    {
        "app": "nebula",
        "id": 1,
        "name": "SQL注入"
    }
]

# global application scope.  create Session class, engine
Session = sessionmaker()


@wsgi_safe
class TestTagsHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/nebula/tags", strategy.TagsHandler)]

    @classmethod
    def setUpClass(cls):
        cls.tag_dao = TagDao()
        cls.tag_dao.clear()

    def tearDown(self):
        self.tag_dao.clear()

    def test_add_tags(self):
        url = "/nebula/tags?auth={}".format(Auth_Code)
        post_args = json.dumps(tags)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.tag_dao.count(), 1)

    def test_get_tags(self):
        for t in tags:
            self.tag_dao.add_tag(t)

        url = "/nebula/tags?auth={}".format(Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)


class TagQueryHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/nebula/tag/(.*)", strategy.TagQueryHandler)]

    @classmethod
    def setUpClass(cls):
        cls.tag_dao = TagDao()
        cls.tag_dao.clear()

    def tearDown(self):
        self.tag_dao.clear()

    def test_get_tag(self):
        self.tag_dao.add_tag(tags[0])
        tag = self.tag_dao.list_all_tags()[0]

        url = "/nebula/tag/{}?auth={}".format(tag['id'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)
