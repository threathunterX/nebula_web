#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from tornado.ioloop import PeriodicCallback

from threathunter_common.metrics.redismetrics import RedisMetrics
from threathunter_common.event import Event
from threathunter_common.util import millis_now

import settings
from .babel import get_global_value_client


class NetworkStatisticsTask(object):

    def __init__(self):
        self._task = None
        self.metrics_recorder = RedisMetrics(host=settings.Redis_Host, port=settings.Redis_Port)
        self.client = get_global_value_client()

    def _run(self):
        """
        请求_global__variableglobalvalue_request,得到http_count五分钟请求数量,记录metrics
        """

        now = millis_now()
        property_values = dict(count=1, varnames=[''])
        request = Event('__all__', '_global__variableglobalvalue_request',
                        '', now, property_values)
        response = self.client.send(request, 'nebula', False, 10)

        value = 0
        if response[0]:
            for resultEvent in response[1]:
                if resultEvent.property_values.get('count') > 0 and \
                        resultEvent.property_values.get('varvalues')[0] is not None:
                    value += resultEvent.property_values.get('varvalues')[0]

        self.metrics_recorder.add_metrics(
            'default', 'web.network', {}, int(value), 86400 * 7, timestamp=now)

    def start(self):
        """
        定时任务,请求http数量统计
        """
        self._task = PeriodicCallback(self._run, 5 * 60 * 1000)
        self._task.start()

    def stop(self):
        self._task.stop()

    def close(self):
        self.stop()

    def __del__(self):
        self.stop()
