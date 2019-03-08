#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy.orm import sessionmaker

from nebula.views import permission
from nebula.dao.permission_dao import PermissionDao
from base import WebTestCase, wsgi_safe, Auth_Code

permissions = [
    {
        "app": "nebula",
        "remark": "内部模块定期拉取配置、计算变量",
        "id": 1,
        "codename": "fetch_config"
    }
]

# global application scope.  create Session class, engine
Session = sessionmaker()


@wsgi_safe
class TestPermissionListHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/auth/permissions", permission.PermissionListHandler)]

    @classmethod
    def setUpClass(cls):
        cls.permission_dao = PermissionDao()
        cls.permission_dao.delete_permission_list()

    def tearDown(self):
        self.permission_dao.delete_permission_list()

    def test_add_permissions(self):
        url = "/auth/permissions?auth={}".format(Auth_Code)
        post_args = json.dumps(permissions)
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.permission_dao.count(), 1)

    def test_get_permissions(self):
        for p in permissions:
            self.permission_dao.add_permission(p)

        url = "/auth/permissions?auth={}".format(Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_permissions(self):
        for p in permissions:
            self.permission_dao.add_permission(p)

        url = "/auth/permissions?auth={}".format(Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.permission_dao.count(), 0)


class TestPermissionQueryHandler(WebTestCase):

    def get_handlers(self):
        return [(r"/auth/permissions/(.*)/(.*)", permission.PermissionQueryHandler)]

    @classmethod
    def setUpClass(cls):
        cls.permission_dao = PermissionDao()
        cls.permission_dao.delete_permission_list()

    def tearDown(self):
        self.permission_dao.delete_permission_list()

    def test_add_permission(self):
        url = "/auth/permissions/{}/{}?auth={}".format(
            permissions[0]['app'], permissions[0]['codename'], Auth_Code)
        post_args = json.dumps(permissions[0])
        response = self.fetch(url, method='POST', body=post_args)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.permission_dao.count(), 1)

    def test_get_permission(self):
        for p in permissions:
            self.permission_dao.add_permission(p)

        url = "/auth/permissions/{}/{}?auth={}".format(
            permissions[0]['app'], permissions[0]['codename'], Auth_Code)
        response = self.fetch(url)
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(len(res['values']), 1)

    def test_delete_permission(self):
        for p in permissions:
            self.permission_dao.add_permission(p)

        url = "/auth/permissions/{}/{}?auth={}".format(
            permissions[0]['app'], permissions[0]['codename'], Auth_Code)
        response = self.fetch(url, method='DELETE')
        res = json.loads(response.body)
        self.assertEqual(res['status'], 200)
        self.assertEqual(res['msg'], 'ok')
        self.assertEqual(self.permission_dao.count(), 0)
