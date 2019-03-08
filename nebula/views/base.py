#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json

from tornado.web import RequestHandler

from threathunter_common.metrics.metricsrecorder import MetricsRecorder
from threathunter_common.metrics.metricsagent import get_latency_str_for_millisecond

import settings

cost_range_metrics = MetricsRecorder(
    "web.api.cost.range", db="default", type="count", expire=86400 * 7, interval=60)
cost_max_metrics = MetricsRecorder(
    "web.api.cost.max", db="default", type="max", expire=86400 * 7, interval=60)
cost_min_metrics = MetricsRecorder(
    "web.api.cost.min", db="default", type="min", expire=86400 * 7, interval=60)
cost_avg_metrics = MetricsRecorder(
    "web.api.cost.avg", db="default", type="avg", expire=86400 * 7, interval=60)
user_access_metrics = MetricsRecorder(
    "web.api.user.count", db="default", type="count", expire=86400 * 7, interval=60)


class BaseHandler(RequestHandler):

    def data_received(self, chunk):
        pass

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def initialize(self):
        self.global_vars = {}
        self.global_vars_update({"user": self.current_user})

    def get_context(self):
        """
        设置全局变量
        @display_menu:不显示菜单
        """

        return {'site_title': settings.SITE_TITLE, 'display_menu': True, 'global_vars': json.dumps(self.global_vars)}

    def global_vars_update(self, var_dict={}):
        """
        更新全局JS变量
        """
        self.global_vars.update(var_dict)

    def base_render(self, template_name, **kwargs):
        context = self.get_context()  # 中括号里面填写继承此基类的子类名字
        context.update(kwargs)  # 将子类的新参数集更新到context中
        self.render(template_name, **context)

    def process_error(self, status=-1, msg="error"):
        self.set_header('content-type', 'application/json')
        self.finish(json.dumps({"status": status, "msg": msg}))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

    def on_finish(self):
        """
        API请求完成后,metrics记录API请求时间和路径
        """
        path = self.request.path.split('/')
        group = path[1] if not path[0] else path[0]
        cost = int(1000.0 * self.request.request_time())
        cost_range = get_latency_str_for_millisecond(cost)
        method = self.request.method
        status = self.get_status()
        tags = dict(group=group, path=self.request.path,
                    range=cost_range, method=method, status=status)

        cost_range_metrics.record(1, tags)
        cost_avg_metrics.record(cost, tags)
        cost_max_metrics.record(cost, tags)
        cost_min_metrics.record(cost, tags)

        if hasattr(self, 'user') and getattr(self, 'user'):
            user = self.user.name
            tags = dict(path=self.request.path, user=user)
            user_access_metrics.record(1, tags)
