#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, time
import tornado_mysql
from tornado import gen

from threathunter_common.util import json_dumps, millis_now
from threathunter_common.metrics.metricsagent import MetricsAgent

from nebula.models.engine import tornado_mysql_config
from nebula.dao import cache
from nebula.dao.user_dao import authenticated
from .base import BaseHandler
from nebula.dao.notice_dao import NoticeDao
from common import utils
import settings


logger = logging.getLogger('nebula.api.alarm')
DEBUG_PREFIX = '==============='

hour = 60 * 60 * 1000
URL_QUERY = 'SELECT uri_stem, count(uri_stem) FROM notice WHERE timestamp >= %s AND timestamp <= %s GROUP BY uri_stem ORDER BY count(uri_stem);'
LOCATION_QUERY = 'SELECT geo_city, count(geo_city) FROM notice WHERE timestamp >= %s AND timestamp <= %s GROUP BY geo_city ORDER BY count(geo_city);'
STRATEGY_QUERY = 'SELECT strategy_name, test, remark, count(strategy_name) FROM notice WHERE timestamp >= %s AND timestamp <= %s GROUP BY strategy_name, test ORDER BY count(strategy_name);'

class TagStatHandler(BaseHandler):

    REST_URL = '/platform/behavior/tag_statistics'

    @authenticated
    def get(self):
        """
        获取当前小时tags的统计

        @API
        summary: 获取当前小时tags的统计
        description: ''
        tags:
          - platform
        """
        tag_statistics = []
        temp_statistics = {}
        try:
            # 查询风险名单数据库,统计命中策略变量
            from_time = utils.get_hour_start() * 1000
            end_time = millis_now()
            ret = NoticeDao().get_statistic_scene(from_time, end_time)

            # 根据命中策略查询策略包含的tags,并统计命中每一个tag的数量
            strategy_weigh = cache.Strategy_Weigh_Cache
            for strategy, count in ret:
                tags = strategy_weigh.get(strategy, {}).get('tags', [])
                for tag in tags:
                    utils.dict_merge(temp_statistics, {tag: count})

            # tags根据命中数量排序
            sorted_tags = sorted(temp_statistics.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)[:10]
            tag_statistics = [{'name': tag, 'count': count} for tag, count in sorted_tags]
            self.finish(json_dumps(tag_statistics))
        except Exception as e:
            logger.error(e)
            self.finish(json_dumps(tag_statistics))

class AlarmListHandler(BaseHandler):

    REST_URL = '/platform/alarm'

    @authenticated
    def get(self):
        """
        Get the alarms meet the give conditions

        @API
        summary: get alarm list
        notes: Get the alarms meet the give conditions
        tags:
          - platform
        parameters:
          -
            name: fromtime
            in: query
            required: true
            type: integer
            description: start time
          -
            name: endtime
            in: query
            required: true
            type: integer
            description: end time
          -
            name: page
            in: query
            required: true
            type: integer
            description: the which page of alarm list
          -
            name: size
            in: query
            required: true
            type: integer
            description: the size of one alarm page
          -
            name: query
            in: query
            required: false
            type: string
            description: query
        produces:
          - application/json
        """

        fromtime = int(self.get_argument('fromtime', 0))
        endtime = int(self.get_argument('endtime', 0))
        page = int(self.get_argument('page', 0))
        size = int(self.get_argument('size', 0))
        query = self.get_argument('query', '')

        try:
            notice_dao = NoticeDao()
            count, total_page, notice_list = notice_dao.page_notices(
                fromtime, endtime, page, size, query)
            data = [
                dict(
                    timestamp=_.timestamp,
                    geo_city=_.geo_city,
                    geo_province=_.geo_province,
                    test=_.test,
                    whitelist=True if _.decision == 'accept' else False,
                    url=_.uri_stem,
                    expire=_.expire,
                    key=_.key,
                    tip=_.tip,
                    strategy_name=_.strategy_name,
                    scene_name=_.scene_name
                ) for _ in notice_list]

            self.finish(json_dumps(
                {'total': count, 'total_page': total_page, 'data': data}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, 'fail to get notice')


class ValidCountHandler(BaseHandler):

    REST_URL = '/platform/alarm/valid_count'

    @authenticated
    def get(self):
        """
        Get the valid alarm count

        @API
        summary: valid alarm count
        notes: Get the valid alarm count
        tags:
          - platform
        produces:
          - application/json
        """

        # 查询redis metrics有效报警数量
        try:
            notice_dao = NoticeDao()
            valid_counts = {decision: count for decision,
                            count in notice_dao.get_valid_notices()}
            valid_alarms = {'incident_list': valid_counts.get('review', 0) + valid_counts.get('reject', 0), 'white_list': valid_counts.get('accept', 0)}
            self.finish(json_dumps(valid_alarms))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, 'fail to get valid alarms')


