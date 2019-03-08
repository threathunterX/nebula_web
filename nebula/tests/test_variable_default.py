#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import variable_default
from nebula.dao.variablemeta_dao import VariableMetaDefaultDao
from nebula.models import VariableMeta
from base import WebTestCase, wsgi_safe, Auth_Code

# global application scope.  create Session class, engine
Session = sessionmaker()

with open('nebula/tests/data/variable.json') as json_file:
    variables = json.load(json_file)


@wsgi_safe
class TestDefaultVariableListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/variables", variable_default.VariableListHandler)]

    @classmethod
    def setUpClass(cls):
        cls.variable_dao = VariableMetaDefaultDao()
        cls.variable_dao.clear()

    def tearDown(self):
        self.variable_dao.clear()

    def test_add_variables(self):
        url = "/default/variables?auth={}".format(Auth_Code)
        post_args = json.dumps(variables)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.variable_dao.count(), 1)

    def test_get_variables(self):
        for v in variables:
            self.variable_dao.add_meta(VariableMeta.from_dict(v))

        v = variables[0]
        url = "/default/variables?app={}&type={}&name={}&modules={}&internal={}&auth={}".format(
            v['app'], v['type'], v['name'], v['module'], "true" if v['internal'] else "false", Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_variables(self):
        for v in variables:
            self.variable_dao.add_meta(VariableMeta.from_dict(v))
        url = "/default/variables?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.variable_dao.count(), 0)


class TestDefaultVariableQueryHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/default/variables/variable/(.*)/(.*)", variable_default.VariableQueryHandler)]

    @classmethod
    def setUpClass(cls):
        cls.variable_dao = VariableMetaDefaultDao()
        cls.variable_dao.clear()

    def tearDown(self):
        self.variable_dao.clear()

    def test_add_variable(self):
        url = "/default/variables/variable/{}/{}?auth={}".format(
            variables[0]['app'], variables[0]['name'], Auth_Code)
        post_args = json.dumps(variables[0])
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.variable_dao.count(), 1)

    def test_get_variables(self):
        for v in variables:
            self.variable_dao.add_meta(VariableMeta.from_dict(v))

        url = "/default/variables/variable/{}/{}?auth={}".format(
            variables[0]['app'], variables[0]['name'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_variables(self):
        for v in variables:
            self.variable_dao.add_meta(VariableMeta.from_dict(v))

        url = "/default/variables/variable/{}/{}?auth={}".format(
            variables[0]['app'], variables[0]['name'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 0)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.variable_dao.count(), 0)
