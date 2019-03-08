#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import json

from nebula.views.base import BaseHandler
from nebula.dao.user_dao import authenticated
from nebula.dao.permission_dao import PermissionDao
from nebula.dao.group_dao import GroupDao

logger = logging.getLogger('nebula.api.permission')


class PermissionListHandler(BaseHandler):

    REST_URL = '/auth/permissions'

    @authenticated
    def get(self):
        """
        query permissions

        @API
        summary: query permissions
        notes: query permissions
        tags:
          - auth
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            permission_list = PermissionDao().get_permission_list()
            self.finish(json.dumps(
                {'status': 200, 'msg': 'ok', 'values': permission_list}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询用户组权限失败，请联系管理员')

    @authenticated
    def post(self):
        """
        add permissions

        @API
        summary: add permissions
        notes: add permissions
        tags:
          - auth
        parameters:
          -
            name: permissions
            in: body
            required: true
            type: json
            description: the list of the permissions json
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body

        try:
            permission_dao = PermissionDao()
            for _ in json.loads(body):
                permission_dao.add_permission(_)

            self.finish(json.dumps({'status': 200, 'msg': 'ok', 'values': []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '新建用户组权限失败，请联系管理员')

    @authenticated
    def delete(self):
        """
        delete permissions

        @API
        summary: delete permissions
        notes: delete permissions
        tags:
          - auth
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        try:
            PermissionDao().delete_permission_list()
            self.finish(json.dumps({'status': 200, 'msg': 'ok', 'values': []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '删除用户组权限失败，请联系管理员')


class PermissionQueryHandler(BaseHandler):

    REST_URL = "/auth/permissions/{app}/{codename}"

    @authenticated
    def get(self, app, codename):
        """
        get a specific permission

        @API
        summary: get a permission
        notes: get a permission
        tags:
          - auth
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: the app of the permission
          -
            name: codename
            in: path
            required: true
            type: string
            description: the codename of the permission
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            permission = PermissionDao().get_permission_by_app_and_codename(app, codename)
            values = [permission.to_dict()] if permission else []
            self.finish(json.dumps(
                {"status": 200, "msg": "ok", "values": values}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询用户组权限失败，请联系管理员')

    @authenticated
    def post(self, app, codename):
        """
        update a specific permission

        @API
        summary: update a permission
        notes: update a permission
        tags:
          - auth
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: the app of the permission
          -
            name: codename
            in: path
            required: true
            type: string
            description: the codename of the permission
          -
            name: permission
            in: body
            required: true
            type: json
            description: the json of the permission
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            permission = json.loads(self.request.body)
            PermissionDao().add_permission(permission)
            self.finish(json.dumps({"status": 200, "msg": "ok", "values": []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '修改用户组权限失败，请联系管理员')

    @authenticated
    def delete(self, app, codename):
        """
        delete a specific permission

        @API
        summary: delete a permission
        notes: delete a permission
        tags:
          - auth
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: the app of the permission
          -
            name: codename
            in: path
            required: true
            type: string
            description: the codename of the permission
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            PermissionDao().delete_permission_by_app_and_codename(app, codename)
            self.finish(json.dumps({"status": 200, "msg": "ok", "values": []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '删除用户组权限失败，请联系管理员')
