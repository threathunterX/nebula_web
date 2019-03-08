#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
try:
    import Cookie  # py2
except ImportError:
    import http.cookies as Cookie  # py3

from tornado.web import Application
from tornado.escape import json_decode
from tornado.testing import AsyncHTTPTestCase
from tornado.web import create_signed_value
from tornado.httputil import HTTPHeaders

import settings

from threathunter_common.metrics.metricsagent import MetricsAgent

Auth_Code = '7a7c4182f1bef7504a1d3d5eaa51a242'

# metrics 初始化配置
metrics_dict = {
    "app": "nebula_web",
    "redis": {
        "type": "redis",
        "host": settings.Redis_Host,
        "port": settings.Redis_Port
    },
    "influxdb": {
        "type": "influxdb",
        "url": settings.Influxdb_Url,
        "username": "test",
        "password": "test"
    },
    "server": settings.Metrics_Server
}
MetricsAgent.get_instance().initialize_by_dict(metrics_dict)

wsgi_safe_tests = []


def wsgi_safe(cls):
    wsgi_safe_tests.append(cls)
    return cls


class WebTestCase(AsyncHTTPTestCase):
    """Base class for web tests that also supports WSGI mode.

    Override get_handlers and get_app_kwargs instead of get_app.
    Append to wsgi_safe to have it run in wsgi_test as well.
    """

    def get_app(self):
        self.app = Application(self.get_handlers(), **self.get_app_kwargs())
        return self.app

    def get_handlers(self):
        raise NotImplementedError()

    def get_app_kwargs(self):
        return {'cookie_secret': 'asdfasdf'}

    @staticmethod
    def get_headers():
        cookie_secret = 'asdfasdf'
        auth = 'auth'
        auth_value = '7a7c4182f1bef7504a1d3d5eaa51a242'
        username = 'user'
        username_value = 'threathunter_test'
        userid = 'user_id'
        userid_value = '2'
        secure_auth = create_signed_value(cookie_secret, auth, auth_value)
        secure_username = create_signed_value(
            cookie_secret, username, username_value)
        secure_userid = create_signed_value(
            cookie_secret, userid, userid_value)
        headers = HTTPHeaders()
        headers.add("Cookie", "=".join((auth, secure_auth)))
        headers.add("Cookie", "=".join((username, secure_username)))
        headers.add("Cookie", "=".join((userid, secure_userid)))

        return headers

    @staticmethod
    def get_cookie():
        cookie_secret = 'asdfasdf'
        auth = 'auth'
        auth_value = '7a7c4182f1bef7504a1d3d5eaa51a242'
        username = 'user'
        username_value = 'threathunter_test'
        userid = 'user_id'
        userid_value = '2'
        secure_auth = create_signed_value(cookie_secret, auth, auth_value)
        secure_username = create_signed_value(
            cookie_secret, username, username_value)
        secure_userid = create_signed_value(
            cookie_secret, userid, userid_value)
        cookie = Cookie.SimpleCookie()
        cookie[auth] = secure_auth
        cookie[userid] = secure_userid
        cookie[username] = secure_username
        return cookie

    def fetch_json(self, path):
        return json_decode(self.fetch(path).body)


def get_hour_start(point=None):
    """
    获取point时间戳所在的小时的开始的时间戳, 默认获取当前时间所在小时的开始时的时间戳
    """
    if point is None:
        p = time.time()
    else:
        p = point

    return ((int(p) / 3600) * 3600) * 1.0


def get_current_hour_interval():
    fromtime = int(get_hour_start()) * 1000
    endtime = int(time.time() * 1000)
    return fromtime, endtime


def get_last_hour_interval():
    current_hour = int(get_hour_start()) * 1000
    fromtime = current_hour - (3600 * 1000)
    endtime = current_hour - 1
    return fromtime, endtime
