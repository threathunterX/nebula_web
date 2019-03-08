#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import threading
from tornado import gen
import tornado_mysql

from nebula.models.engine import tornado_mysql_config
from nebula.dao.user_dao import authenticated
from nebula.dao import cache
from nebula.views.base import BaseHandler

logger = logging.getLogger('nebula.api.notice_report')

mutex = threading.Lock()

CONDITIONS_QUERY = 'timestamp >= %s AND timestamp <= %s'
# 风险名单趋势
RISK_TREND_QUERY = 'SELECT `tsHour`, sum(`count`) FROM notice_stat WHERE %s GROUP BY `tsHour`'
# 风险类型分布SQL
RISK_TAG_TOP_QUERY = 'SELECT tag, sum(`count`) FROM notice_stat WHERE tag != "" AND %s GROUP BY tag ORDER BY sum(`count`) DESC'
# 风险账号相关SQL
RISK_DISCOVER_USER_QUERY = 'SELECT count(DISTINCT `key`) FROM notice_stat WHERE check_type = "USER" AND %s'
RISK_BLOCK_USER_QUERY = 'SELECT count(DISTINCT `key`) FROM notice_stat WHERE check_type = "USER" AND test = FALSE AND %s'
RISK_USER_TOP_QUERY = 'SELECT `key`, tag, sum(`count`), `tsHour` FROM notice_stat WHERE check_type = "USER" AND %s AND `key` IN (SELECT t.`key` FROM (SELECT `key` FROM notice_stat WHERE check_type = "USER" AND %s GROUP BY `key` ORDER BY sum(`count`) DESC LIMIT 10) AS t) GROUP BY `key`, tag, `tsHour`'
# 风险IP相关SQL
RISK_DISCOVER_IP_QUERY = 'SELECT count(DISTINCT `key`) FROM notice_stat WHERE check_type = "IP" AND %s'
RISK_BLOCK_IP_QUERY = 'SELECT count(DISTINCT `key`) FROM notice_stat WHERE check_type = "IP" AND test = FALSE AND %s'
RISK_IP_TOP_QUERY = 'SELECT `key`, geo_city, tag, sum(`count`), `tsHour` FROM notice_stat WHERE check_type = "IP" AND %s AND `key` IN (SELECT t.`key` FROM (SELECT `key` FROM notice_stat WHERE check_type = "IP" AND %s GROUP BY `key` ORDER BY sum(`count`) DESC LIMIT 10)AS t) GROUP BY `key`, geo_city, tag, `tsHour`'
RISK_GEO_TOP_QUERY = 'SELECT geo_city, sum(`count`) FROM notice_stat WHERE check_type = "IP" AND %s GROUP BY geo_city ORDER BY sum(`count`) DESC LIMIT 8'
RISK_URL_TOP_QUERY = 'SELECT uri_stem, sum(`count`), `tsHour` FROM notice_stat WHERE check_type = "IP" AND %s AND `uri_stem` IN (SELECT t.`uri_stem` FROM (SELECT `uri_stem` FROM notice_stat WHERE check_type = "IP" AND %s GROUP BY `uri_stem` ORDER BY sum(`count`) DESC LIMIT 10)AS t) GROUP BY uri_stem, `tsHour`'

notice_report = {}


def set_notice_report_value(key, value=None):
    with mutex:
        notice_report[key] = value


def risk_trend_callcack(cursor, *args):
    # 风险名单趋势，没有数据的补0
    trend_ts = args[0]
    risk_trend_tmp = {}
    for r in cursor:
        timestamp, count = r
        risk_trend_tmp[timestamp] = int(count)

    set_notice_report_value(
        'risk_trend', [{ts: risk_trend_tmp.get(ts, 0)} for ts in trend_ts])


