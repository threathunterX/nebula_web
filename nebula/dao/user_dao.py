#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import hashlib
import random
import time
import functools
try:
    import urlparse  # py2
except ImportError:
    import urllib.parse as urlparse  # py3

try:
    from urllib import urlencode  # py2
except ImportError:
    from urllib.parse import urlencode  # py3

import threading

from threathunter_common.util import millis_now

import settings
from nebula.dao.base_dao import BaseDao
from nebula.dao.group_dao import UserGroupDao, GroupDao
from nebula.models import UserModel as Model
from nebula.models import SessionModel


class SessionDao(BaseDao):

    def get_session_jar(self):
        """
        将数据库持久化保存的session auth code缓存在内存中
        """
        query = self.session.query(SessionModel)
        now = time.time()
        query = query.filter(SessionModel.expire_time > now)

        Session_Jar = {session.auth_code: (session.expire_time, session.user_name)
                       for session in query.all()}
        return Session_Jar

    def add_session(self, session):
        """
        将session数据存入
        :param session:
        :return:
        """
        new_session = SessionModel.from_dict(session)
        self.session.add(new_session)
        self.session.commit()

    def delete_session(self, auth_code):
        """
        删除过期的auth_code，用户需要重新登录
        :param auth_code:
        :return:
        """
        query = self.session.query(SessionModel)
        query = query.filter(SessionModel.auth_code == auth_code)
        query.delete()
        self.session.commit()

    def delete_session_by_username(self, user_name):
        """
        用户修改密码后，需要删除原来用户的session
        :param user_name:
        :return:
        """
        query = self.session.query(SessionModel)
        query = query.filter(SessionModel.user_name == user_name)
        query.delete()
        self.session.commit()

    def delete_expire_session(self):
        """
        删除过期session
        :return:
        """
        query = self.session.query(SessionModel)
        now = time.time()
        query = query.filter(SessionModel.expire_time <= now)
        query.delete()
        self.session.commit()


# 将数据库初始化的session导入缓存
Session_Jar = dict()
Session_Jar_Lock = threading.Lock()
# internal authcode
Internal_Auth = settings.Internal_Auth.values()
Internal_Hosts = settings.Internal_Hosts


def authenticated(method):
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in, they will be redirected to the configured
    `login url <RequestHandler.get_login_url>`.

    If you configure a login url with a query parameter, Tornado will
    assume you know what you're doing and use it as-is.  If not, it
    will add a `next` parameter so the login page knows where to send
    you once you're logged in.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        auth = self.get_query_argument('auth', '') or ''
        if not auth:
            # try the cookie
            try:
                auth = self.get_secure_cookie('auth')
            except:
                pass

        if auth:
            if is_auth_valid(auth) or is_auth_internal(auth, self.request.remote_ip):
                self.user = UserDao().get_user_by_id(self.get_secure_cookie('user_id'))
                self.group = GroupDao().get_group_by_id(self.get_secure_cookie('group_id'))
                return method(self, *args, **kwargs)

        url = self.get_login_url()
        if "?" not in url:
            if urlparse.urlsplit(url).scheme:
                # if login url is absolute, make next absolute too
                next_url = self.request.full_url()
            else:
                next_url = self.request.uri
            url += "?" + urlencode(dict(next=next_url))
        self.redirect(url)
        return

    return wrapper


def init_session_jar():
    """
    初始化session_jar，查询数据库保留的未过期的session，删除过期的session
    :return:
    """
    global Session_Jar
    session_dao = SessionDao()
    with Session_Jar_Lock:
        Session_Jar = session_dao.get_session_jar()
        session_dao.delete_expire_session()


def default_auth_code_gen(ingredient):
    return hashlib.md5(ingredient + unicode(random.randint(0, 1000))).hexdigest()


def gen_auth_code(ingredient, expire_day=None, handler=None, user_name=None):
    """
    return expire天的认证code, 生成失败返回None
    """
    if expire_day is None:
        expire_day = 10  # 默认认证保质期10day

    # 生成唯一的session id, 生成过期时间戳
    generater = handler or default_auth_code_gen
    auth_code = generater(ingredient)
    now = time.time()
    expire_time = now + 86400 * expire_day

    with Session_Jar_Lock:
        Session_Jar[auth_code] = (expire_time, user_name)
        session = {'user_name': user_name, 'auth_code': auth_code, 'expire_time': expire_time}
        SessionDao().add_session(session)
    return auth_code


