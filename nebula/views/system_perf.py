#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import psutil

from .base import BaseHandler
from nebula.dao.user_dao import authenticated
from common.utils import get_hour_start

from threathunter_common.util import json_dumps, millis_now
from threathunter_common.metrics.metricsagent import MetricsAgent
from crontab.tasks import system_status

logger = logging.getLogger('nebula.api.system_perf')


class SystemPerformanceHandler(BaseHandler):
    REST_URL = "/system/performance/digest"
    @authenticated
    def get(self):
        """
        get system performance metrics

        @API
        summary: system performance
        notes: get system performance metrics
        tags:
          - system
        produces:
          - application/json
        """
        result = system_status.get_system_status()
        return self.finish(json_dumps(result))
        # db = 'default'
        # metrics_name = 'system.{}'
        #
        #     result = {'memory': memory_statistics,
        #               'cpu': cpu_statistics,
        #               'space': space_percent}
        #
        #     return self.finish(json_dumps(result))
        # except Exception as e:
        #     logger.error(e)
        #     self.process_error(-1, 'fail to get system performance')

    # @authenticated
    # def get(self):
    #     """
    #     get system performance metrics
    #
    #     @API
    #     summary: system performance
    #     notes: get system performance metrics
    #     tags:
    #       - system
    #     produces:
    #       - application/json
    #     """
    #     db = 'default'
    #     metrics_name = 'system.{}'
    #     interval = 5 * 60 * 1000
    #     from_time = get_hour_start() * 1000
    #     end_time = millis_now() / interval * interval
    #     metrics_agent = MetricsAgent.get_instance()
    #
    #     try:
    #         # 查询内存用量
    #         memory_name = metrics_name.format('memratio')
    #         memory_metrics = metrics_agent.query(
    #             db, memory_name, 'max', from_time, end_time, interval)
    #         memory_statistics = list()
    #         for ts in range(from_time, end_time, interval):
    #             if memory_metrics.has_key(ts):
    #                 memory_statistics.append(
    #                     int(memory_metrics[ts].values()[0]))
    #             else:
    #                 memory_statistics.append(0)
    #
    #         # 查询CPU用量
    #         cpu_name = metrics_name.format('cpuload')
    #         cpu_metrics = metrics_agent.query(
    #             db, cpu_name, 'max', from_time, end_time, interval)
    #         cpu_statistics = list()
    #         for ts in range(from_time, end_time, interval):
    #             if cpu_metrics.has_key(ts):
    #                 cpu_statistics.append(int(cpu_metrics[ts].values()[0]))
    #             else:
    #                 cpu_statistics.append(0)
    #
    #         # 查询磁盘用量，查询一分钟内记录的磁盘用量最大值
    #         space_name = metrics_name.format('spaceratio')
    #         space_interval = 60000
    #         space_metrics = metrics_agent.query(
    #             db, space_name, 'max', end_time - space_interval, end_time, space_interval)
    #         if space_metrics:
    #             space_statistics = space_metrics.values()[0]
    #             space_percent = int(space_statistics.values()[0])
    #         else:
    #             space_percent = 0
    #
    #         result = {'memory': memory_statistics,
    #                   'cpu': cpu_statistics,
    #                   'space': space_percent}
    #
    #         return self.finish(json_dumps(result))
    #     except Exception as e:
    #         logger.error(e)
    #         self.process_error(-1, 'fail to get system performance')


class RealTimeSystemPerformanceHandler(BaseHandler):
    REST_URL = "/system/performance/{performance_type}"

    @authenticated
    def get(self, performance_type):
        """
        get system performance metrics

        @API
        summary: get system performance metrics
        notes: get system performance metrics
        tags:
          - system
        parameters:
          -
            name: performance_type
            in: path
            required: true
            default: digest
            type: string
            description: performance type, can be freemem/totalmem/memratio/freespace/totalspace/spaceratio/digest
        produces:
          - application/json
        """
        result = None
        meminfo = psutil.virtual_memory()
        cpuinfo = psutil.cpu_percent(interval=None)
        diskinfo = psutil.disk_usage("/")
        if performance_type.lower() == "freemem":
            result = meminfo.available
        elif performance_type.lower() == "totalmem":
            result = meminfo.total
        elif performance_type.lower() == "memratio":
            result = meminfo.percent / 100.0
        elif performance_type.lower() == "cpuload":
            result = cpuinfo / 100.0
        elif performance_type.lower() == "totalspace":
            result = diskinfo.total
        elif performance_type.lower() == "freespace":
            result = diskinfo.free
        elif performance_type.lower() == "spaceratio":
            result = diskinfo.percent / 100.0
        elif performance_type.lower() == "digest":
            result = {
                "mem":
                {
                    "total": meminfo.total,
                    "free": meminfo.available,
                    "ratio": meminfo.percent / 100.0
                },
                "cpu":
                {
                    "load": cpuinfo / 100.0
                },
                "space":
                {
                    "total": diskinfo.total,
                    "free": diskinfo.free,
                    "ratio": diskinfo.percent / 100.0
                }
            }

        if result:
            response = {"status": 0, "msg": "ok", "values": [result]}
        else:
            response = {"status": -1, "msg": "error"}

        self.set_header('content-type', 'application/json')
        self.finish(json_dumps(response, self.get_arguments('pretty')))
