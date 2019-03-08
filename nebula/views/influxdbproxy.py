#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import urllib

from .base import BaseHandler
from nebula.dao.user_dao import authenticated

from threathunter_common.util import json_dumps
from threathunter_common.metrics import influxdbproxy
from threathunter_common.metrics.metricsagent import MetricsAgent


class InfluxdbProxyHandler(BaseHandler):
    REST_URL = "/metricsproxy/"

#    @authenticated
    def get(self):
        """
        get metrics via influxdb proxy

        @API
        summary: get metrics via influxdb proxy
        notes: get metrics via influxdb proxy
        tags:
          - platform
        parameters:
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        u = self.request.uri
        unquoted = urllib.unquote_plus(u)
        print u, unquoted
        if "list series" in unquoted:
            result = [{"name": "list_series_result",
                       "columns": ["time", "name"], "points":[]}]
        elif "select *" in unquoted:
            result = [{"points": [], "name": "", "columns": ["time", "value"]}]
        elif "select" in unquoted:
            result = influxdbproxy.get_metrics(u)
        else:
            result = {}
        self.finish(json_dumps(result))

    def post(self):
        """
        add metrics via influxdb proxy
        """
        path = self.request.path.split('/')
        metrics = json.loads(self.request.body)
        metric_agent = MetricsAgent.get_instance()
        expire_seconds = 86400 * 7
        if 'db' in path:
            db = path[3]
            for metric in metrics:
                metric_name = metric['name']
                columns = metric['columns']
                value_index = columns.index('value')
                points = metric['points']
                for point in points:
                    value = point[value_index]
                    tags = {columns[i]: point[i] for i in range(len(point)) if i != value_index}
                    metric_agent.add_metrics(
                        db, metric_name, tags, value, expire_seconds)
            self.finish(json_dumps({'status': 0, 'msg': 'ok'}))
        else:
            self.finish(json_dumps({'status': 0, 'msg': 'db not exist'}))
