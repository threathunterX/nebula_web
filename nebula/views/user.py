#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import json

from threathunter_common.util import json_dumps

from nebula.views.base import BaseHandler
from nebula.dao.user_dao import authenticated
from nebula.dao.user_dao import UserDao
from nebula.dao.group_dao import GroupDao

logger = logging.getLogger('nebula.api.user')


class UserListHandler(BaseHandler):

    REST_URL = '/auth/users'

    @authenticated
    def get(self):
        """
        list all users

        @API
        summary: list all users
        notes: get detail of users
        tags:
          - auth
        responses:
          '200':
            description: users
            schema:
              $ref: '#/definitions/User'
          default:
            description: Unexcepted error
            schema:
              $ref: '#/definitions/Error'
        """

        self.set_header('content-type', 'application/json')
        try:
            user_list = UserDao().get_user_detail_list()

            # root用户组可以查看root、manager用户组成员
            # manager用户组可以查看普通用户组
            # 普通用户组不可用查看用户组
            manage_groups = GroupDao().get_manage_groups(self.group.id)
            result = [user for user in user_list if user[
                'group_id'] in manage_groups]

            self.finish(json_dumps(
                {'status': 200, 'msg': 'ok', 'values': result}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询用户失败，请联系管理员')

    @authenticated
    def post(self):
        """
        add a list of users

        @API
        summary: add a list of users
        notes: add a list of users
        tags:
          - auth
        parameters:
          -
            name: users
            in: body
            required: true
            type: json
            description: the list of the users json
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            # root用户组成员可以新增root、manager用户组成员
            # manager用户组成员可以新增普通用户组成员
            # 普通用户组成员不可用新增用户
            group_dao = GroupDao()
            manage_groups = group_dao.get_manage_groups(self.group.id)
            user_dao = UserDao()
            creator = self.user.id

            for user in json.loads(body):
                group_id = user['group_id']
                if group_id in manage_groups:
                    user['creator'] = creator
                    result = user_dao.add_user_and_group(user)
                    if not result:
                        self.process_error(-1, '已存在相同名字用户')
                else:
                    self.process_error(-1, '权限不足，请联系管理员')

            self.finish(json_dumps({'status': 200, 'msg': 'ok', 'values': []}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '新增用户失败，请联系管理员')


class UserQueryHandler(BaseHandler):

    REST_URL = '/auth/users/{id}'

    @authenticated
    def get(self, id):
        """
        get a specific user detail

        @API
        summary: get a specific user detail
        notes: get a specific user detail
        tags:
          - auth
        parameters:
          -
            name: id
            in: path
            required: true
            type: integer
            description: id of the user
        """

        self.set_header('content-type', 'application/json')
        try:
            user = UserDao().get_user_detail_by_id(id)

            # root用户组可以查看root、manager用户组成员
            # manager用户组可以查看普通用户组
            # 普通用户组不可用查看用户组
            manage_groups = GroupDao().get_manage_groups(self.group.id)
            if user['group_id'] not in manage_groups:
                user = {}

            self.finish(json_dumps(
                {'status': 200, 'msg': 'ok', 'values': user}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询用户失败，请联系管理员')

    @authenticated
    def post(self, id):
        """
        modify a specific user

        @API
        summary: modify a specific user
        notes: modify a specific user
        tags:
          - auth
        parameters:
          -
            name: id
            in: path
            required: true
            type: integer
            description: the id of the user
          -
            name: user
            in: body
            required: true
            type: json
            description: the body of the user
        """

        self.set_header('content-type', 'application/json')
        user = json.loads(self.request.body)

        try:
            # root用户组可以修改root、manager用户组成员
            # manager用户组可以修改普通用户组成员
            # 普通用户组不可以修改用户组成员
            manage_groups = GroupDao().get_manage_groups(self.group.id)

            user_dao = UserDao()
            old_user = user_dao.get_user_detail_by_id(id)
            old_group_id = old_user['group_id']
            new_group_id = user.get('group_id', None)
            if old_group_id in manage_groups:
                if new_group_id and new_group_id not in manage_groups:
                    return self.process_error(-1, '权限不足，请联系管理员')
                result = user_dao.update_user(id, user)
                if result:
                    self.finish(json_dumps(
                        {'status': 200, 'msg': 'ok', 'values': []}))
                else:
                    self.process_error(-1, '已存在相同用户名用户')
            else:
                self.process_error(-1, '权限不足，请联系管理员')
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '修改用户失败，请联系管理员')