def is_auth_valid(auth_code):
    now = time.time()
    if Session_Jar.has_key(auth_code):
        if Session_Jar.get(auth_code)[0] > now:
            return True
        else:
            with Session_Jar_Lock:
                Session_Jar.pop(auth_code)
                SessionDao().delete_session(auth_code)

    return False


def clean_auth_of_user(clean_user):
    global Session_Jar
    with Session_Jar_Lock:
        session_dao = SessionDao()
        session_dao.delete_session_by_username(clean_user)
        Session_Jar = session_dao.get_session_jar()


def is_auth_internal(auth_code, remote_ip="127.0.0.1"):
    if auth_code and remote_ip:
        if remote_ip in Internal_Hosts or auth_code in Internal_Auth:
            return True

    return False


class UserDao(BaseDao):

    def _get_user_by_name(self, name):
        """
        根据用户名查询唯一的用户
        """
        query = self.session.query(Model)
        return query.filter(Model.name == name).first()

    def get_user_by_id(self, user_id):
        """
        根据用户id查询用户名
        """
        query = self.session.query(Model)
        return query.filter(Model.id == user_id).first()

    def add_user_and_group(self, user):
        new_user = Model.from_dict(user)
        existing_user = self._get_user_by_name(new_user.name)

        if existing_user or not user.get('group_id'):
            return False
        else:
            self.session.add(new_user)
            self.session.commit()

        user_id = new_user.id
        group_id = user['group_id']
        UserGroupDao().add_user_group(dict(user_id=user_id, group_id=group_id))

        return True

    def update_user(self, user_id, user):
        """
        更新用户信息及用户组信息
        """
        query = self.session.query(Model)
        existing = query.filter(Model.id == user_id).first()

        name = user.get('name', None)
        password = user.get('password', None)
        is_active = user.get('is_active', None)
        group_id = user.get('group_id', None)

        if existing:
            if name and name != existing.name:
                if self._get_user_by_name(name):
                    return False
                existing.name = name
            if password:
                existing.password = hashlib.sha1(password).hexdigest()
            if is_active is not None:
                existing.is_active = is_active

            existing.last_modified = millis_now()
            self.session.merge(existing)
            self.session.commit()

            if group_id:
                UserGroupDao().update_group_id(existing.id, group_id)

            return True

    def get_user_detail_list(self):
        query = self.session.query(Model)
        return [self.get_user_detail_by_id(_.id) for _ in query.all()]

    def get_user_detail_by_id(self, user_id):
        """
        获取用户详细信息
        """
        user = self.get_user_by_id(user_id).to_dict()

        group = UserGroupDao().get_group_by_user(user['id'])
        user['group_id'] = group['id']
        user['group_name'] = group['name']
        user['privileges'] = group['privileges']
        user['blocked'] = group['blocked']
        creator = self.get_user_by_id(user['creator'])
        user['creator'] = creator.name

        return user

    def check_user_pwd(self, username, password):
        """
        :username 用户名
        :password 密码
        return 返回用户所有信息
        """
        sha1_pwd = str(hashlib.sha1(password).hexdigest())
        query = self.session.query(Model)
        user = query.filter(Model.name == username,
                            Model.password == sha1_pwd).first()
        if user:
            user.last_login = millis_now()
            self.session.merge(user)
            self.session.commit()
            return self.get_user_by_id(user.id)
        return False

    def get_privileges_by_name(self, username):
        """
        :param username:
        :return: 根据用户名获取访问权限
        """
        user = self._get_user_by_name(username)
        if user and user.is_active:
            group = UserGroupDao().get_group_by_user(user.id)
            if group and group['is_active']:
                return group['id']

        return False

    def change_pwd(self, username, password, newpassword):
        """
        :username 用户名
        :password 密码
        :newpassword 新密码
        return 返回密码更改结果
        """
        old_pwd = str(hashlib.sha1(password).hexdigest())
        new_pwd = str(hashlib.sha1(newpassword).hexdigest())
        query = self.session.query(Model)

        user = query.filter(Model.name == username).filter(
            Model.password == old_pwd).first()
        if user:
            user.password = new_pwd
            user.last_modified = millis_now()
            self.session.merge(user)
            self.session.commit()
            return True

        return False
