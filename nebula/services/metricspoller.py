#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import gevent
import psutil

from threathunter_common.metrics.metricsagent import MetricsAgent
from threathunter_common.util import millis_now

logger = logging.getLogger('nebula.services.metrics')


class HistoryMetricsPoller(object):
    def __init__(self):
        self._task = None

    def _run(self):
        while True:
            try:
                diskinfo = psutil.disk_usage("/")
                cpuinfo = psutil.cpu_percent(interval=None)
                meminfo = psutil.virtual_memory()

                metrics = {
                    "totalmem": meminfo.total,
                    "freemem": meminfo.available,
                    "memratio": meminfo.percent,
                    "totalspace": diskinfo.total,
                    "freespace": diskinfo.free,
                    "spaceratio": diskinfo.percent,
                    "cpuload": cpuinfo
                }

                current = millis_now()
                # align current to 5 second
                current = (current+4999)/5000*5000

                for name, data in metrics.iteritems():
                    db = "default"
                    metrics_name = "system.{}".format(name)
                    MetricsAgent.get_instance().add_metrics(db, metrics_name, {}, data, 3600 * 24 * 7)
                gevent.sleep(5) # @todo
            except Exception as error:
                logger.error(error)

    def start(self):
        self._task = gevent.spawn(self._run) # # @todo

    def stop(self):
        if self._task:
            self._task.kill()
            self._task.stop()

    def close(self):
        self.stop()

    def __del__(self):
        self.stop()
