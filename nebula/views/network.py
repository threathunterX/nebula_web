#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from threathunter_common.util import millis_now, json_dumps
from threathunter_common.metrics.metricsagent import MetricsAgent

from nebula.dao.user_dao import authenticated

from .base import BaseHandler

logger = logging.getLogger('nebula.api.network')

minute = 60 * 1000
hour = 60 * minute


class NetworkStatisticsHandler(BaseHandler):

    REST_URL = '/platform/network/statistics'

    @authenticated
    def get(self):
        """
        Get the all the http count
        @API
        summary: all the http count
        notes: Get all the http count
        tags:
          - platform
        produces:
          - application/json
        """

        interval = 5 * minute
        now = millis_now()
        endtime = now - (now % interval)
        fromtime = endtime - hour
        try:
            network_statistics = MetricsAgent.get_instance().query(
                'nebula.online', 'events.income.count', 'sum', fromtime, endtime, interval)
        except Exception as e:
            logger.error(e)
            self.process_error(-1, 'fail to get metrics')

        # 按照时间戳顺序解析network statistics结果
        statistics_timeframe = network_statistics.keys()
        network_list = list()
        try:
            for time_frame in range(fromtime, endtime, interval):
                network = dict(time_frame=time_frame, count=0)

                if time_frame in statistics_timeframe:
                    ts_data = network_statistics[time_frame]
                    for legend, value in ts_data.iteritems():
                        network['count'] = int(value)

                network_list.append(network)

            self.finish(json_dumps(network_list))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, 'fail to get network statistics')