def risk_tag_top_callback(cursor, *args):
    # 查询风险类型分布，只取排名前五，其余tag总和为其他标签
    risk_tag_top = [{tag: int(count)} for tag, count in cursor[:5]]
    other_tag_count = sum([int(count) for _, count in cursor[5:]])
    if other_tag_count > 0:
        risk_tag_top.append({u'其他': other_tag_count})

    set_notice_report_value('risk_tag_top', risk_tag_top)


def risk_discover_user_callback(cursor, *args):
    # 查询风险账号总数
    for _ in cursor:
        user_count = int(_[0])
    set_notice_report_value('risk_discover_stat_user', user_count)


def risk_block_user_callback(cursor, *args):
    # 查询拦截风险账号总数，拦截账号为test为FALSE
    for _ in cursor:
        user_count = int(_[0])
    set_notice_report_value('risk_block_stat_user', user_count)


def risk_user_top_callback(cursor, *args):
    # 查询风险账号TOP 10相关数据
    risk_user_top = []
    trend_ts = args[0]
    last_key = None
    for _ in cursor:
        key, tag, count, timestamp = _
        if key == last_key:
            risk_user_top[-1]['type'][tag] = risk_user_top[-1][
                'type'].get(tag, 0) + int(count)
            risk_user_top[-1]['trend'][timestamp] = risk_user_top[-1][
                'trend'].get(timestamp, 0) + int(count)
            risk_user_top[-1]['count'] += int(count)
        else:
            last_key = key
            last_user = {
                'name': key,
                'trend': {timestamp: int(count)},
                'type': {tag: int(count)},
                'count': int(count)
            }
            risk_user_top.append(last_user)

    risk_user_top = sorted(risk_user_top, key=lambda _: _[
                           'count'], reverse=True)
    for user in risk_user_top:
        user['trend'] = [{ts: user['trend'].get(ts, 0)} for ts in trend_ts]

    set_notice_report_value('risk_user_top', risk_user_top)


def risk_ip_top_callback(cursor, *args):
    # 查询风险IP top 10相关数据
    risk_ip_top = []
    trend_ts = args[0]
    last_key = ''
    for _ in cursor:
        key, geo_city, tag, count, timestamp = _
        if key == last_key:
            risk_ip_top[-1]['type'][tag] = risk_ip_top[-1][
                'type'].get(tag, 0) + int(count)
            risk_ip_top[-1]['trend'][timestamp] = risk_ip_top[-1][
                'trend'].get(timestamp, 0) + int(count)
            risk_ip_top[-1]['count'] += int(count)
        else:
            last_key = key
            last_ip = {
                'name': key,
                'trend': {timestamp: int(count)},
                'type': {tag: int(count)},
                'geo_city': geo_city,
                'count': int(count)
            }
            risk_ip_top.append(last_ip)

    risk_ip_top = sorted(risk_ip_top, key=lambda _: _['count'], reverse=True)
    for ip in risk_ip_top:
        ip['trend'] = [{ts: ip['trend'].get(ts, 0)} for ts in trend_ts]

    set_notice_report_value('risk_ip_top', risk_ip_top)


def risk_discover_ip_callback(cursor, *args):
    # 查询风险IP总数
    for _ in cursor:
        ip_count = int(_[0])
    set_notice_report_value('risk_discover_stat_ip', ip_count)


def risk_block_ip_callback(cursor, *args):
    # 查询拦截风险IP总数，拦截IP为test为FALSE
    for _ in cursor:
        ip_count = int(_[0])
    set_notice_report_value('risk_block_stat_ip', ip_count)


def risk_geo_top_callback(cursor, *args):
    # 风险IP地理位置
    risk_geo_top = []
    for _ in cursor:
        city, count = _
        risk_geo_top.append({city: int(count)})
    set_notice_report_value('risk_geo_top', risk_geo_top)


