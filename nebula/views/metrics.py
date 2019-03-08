#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .base import BaseHandler
#from nebula.middleware.tornado_rest_swagger.restutil import rest_class, rest_method
from nebula.dao.user_dao import authenticated

from threathunter_common.util import json_dumps, millis_now
from threathunter_common.metrics.metricsagent import MetricsAgent

def _get_metrics_data(name, accumulative, fromtime, endtime, window):
    db = "default"
    if name.startswith("system"):
        # hack for old grafana
        accumulative = False
    if accumulative:
        aggregation_type = "sum"
    else:
        aggregation_type = "max"

    data = MetricsAgent.get_instance().query(db, name, aggregation_type, fromtime, endtime, window/1000, {}, [])
    start = fromtime
    if data:
        minimum = min(data.keys())
        start = start + (minimum - start) % window
    values = []
    ts = start
    while ts <= endtime:
        entry = data.get(ts)
        if not entry:
            values.append(None)
        else:
            values.append(entry.get(tuple()))
        ts += window

    return {"start": start, "interval": window, "values": values}


class MetricsHandler(BaseHandler):
    REST_URL = "/platform/metrics/{name}"

    @authenticated
    def get(self, name):
        """
        get named metrics' value
        
        @API
        summary: get named metric's value
        notes: get metrics value of a given name
        tags:
          - platform
        parameters:
          -
            name: name
            in: path
            required: true
            type: string
            description: metrics name
          -
            name: period
            in: query
            required: true
            type: int
            default: 60000
            description: indicated the time between two original data points that are recorded
          -
            name: window
            in: query
            required: false
            type: int
            default: 60000
            description: indicated the time between two returned data points, the window value should be multiples of period
          - 
            name: fromtime
            in: query
            required: false
            type: int
            description: the timestamp of the first data point
          - 
            name: endtime
            in: query
            required: false
            type: int
            description: the timestamp of the last data point
          - 
            name: accumulative
            in: query
            required: false
            default: true
            type: boolean
            description: whether the metrics is accumulative
        produces:
          - application/json
        """
        self.set_header("Content-Type", "application/json")

        window = int(self.get_argument("window", "0"))
        fromtime = int(self.get_argument("fromtime", millis_now() - 180000))
        endtime = int(self.get_argument("endtime", millis_now()))
        accumulative = "true" == (self.get_argument("accumulative", "true"))

        try:
            data = _get_metrics_data(name, accumulative, fromtime, endtime, window)
            response = {
                "status": 0,
                "msg": "ok",
                "values": [data]
            }
            self.finish(json_dumps(response, self.get_argument("pretty", False)))
        except Exception as err:
            self.finish(json_dumps({"status": -1, "msg": "fail to get metrics data"}))


class BatchMetricsHandler(BaseHandler):
    REST_URL = "/platform/batchmetrics/"

    @authenticated
    def get(self):
        """
        get metrics value
        
        @API
        summary: get metrics value
        notes: get metrics value of a group of metrics
        tags:
          - platform
        parameters:
          -
            name: names
            in: query
            required: true
            type: string
            description: indicated a group of metrics names
          -
            name: period
            in: query
            required: true
            type: int
            default: 60000
            description: indicated the time between two original data points that are recorded
          -
            name: window
            in: query
            required: false
            type: int
            default: 60000
            description: indicated the time between two returned data points, the window value should be multiples of period
          - 
            name: fromtime
            in: query
            required: false
            type: int
            description: the timestamp of the first data point
          - 
            name: endtime
            in: query
            required: false
            type: int
            description: the timestamp of the last data point
          - 
            name: accumulative
            in: query
            required: false
            default: true
            type: boolean
            description: whether the metrics is accumulative
        produces:
          - application/json
        """
        self.set_header("Content-Type", "application/json")

        names = self.get_argument("names").split(",")
        period = int(self.get_argument("period"))
        window = int(self.get_argument("window", "0"))
        fromtime = int(self.get_argument("fromtime", millis_now() - 180000))
        endtime = int(self.get_argument("endtime", millis_now()))
        accumulative = "true" == (self.get_argument("accumulative", "true"))

        try:
            values = []
            for name in names:
                data = _get_metrics_data(name, accumulative, fromtime, endtime, window)
                data["name"] = name
                values.append(data)

            response = {
                "status": 0,
                "msg": "ok",
                "values": values
            }
            self.finish(json_dumps(response, self.get_argument("pretty", False)))
        except Exception as err:
            self.finish(json_dumps({"status": -1, "msg": "fail to get metrics data"}))

