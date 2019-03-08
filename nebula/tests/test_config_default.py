#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import config_default
from nebula.dao.config_dao import ConfigDefaultDao
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
class TestDefaultConfigListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/config", config_default.ConfigListHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultConfigListHandler, cls).setUpClass()
        cls.config_dao = ConfigDefaultDao()
        cls.config_dao.clear()

    def tearDown(self):
        self.config_dao.clear()

    def test_add_configs(self):
        url = "/default/config?auth={}".format(Auth_Code)
        post_args = json.dumps(configs)
        response = self.fetch(url, method="POST", body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.config_dao.count(), 1)

    def test_get_configs(self):
        for config in configs:
            self.config_dao.add_config(config['key'], config['value'])

        url = "/default/config?auth={}".format(Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_configs(self):
        for config in configs:
            self.config_dao.add_config(config['key'], config['value'])

        url = "/default/config?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.config_dao.count(), 0)


class TestDefaultConfigPropertiesHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/configproperties", config_default.ConfigPropertiesHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultConfigPropertiesHandler, cls).setUpClass()
        cls.config_dao = ConfigDefaultDao()
        cls.config_dao.clear()

    def tearDown(self):
        self.config_dao.clear()

    def test_add_configproperties(self):
        configproperties = "\n".join(
            ["{}={}".format(_["key"], _["value"]) for _ in configs])

        url = "/default/configproperties?auth={}".format(Auth_Code)
        response = self.fetch(url, method='POST', body=configproperties)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.config_dao.count(), 1)

    def test_get_configproperties(self):
        for config in configs:
            self.config_dao.add_config(config['key'], config['value'])
        configproperties = "\n".join(
            ["{}={}".format(_["key"], _["value"]) for _ in configs])

        url = "/default/configproperties?auth={}".format(Auth_Code)
        response = self.fetch(url)
        self.assertEqual(response.body, configproperties)

    def test_delete_configproperties(self):
        for config in configs:
            self.config_dao.add_config(config['key'], config['value'])

        url = "/default/configproperties?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.config_dao.count(), 0)


class TestDefaultConfigHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/config/(.*)", config_default.ConfigHandler)]

    @classmethod
    def setUpClass(cls):
        super(TestDefaultConfigHandler, cls).setUpClass()
        cls.config_dao = ConfigDefaultDao()
        cls.config_dao.clear()

    def tearDown(self):
        self.config_dao.clear()

    def test_add_config(self):
        url = "/default/config/{}?auth={}".format(configs[0]['key'], Auth_Code)
        post_args = json.dumps(configs[0])
        response = self.fetch(url, method="POST", body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.config_dao.count(), 1)

    def test_get_config(self):
        for config in configs:
            self.config_dao.add_config(config['key'], config['value'])

        url = "/default/config/{}?auth={}".format(configs[0]['key'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_config(self):
        for config in configs:
            self.config_dao.add_config(config['key'], config['value'])

        url = "/default/config/{}?auth={}".format(configs[0]['key'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.config_dao.count(), 0)
