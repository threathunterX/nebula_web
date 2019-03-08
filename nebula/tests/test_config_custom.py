#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import config
from nebula.dao.config_dao import ConfigCustDao, ConfigDefaultDao
from base import WebTestCase, wsgi_safe, Auth_Code

configs = [
    {
        "last_modified": 1497421508806,
        "value": "did",
        "key": "sniffer.did.keyset"
    }
]

# global application scope.  create Session class, engine
Session = sessionmaker()


@wsgi_safe
class TestCustomConfigListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/config", config.ConfigListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestCustomConfigListHandler, cls).setUpClass()
        cls.default_dao = ConfigDefaultDao()
        cls.custom_dao = ConfigCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_configs(self):
        for c in configs:
            self.default_dao.add_config(c['key'], c['value'])

        url = "/platform/config?auth={}".format(Auth_Code)
        post_args = json.dumps(configs)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_configs(self):
        for c in configs:
            self.default_dao.add_config(c['key'], c['value'])
            self.custom_dao.add_config(c['key'], c['value'])

        url = "/platform/config?auth={}".format(Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_configs(self):
        for c in configs:
            self.custom_dao.add_config(c['key'], c['value'])

        url = "/platform/config?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)


class TestCustomConfigPropertiesHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/configproperties", config.ConfigPropertiesHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestCustomConfigPropertiesHandler, cls).setUpClass()
        cls.default_dao = ConfigDefaultDao()
        cls.custom_dao = ConfigCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_configproperties(self):
        configproperties = "\n".join(
            ["{}={}".format(_["key"], _["value"]) for _ in configs])

        url = "/platform/configproperties?auth={}".format(Auth_Code)
        response = self.fetch(url, method='POST', body=configproperties)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_configproperties(self):
        for c in configs:
            self.default_dao.add_config(c['key'], c['value'])
            self.custom_dao.add_config(c['key'], c['value'])

        configproperties = "\n".join(
            ["{}={}".format(_["key"], _["value"]) for _ in configs])
        url = "/platform/configproperties?auth={}".format(Auth_Code)
        response = self.fetch(url)
        self.assertEqual(response.body, configproperties)

    def test_delete_configproperties(self):
        for c in configs:
            self.custom_dao.add_config(c['key'], c['value'])

        url = "/platform/configproperties?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)


class TestCustomConfigHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/config/(.*)", config.ConfigHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestCustomConfigHandler, cls).setUpClass()
        cls.default_dao = ConfigDefaultDao()
        cls.custom_dao = ConfigCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_config(self):
        url = "/platform/config/{}?auth={}".format(
            configs[0]['key'], Auth_Code)
        post_args = json.dumps(configs[0])
        response = self.fetch(url, method="POST", body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_config(self):
        for c in configs:
            self.default_dao.add_config(c['key'], c['value'])
            self.custom_dao.add_config(c['key'], c['value'])

        url = "/platform/config/{}?auth={}".format(
            configs[0]['key'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_config(self):
        for c in configs:
            self.custom_dao.add_config(c['key'], c['value'])
        url = "/platform/config/{}?auth={}".format(
            configs[0]['key'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)