def risk_url_top_callback(cursor, *args):
    # 风险IP访问主要URL TOP10
    trend_ts = args[0]
    risk_url_top = []
    last_uri_stem = None
    for _ in cursor:
        uri_stem, count, timestamp = _
        if uri_stem == last_uri_stem:
            risk_url_top[-1]['trend'][timestamp] = int(count)
            risk_url_top[-1]['count'] += int(count)
        else:
            last_uri_stem = uri_stem
            last_uri = {
                'name': uri_stem,
                'trend': {timestamp: int(count)},
                'count': int(count)
            }
            risk_url_top.append(last_uri)

    risk_url_top = sorted(risk_url_top, key=lambda _: _['count'], reverse=True)
    for url in risk_url_top:
        url['trend'] = [{ts: url['trend'].get(ts, 0)} for ts in trend_ts]

    set_notice_report_value('risk_url_top', risk_url_top)


class NoticeReportHandler(BaseHandler):

    REST_URL = '/platform/stats/notice_report'

    @gen.coroutine
    @authenticated
    def get(self):
        """
        @API
        summary: 风险名单报表数据接口
        tags:
          - platform
        parameters:
          - name: key
            in: query
            required: false
            type: string
            description: notice key包含的字符串
          - name: strategy
            in: query
            required: false
            type: string
            description: notice命中的策略，支持多个策略名字
          - name: sceneType
            in: query
            required: false
            type: string
            description: notice命中的场景，支持多个场景
          - name: checkType
            in: query
            required: false
            type: string
            description: notice类型，支持多个类型
          - name: decision
            in: query
            required: false
            type: string
            description: notice操作建议类型，支持多个操作
          - name: fromtime
            in: query
            required: true
            type: timestamp
            description: notice报警时间应大于等于fromtime
          - name: endtime
            in: query
            required: true
            type: timestamp
            description: notice报警时间应小于等于endtime
          - name: test
            in: query
            required: false
            type: boolean
            description: notice是否是测试名单
          - name: tag
            in: query
            required: false
            type: string
            description: filter notice strategy tag
        produces:
          - application/json
        """
        key = self.get_argument('key', default=None)
        fromtime = self.get_argument('fromtime', default=None)
        endtime = self.get_argument('endtime', default=None)
        strategies = self.get_arguments('strategy')
        scene_types = self.get_arguments('sceneType')
        check_types = self.get_arguments('checkType')
        decisions = self.get_arguments('decision')
        test = self.get_argument('test', default=None)
        tags = self.get_arguments('tag')  # 策略风险标签

        self.set_header('content-type', 'application/json')
        if not fromtime or not endtime:
            self.process_error(-1, '缺少fromtime或endtime参数')
            return

        # 初始化查询条件子句
        hour = 3600000
        fromtime = int(fromtime) / 1000 / 3600 * hour
        endtime = int(endtime) / 1000 / 3600 * hour
        # 避免时间fromtime 12:00:00和endtime12:59:59经过处理后全部被同步成12:00:00
        # 所以对endtime进行处理，保证最少返回from time开始后一个小时数据
        if fromtime == endtime:
            endtime = fromtime + hour

        trend_ts = [ts for ts in range(fromtime, endtime + hour, hour)]
        conditions_query = CONDITIONS_QUERY % (fromtime, endtime)

        if key:
            conditions_query = conditions_query + ' AND ' + '`key` = "%s"' % key

        if tags:
            # 根据风险标签，查询策略名
            if cache.Strategy_Weigh_Cache is None:
                from nebula.dao.strategy_dao import init_strategy_weigh
                init_strategy_weigh()

            strategy_weigh = filter(lambda s: list(set(tags) & (
                set(s['tags']))), cache.Strategy_Weigh_Cache.values())
            strategies.extend([s['name'] for s in strategy_weigh])

        if strategies:
            conditions_query = conditions_query + ' AND ' + \
                "strategy_name IN (%s)" % ','.join(
                    ['"%s"' % _ for _ in strategies])

        if scene_types:
            conditions_query = conditions_query + ' AND ' + \
                'scene_name IN (%s)' % ','.join(
                    ['"%s"' % _ for _ in scene_types])

        if check_types:
            conditions_query = conditions_query + ' AND ' + \
                'check_type IN (%s)' % ','.join(
                    ['"%s"' % _ for _ in check_types])

        if decisions:
            conditions_query = conditions_query + ' AND ' + \
                'decision IN (%s)' % ','.join(['"%s"' % _ for _ in decisions])

        if test is not None:
            test = 'TRUE' if test.lower() == 'true' else 'FALSE'
            conditions_query = conditions_query + ' AND ' + 'test = %s' % test

        try:
            # 初始化数据库连接
            conn = yield tornado_mysql.connect(**tornado_mysql_config)
            cursor = conn.cursor()
            sql_list = list()
            callback_list = list()

            # 查询风险名单趋势
            sql_list.append(RISK_TREND_QUERY % conditions_query)
            callback_list.append(risk_trend_callcack)

            # 查询风险类型分布
            sql_list.append(RISK_TAG_TOP_QUERY % conditions_query)
            callback_list.append(risk_tag_top_callback)

            # 查询风险账号相关数据
            if check_types and 'USER' not in check_types:
                set_notice_report_value('risk_discover_stat_user', 0)
                set_notice_report_value('risk_block_stat_user', 0)
                set_notice_report_value('risk_user_top', 0)
            else:
                # 查询风险账号总数
                sql_list.append(RISK_DISCOVER_USER_QUERY % conditions_query)
                callback_list.append(risk_discover_user_callback)

                # 查询拦截风险账号总数
                if test == 'TRUE':
                    set_notice_report_value('risk_block_stat_user', 0)
                else:
                    sql_list.append(RISK_BLOCK_USER_QUERY % conditions_query)
                    callback_list.append(risk_block_user_callback)

                # 查询风险账号TOP 10
                sql_list.append(RISK_USER_TOP_QUERY %
                                (conditions_query, conditions_query))
                callback_list.append(risk_user_top_callback)

            # 查询风险IP相关数据
            if check_types and 'IP' not in check_types:
                set_notice_report_value('risk_discover_stat_ip', 0)
                set_notice_report_value('risk_block_stat_ip', 0)
                set_notice_report_value('risk_ip_top', [])
                set_notice_report_value('risk_geo_top', [])
                set_notice_report_value('risk_url_top', [])
            else:
                # 查询风险IP总数
                sql_list.append(RISK_DISCOVER_IP_QUERY % conditions_query)
                callback_list.append(risk_discover_ip_callback)

                # 查询拦截风险IP总数
                if test == 'TRUE':
                    set_notice_report_value('risk_block_stat_ip', 0)
                else:
                    sql_list.append(RISK_BLOCK_IP_QUERY % conditions_query)
                    callback_list.append(risk_block_ip_callback)

                # 查询风险IP top 10
                sql_list.append(RISK_IP_TOP_QUERY %
                                (conditions_query, conditions_query))
                callback_list.append(risk_ip_top_callback)

                # 风险IP地理位置
                sql_list.append(RISK_GEO_TOP_QUERY % conditions_query)
                callback_list.append(risk_geo_top_callback)

                # 风险IP访问主要URL TOP10
                sql_list.append(RISK_URL_TOP_QUERY %
                                (conditions_query, conditions_query))
                callback_list.append(risk_url_top_callback)

            # 数据库执行查询语句
            sql_statements = ';'.join(sql_list)
            yield cursor.execute(sql_statements)

            # 将查询结果的callback方法，多线程处理
            threads = []
            for callback in callback_list:
                t = threading.Thread(
                    target=callback, args=(cursor.fetchall(), trend_ts))
                threads.append(t)
                yield cursor.nextset()

            for t in threads:
                t.setDaemon(True)
                t.start()
            t.join()
            cursor.close()
            conn.close()

            # 返回多线程处理结束后的结果
            self.finish(json.dumps(
                {'status': 200, 'msg': 'ok', 'values': notice_report}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '报表生成失败，请重新查询')
