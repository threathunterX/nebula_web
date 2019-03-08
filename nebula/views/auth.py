#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging

import settings
from nebula.views.base import BaseHandler
from nebula.dao.config_helper import get_config
from nebula.dao.user_dao import UserDao, authenticated, clean_auth_of_user, gen_auth_code

logger = logging.getLogger('nebula.api.auth')


def check_user_pwd(username, password):
    user = UserDao().check_user_pwd(username, password)
    if user:
        return dict(id=str(user.id), username=user.name)
    else:
        return False


def kerberos_authentication(username, password):
    try:
        import kerberos
        kerberos.checkPassword(
            username, password, settings.sso_service, settings.sso_realm)
        return dict(id='', username=username)
    except ImportError:
        return False
    except kerberos.BasicAuthError:
        return False


authentication_modules = [
    {"name": "kerberos", "function": kerberos_authentication},
    {"name": "database", "function": check_user_pwd}]


class RegisterHandler(BaseHandler):
    REST_METHODS = set()

    def get(self):
        self.base_render('register.html')


class LoginHandler(BaseHandler):
    REST_URL = '/auth/login'
    REST_METHODS = {'post', }

    def get(self):
        self.base_render('index.html')

    def post(self):
        """
        login

        @API
        summary: login
        tags:
          - auth
        parameters:
          -
            name: auth
            in: body
            required: true
            type: string
            description: username and password json
        produces:
          - application/json
        """

        result = {'auth': False, 'msg': '用户名密码错误'}
        body = json.loads(self.request.body)
        username = str(body.get('username', ''))
        password = str(body.get('password', ''))

        if username and password:
            # 获取数据库中配置的登陆验证模块
            authentications = json.loads(
                get_config('login.authentications', '{"database":true}'))
            for module in authentication_modules:
                if authentications.get(module['name'], False):
                    user = module['function'](username, password)

                    if user:

                        group_id = UserDao().get_privileges_by_name(username)
                        if group_id:
                            # generate auth_code
                            code = gen_auth_code(
                                username + password, user_name=username)
                            if code is None:
                                logger.error(
                                    'user %s can not generate auth code' % user)
                                result = {'auth': False, 'msg': "登录系统错误"}
                            else:
                                # 登陆成功,默认保存一个月
                                self.set_secure_cookie(
                                    'user', user['username'], expires_days=30)
                                self.set_secure_cookie(
                                    'user_id', user['id'], expires_days=30)
                                self.set_secure_cookie(
                                    'group_id', str(group_id), expires_days=30)
                                self.set_secure_cookie(
                                    'auth', code, expires_days=30)

                                result = {'auth': True, 'code': code}
                        else:

                            result = {'auth': False, 'msg': '用户没有权限登录系统'}

                        break
                    else:
                        result = {'auth': False, 'msg': '用户名密码错误'}

        self.write(json.dumps(result))


class ChangePasswordHandler(BaseHandler):
    REST_URL = '/auth/changepwd'
    REST_METHODS = {'post', }

    @authenticated
    def post(self):
        """
        change password @todo verify if body is a json

        @API
        summary: change password
        notes: change password
        tags:
          - auth
        parameters:
          -
            name: auth
            in: body
            required: true
            type: string
            description: username and old pwd and new pwd
        produces:
          - application/json
        """

        body = json.loads(self.request.body)
        username = body.get('username', None)
        password = body.get('password', None)
        newpassword = body.get('newpassword', None)

        if username and password and newpassword:
            user_dao = UserDao()
            if user_dao.change_pwd(username, password, newpassword):
                clean_auth_of_user(username)
                result = {'result': 0, 'msg': '修改成功'}
            else:
                result = {'result': 1, 'msg': '用户名密码错误'}
        else:
            result = {'result': 2, 'msg': '用户名密码为空'}
        self.write(json.dumps(result))


class LogoutHandler(BaseHandler):
    REST_URL = '/auth/logout'
    REST_METHODS = {'post', }

    @authenticated
    def get(self):
        self.clear_cookie('user')
        self.clear_cookie('user_id')
        self.clear_cookie('group_id')
        self.clear_cookie('auth')
        self.redirect(settings.Login_Url)

    @authenticated
    def post(self):
        """
        logout

        @API
        summary: do logout
        tags:
          - auth
        parameters:
        produces:
        """
        self.clear_cookie('user')
        self.clear_cookie('user_id')
        self.clear_cookie('group_id')
        self.clear_cookie('auth')
