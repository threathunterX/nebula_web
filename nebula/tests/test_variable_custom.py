#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import variable
from nebula.dao.variablemeta_dao import VariableMetaDefaultDao, VariableMetaCustDao
from nebula.models import VariableMeta
from base import WebTestCase, wsgi_safe, Auth_Code


# global application scope.  create Session class, engine
Session = sessionmaker()

with open('nebula/tests/data/variable.json') as json_file:
    variables = json.load(json_file)


@wsgi_safe
class TestCustomVariableListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/variables", variable.VariableListHandler)]

    @classmethod
    def setUpClass(cls):
        cls.default_dao = VariableMetaDefaultDao()
        cls.custom_dao = VariableMetaCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_variables(self):
        url = "/platform/variables?auth={}".format(Auth_Code)
        post_args = json.dumps(variables)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_variables(self):
        for v in variables:
            self.default_dao.add_meta(VariableMeta.from_dict(v))
            self.custom_dao.add_meta(VariableMeta.from_dict(v))

        v = variables[0]
        url = "/platform/variables?app={}&type={}&name={}&modules={}&internal={}&auth={}".format(
            v['app'], v['type'], v['name'], v['module'], "true" if v['internal'] else "false", Auth_Code)

        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_variables(self):
        for v in variables:
            self.custom_dao.add_meta(VariableMeta.from_dict(v))

        url = "/platform/variables?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)


class TestCustomVariableQueryHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/platform/variables/variable/(.*)/(.*)", variable.VariableQueryHandler)]

    @classmethod
    def setUpClass(cls):
        cls.default_dao = VariableMetaDefaultDao()
        cls.custom_dao = VariableMetaCustDao()
        cls.default_dao.clear()
        cls.custom_dao.clear()

    def tearDown(self):
        self.default_dao.clear()
        self.custom_dao.clear()

    def test_add_variable(self):
        url = "/platform/variables/variable/{}/{}?auth={}".format(
            variables[0]['app'], variables[0]['name'], Auth_Code)
        post_args = json.dumps(variables[0])
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 1)

    def test_get_variable(self):
        for v in variables:
            self.custom_dao.add_meta(VariableMeta.from_dict(v))

        url = "/platform/variables/variable/{}/{}?auth={}".format(
            variables[0]['app'], variables[0]['name'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_variable(self):
        for v in variables:
            self.custom_dao.add_meta(VariableMeta.from_dict(v))

        url = "/platform/variables/variable/{}/{}?auth={}".format(
            variables[0]['app'], variables[0]['name'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.custom_dao.count(), 0)
