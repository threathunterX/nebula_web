#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import json

from threathunter_common.util import json_dumps

from nebula.views.base import BaseHandler
from nebula.dao.user_dao import authenticated
from nebula.dao.group_dao import GroupDao
from nebula.dao.permission_dao import GroupPermissionDao

logger = logging.getLogger('nebula.api.group')


class GroupListHandler(BaseHandler):

    REST_URL = '/auth/groups'

    @authenticated
    def get(self):
        """
        list all groups

        @API
        summary: list all groups
        notes: get details for groups
        tags:
          - auth
        responses:
          '200':
            description: user groups
            schema:
              $ref: '#/definitions/UserGroup'
          default:
            description: Unexcepted error
            schema:
              $ref: '#/definitions/Error'
        """

        self.set_header('content-type', 'application/json')
        try:
            # root用户组可以查看root、manager用户组
            # manager用户组可以查看普通用户组
            # 普通用户组不可用查看用户组
            group_dao = GroupDao()
            group_list = group_dao.get_group_detail_list()
            manage_groups = group_dao.get_manage_groups(self.group.id)

            result = [group for group in group_list if group[
                'id'] in manage_groups]

            self.finish(json_dumps(
                {'status': 200, 'msg': 'ok', 'values': result}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询用户组失败，请联系管理员')

    @authenticated
    def post(self):
        """
        add a list of groups

        @API
        summary: add a list of groups
        notes: add a list of groups
        tags:
          - auth
        parameters:
          -
            name: groups
            in: body
            required: true
            type: json
            description: the list of the groups json
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            # 判断当前用户所在用户组，只有manager用户组有权限新建普通用户组
            if self.group.is_manager():
                group_dao = GroupDao()
                creator = self.user.id

                for _ in json.loads(body):
                    _['creator'] = creator
                    group_dao.add_group(_)

                self.finish(json_dumps(
                    {'status': 200, 'msg': 'ok', 'values': []}))
            else:
                self.process_error(-1, '权限不足，请联系管理员')
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '新建用户组失败，请联系管理员')


class GroupQueryHandler(BaseHandler):

    REST_URL = '/auth/groups/{id}'

    @authenticated
    def get(self, id):
        """
        get a specific group detail

        @API
        summary: get a specific group detail
        notes: get a specific group detail
        tags:
          - auth
        parameters:
          -
            name: id
            in: path
            required: true
            type: integer
            description: id of the group
        """

        self.set_header('content-type', 'application/json')
        try:
            # root用户组可以查看root、manager用户组
            # manager用户组可以查看普通用户组
            # 普通用户组不可用查看用户组
            group_dao = GroupDao()
            manage_groups = group_dao.get_manage_groups(self.group.id)
            group_id = int(id)
            if group_id in manage_groups:
                group = group_dao.get_group_detail_by_id(id)
            else:
                group = {}

            self.finish(json_dumps(
                {'status': 200, 'msg': 'ok', 'values': group}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询用户组失败，请联系管理员')

    @authenticated
    def post(self, id):
        """
        modify a specific group

        @API
        summary: modify a specific group
        notes: modify a specific group
        tags:
          - auth
        parameters:
          -
            name: id
            in: path
            required: true
            type: integer
            description: the id of the group
          -
            name: group
            in: body
            required: true
            type: json
            description: the json of group
        """
        self.set_header('content-type', 'application/json')
        group = json.loads(self.request.body)

        try:
            # root用户组不可以修改root、manager、普通用户组
            # manager用户组可以修改普通用户组
            # 普通用户组不可用修改用户组
            group_id = int(id)
            group_dao = GroupDao()
            manage_groups = group_dao.get_manage_groups(self.group.id)

            if self.group.is_manager() and group_id in manage_groups:
                group_dao.update_group(id, group)
                self.finish(json_dumps(
                    {'status': 200, 'msg': 'ok', 'values': []}))
            else:
                self.process_error(-1, '权限不足，请联系管理员')
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '修改用户组失败，请联系管理员')


class StrategyAccessHandler(BaseHandler):

    REST_URL = '/auth/strategy_access'

    @authenticated
    def get(self):
        """
        创建用户组时，规则管理，查询配置策略可见用户组

        @API
        summary: get strategy access groups
        notes: user groups
        tags:
          - auth
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            # 只有manager用户组可以创建用户组
            if self.group.is_manager():
                access_groups = GroupDao().get_group_strategy_access()
                self.finish(json.dumps(
                    {"status": 200, "msg": "ok", "values": access_groups}))
            else:
                self.finish(json.dumps(
                    {"status": 200, "msg": "ok", "values": []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, "查询失败，请联系管理员")


class PrivilegesHandler(BaseHandler):

    REST_URL = '/auth/privileges'

    @authenticated
    def get(self):
        """
        登录后，查询用户所在用户组，能查看的页面权限

        @API
        summary: get user group view privileges
        notes: user group privileges
        tags:
          - auth
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            group_id = self.get_secure_cookie('group_id')

            if group_id:
                privileges = GroupPermissionDao().get_group_extra_settings(
                    group_id, 'view_privileges')
                privileges = json.loads(privileges) if privileges else []
                self.finish(json.dumps(
                    {"status": 200, "msg": "ok", "values": privileges}))
            else:
                self.finish(json.dumps(
                    {"status": 200, "msg": "ok", "values": []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, "用户权限获取失败，请联系管理员")