class StatisticsHandler(BaseHandler):

    # TODO the logic could be wrong
    REST_URL = '/platform/alarm/statistics'

    @authenticated
    def get(self):
        """
        Get the alarm statistics for the specified period of time

        @API
        summary: alarm statistics
        notes: Get the alarm statistics for the specified period of time
        tags:
          - platform
        parameters:
          -
            name: fromtime
            in: query
            required: true
            type: integer
            description: start time
          -
            name: endtime
            in: query
            required: true
            type: integer
            description: end time
        produces:
          - application/json
        """

        fromtime = int(self.get_argument('fromtime', 0))
        endtime = int(self.get_argument('endtime', 0))
        statistics_result = None

        try:
            notice_dao = NoticeDao()
            # 查询生产数据
            production_counts = notice_dao.get_statistic_count(
                fromtime, endtime, 0)
            production_counts_map = {int(ts): int(count)
                                     for ts, count in production_counts}
            # 查询测试数据
            test_counts = notice_dao.get_statistic_count(fromtime, endtime, 1)
            test_counts_map = {int(ts): int(count)
                               for ts, count in test_counts}

            # 按照时间戳顺序解析alarm结果
            alarm_statistics = [{'production_count': production_counts_map.get(ts, 0), 'test_count': test_counts_map.get(ts, 0), 'time_frame': ts} for ts in range(
                fromtime, endtime, 3600000)]
            self.finish(json_dumps(alarm_statistics))

        except Exception as e:
            logger.error(e)
            self.process_error(-1, 'fail to get metrics')


class StatisticsDetailHandler(BaseHandler):

    REST_URL = '/platform/alarm/statistics_detail'

    @gen.coroutine
    @authenticated
    def get(self):
        """
        Get the assorted alarm statistics detail for the specified period of time

        @API
        summary: alarm statistics detail
        notes: Get the assorted alarm statistics detail for the specified period of time
        tags:
          - platform
        parameters:
          -
            name: fromtime
            in: query
            required: true
            type: integer
            description: start time
          -
            name: endtime
            in: query
            required: true
            type: integer
            description: end time
        produces:
          - application/json
        """

        fromtime = int(self.get_argument('fromtime', 0))
        endtime = int(self.get_argument('endtime', 0))
        url_query = URL_QUERY % (fromtime, endtime)
        location_query = LOCATION_QUERY % (fromtime, endtime)
        strategy_query = STRATEGY_QUERY % (fromtime, endtime)
        sql = url_query + location_query + strategy_query
        alarm_statistics = {'url': [], 'location': [], 'strategy': []}
        now_in_hour_start = utils.get_hour_start() * 100
        # @todo
        logger.debug("fromtime: %s(%s), current_hour_start:%s(%s), current hour query is enable?(%s)" % (fromtime, type(fromtime), now_in_hour_start, type(now_in_hour_start), settings.Enable_Online))
        if fromtime >= now_in_hour_start and not settings.Enable_Online:
            self.finish(json_dumps(alarm_statistics))
            return
        try:

            # 初始化数据库连接
            conn = yield tornado_mysql.connect(**tornado_mysql_config)
            cursor = conn.cursor()
            yield cursor.execute(url_query)

            # 解析URL查询结果
            for r in cursor.fetchall():
                url, count = r
                alarm_statistics['url'].append({'value': url, 'count': count})

            yield cursor.execute(location_query)

            # 解析location查询结果
            for r in cursor.fetchall():
                location, count = r
                alarm_statistics['location'].append(
                    {'value': location, 'count': count})
                
            yield cursor.execute(strategy_query)

            # 解析strategy查询结果
            for r in cursor.fetchall():
                strategy, test, remark, count = r
                alarm_statistics['strategy'].append(
                    {'value': strategy, 'test': bool(test), 'remark': remark, 'count': count})

            self.finish(json_dumps(alarm_statistics))
        except Exception:
            import traceback
            logger.error("Home page URL, location, Strategy fetch Error: %s" % traceback.format_exc())
            self.process_error(-1, 'fail to get notices')
