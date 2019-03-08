#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging, operator, json
import traceback
from traceback import print_exc

from .base import BaseHandler
from ..dao.notice_dao import NoticeDao
from nebula.dao.user_dao import authenticated
from nebula.dao import cache

from threathunter_common.util import json_dumps, millis_now
from nebula_meta.model.notice import Notice

logger = logging.getLogger('nebula.api.notice')

class NoticeBWListHandler(BaseHandler):
    REST_URL = "/platform/bwlist"

    @authenticated
    def get(self):
        """
        查询黑白名单的key(ip/phone/email)列列表
        - test: 可选值: true , false , false代表生产, true代表测试。
        - decision: 可选值: accept, reject, accept代表白名单, reject代表黑名单。
        - check_type: 可选值: ip, email, mobile, 返回key值的类型分别代表ip,  邮箱, 和手机号。
        ex. test=true&decision=reject&check_type=mobile 代表测试环境的手机黑名单
            test=false&decision=accept&check_type=ip 代表正式 环境ip白名单

        @API
        summary: get black/white ip/phone/email list
        notes: get non-expire-black-or-white-ip-or-phonenumber-or-email-list, default is black ip list
        tags:
          - platform
        parameters:
          -
            name: test
            in: query
            required: false
            type: boolean
            default: false
            description: if check in test data
          -
            name: decision
            in: query
            required: false
            type: string
            description: 'reject' for blacklist 'accept' for white list
          -
            name: check_type
            in: query
            required: false
            type: string
            description: 'ip' or 'mobile' or 'email' list to looking for
        produces:
          - application/json
        """
        iftest = self.get_argument("test", default="false")
        test = True if iftest == 'true' else False
        logger.error('%s %s' % (test, type(test)) )
        check_type = self.get_argument("check_type", default='ip')
        decision = self.get_argument("decision", default='reject')

        self.set_header('content-type', 'application/json')
        if check_type not in ('ip', 'mobile', 'email') or \
           decision not in ('reject', 'accept'):
            self.finish(json_dumps({"status": -1, "msg": "avalid query, check check_type and decision"}))
        try:
            notices = NoticeDao().white_or_black(test=test, check_type=check_type, decision=decision)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": notices}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))


class NoticeListHandler(BaseHandler):
    REST_URL = "/platform/notices"

    @authenticated
    def get(self):
        """
        Get the latest notices meet the give conditions.

        @API
        summary: get notice list
        notes: get notices that meet the given conditions
        tags:
          - platform
        parameters:
          -
            name: limit
            in: query
            required: false
            type: int
            default: 25
            description: the max number of records that should be return
          -
            name: key
            in: query
            required: false
            type: string
            description: if this value is given, it means we need all the notices on some key
          -
            name: strategy
            in: query
            required: false
            type: string
            description: filter by strategy name
          -
            name: sceneType
            in: query
            required: false
            type: string
            description: scene type filter statement, ex. login, visit
          -
            name: checkType
            in: query
            required: false
            type: string
            description: check Type filter statement, ex. ip, email, mobile
          -
            name: decision
            in: query
            required: false
            type: string
            description: decision filter statement, ex. accept, reject
          -
            name: fromtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp greater than fromtime
          -
            name: endtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp smaller than fromtime
          -
            name: filter_expire
            in: query
            required: false
            type: boolean
            description: if filter expired notices
          -
            name: offset
            in: query
            required: false
            type: long
            default: 1
            description: page number
          -
            name: test
            in: query
            required: false
            type: boolean
            description: test notice is test or production
          -
            name: tag
            in: query
            required: false
            type: string
            description: filter notice strategy tag
        produces:
          - application/json
        """

        limit = int(self.get_argument("limit", default=25))

        key = self.get_argument("key", default=None)

        fromtime = self.get_argument("fromtime", default=None)

        endtime = self.get_argument("endtime", default=None)

        strategies = self.get_arguments("strategy") # 规则命中

        scene_types = self.get_arguments("sceneType")# 规则场景 login visit

        check_types = self.get_arguments("checkType")# 名单类型 ip email mobile

        decisions = self.get_arguments("decision")# 风险类型 accept reject

        page = int(self.get_argument("offset", default=1))

        filter_expire = self.get_argument('filter_expire', default='false')
        filter_expire = True if filter_expire == 'true' else False

        test = self.get_argument('test', default=None)

        tags = self.get_arguments('tag')  # 策略风险标签
        # 根据风险标签，查询策略名
        if tags:
            if cache.Strategy_Weigh_Cache is None:
                from nebula.dao.strategy_dao import init_strategy_weigh
                init_strategy_weigh()
            strategy_weigh = filter(lambda s: list(set(tags) & (set(s['tags']))), cache.Strategy_Weigh_Cache.values())
            if not strategy_weigh:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": {'total_page': 0, 'count': 0, 'items': []}}))
                return

            strategies.extend([s['name'] for s in strategy_weigh])

        ND = NoticeDao()
        whitelists = dict(ND.get_whitelist_whole())
        not_whitelist = ('reject', 'review')

        self.set_header('content-type', 'application/json')

        result = []
        try:
            count, total, notices = ND.aggregate_notices(
                key=key, fromtime=fromtime, endtime=endtime,
                strategies=strategies, scene_types=scene_types,
                check_types=check_types, decisions=decisions,
                filter_expire=filter_expire, page=page, limit=limit, test=test
            )

            # 如果黑灰名单对应在白名单中，标识并贴上白名单信息
            for rd in notices:
                if whitelists.has_key((rd['key'], rd['check_type'], rd['test'])):
                    rd['key_in_whitelist'] = True
                    rd['whitelist'] = whitelists.get((rd.key, rd.check_type, rd.test))

                result.append(rd)

            self.finish(json_dumps({"status": 0, "msg": "ok", "values": {'total_page': total, 'count': count, 'items': result}}))
        except Exception:
            logger.error(traceback.format_exc())
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    @authenticated
    def delete(self):
        """
        Remove notices that meet given conditions.

        @API
        summary: delete notices
        notes: Remove notices that meet given conditions.
        tags:
          - platform
        parameters:
          -
            name: key
            in: query
            required: false
            type: string
            description: if this value is given, it means we need all the notices on some key
          -
            name: fromtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp greater than fromtime
          -
            name: endtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp smaller than fromtime
        produces:
          - application/json
        """

        key = self.get_argument("key", default=None)
        fromtime = self.get_argument("fromtime", default=None)
        endtime = self.get_argument("endtime", default=None)

        # 如果三个参数都为空,则不进行操作,避免删除所有风险名单
        if not (key or fromtime or endtime):
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))

        self.set_header('content-type', 'application/json')
        try:
            NoticeDao().remove_notices(key=key, fromtime=fromtime, endtime=endtime)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to delete data in database"}))

    @authenticated
    def post(self):
        """
        add a list of new notice items

        @API
        summary: add a list of new notice items
        notes: add a list of new notice items
        tags:
          - platform
        parameters:
          -
            name: notices
            in: body
            required: true
            type: json
            description: the list of the notice json item
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            notices = [Notice.from_dict(_) for _ in json.loads(body)]
        except Exception as error:
            return self.process_error(400, "invalid request body: {}".format(error.message))

        try:
            dao = NoticeDao()
            for n in notices:
                dao.add_notice(n)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as error:
            return self.process_error(500, "fail to add notice to database: {}".format(error.message))


class NoticeTimestampListHandler(BaseHandler):
    REST_URL = "/platform/noticetimestamps"

    def get(self):
        """
        Get the latest notices meet the give conditions, and this handler only returns timestamp instead of full
        information.

        @API
        summary: get notice list with only timestamp information
        notes: get notices that meet the given conditions
        tags:
          - platform
        parameters:
          -
            name: limit
            in: query
            required: false
            type: int
            default: 10
            description: the max number of records that should be return
          -
            name: key
            in: query
            required: false
            type: string
            description: if this value is given, it means we need all the notices on some key
          -
            name: fromtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp greater than fromtime
          -
            name: endtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp smaller than fromtime
        produces:
          - application/json
        """

        limit = self.get_argument("limit", default=None)
        key = self.get_argument("key", default=None)
        fromtime = self.get_argument("fromtime", default=None)
        endtime = self.get_argument("endtime", default=None)

        self.set_header('content-type', 'application/json')
        try:
            notices = NoticeDao().list_notices(key=key, limit=limit, fromtime=fromtime, endtime=endtime)
            notices = notices or []
            notices = [_.get_dict() for _ in notices]
            notices = [{"timestamp": _["timestamp"]} for _ in notices]
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": notices}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))


last_query_timestamp = 0
cached_stats = dict()
def get_notice_stats(duration=3600):
    global last_query_timestamp, cached_stats

    current = millis_now()
    # 30s 之内的请求使用缓存
    if current - last_query_timestamp < 30 * 1000:
        return cached_stats

    fromtime = current - duration * 1000
    endtime = current
    notices = NoticeDao().list_notices(key=None, limit=None, fromtime=fromtime, endtime=endtime)

    counts = {
        "http": {},
        "account": {},
        "fraud": {},
        "other": {}
    }

    for n in notices:
        city = n.geo_city
        if not city:
            city = "unknown"
        scene_name = n.scene_name

        count_dict = counts["other"]
        if scene_name == 'visit':
            count_dict = counts['http']
        elif scene_name == 'order':
            count_dict = counts['fraud']
        elif scene_name in {"login", "regist"}:
            count_dict = counts['account']

        count_dict.setdefault(city, 0)
        count_dict[city] = (count_dict[city] + 1)

    for k in counts.keys():
        sorted_list = sorted(counts[k].items(), key=operator.itemgetter(1))
        sorted_list = filter(lambda x: x[0], sorted_list)
        sorted_list = sorted_list[::-1][:10]
        counts[k] = [{"name": city_name, "value": count} for city_name, count in sorted_list]

    stats = {
        "http_attack_top": counts["http"],
        "account_attack_top": counts["account"],
        "fraud_attack_top": counts["fraud"],
        "other_attack_top": counts["other"],
    }

    cached_stats = stats
    last_query_timestamp = current
    return cached_stats


class NoticeStatsHandler(BaseHandler):
    REST_URL = "/platform/noticestats"

    @authenticated
    def get(self):
        """
        Get top 10 cities notice stats

        @API
        summary: Get top 10 cities notice stats
        notes: get top 10 cities with more notices than others
        tags:
          - platform
        parameters:
          -
            name: duration
            in: query
            required: false
            type: long
            default: 3600
            description: the result notices should have timestamp in the past duration
        produces:
          - application/json
        """

        duration = self.get_argument("duration", default=3600)
        duration = int(duration)
        self.set_header('content-type', 'application/json')
        self.finish(json_dumps(get_notice_stats(duration)))
        return


class NoticeExportHandler(BaseHandler):

    @authenticated
    def get(self):
        """
        export the notices into xls file

        @API
        summary: export notice
        notes: export notices into xls file
        tags:
          - platform
        parameters:
          -
            name: key
            in: query
            required: false
            type: string
            description: if this value is given, it means we need all the notices on some key
          -
            name: strategy
            in: query
            required: false
            type: string
            description: filter by strategy name
          -
            name: sceneType
            in: query
            required: false
            type: string
            description: scene type filter statement, ex. login, visit
          -
            name: checkType
            in: query
            required: false
            type: string
            description: check Type filter statement, ex. ip, email, mobile
          -
            name: decision
            in: query
            required: false
            type: string
            description: decision filter statement, ex. accept, reject
          -
            name: fromtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp greater than fromtime
          -
            name: endtime
            in: query
            required: false
            type: long
            description: the result notices should have timestamp smaller than fromtime
          -
            name: test
            in: query
            required: false
            type: string
            description: test notice is test or production
        produces:
          - application/msexcel
        """
        # 获取报警数据
        key = self.get_argument("key", default=None)
        fromtime = self.get_argument("fromtime", default=None)
        endtime = self.get_argument("endtime", default=None)
        strategies = self.get_arguments("strategy") # 规则命中
        scene_types = self.get_arguments("sceneType")# 规则场景 login visit
        check_types = self.get_arguments("checkType")# 名单类型 ip email mobile
        decisions = self.get_arguments("decision")# 风险类型 accept reject
        test = self.get_argument('test', default=None)
        if fromtime:
            fromtime = int(fromtime)
        if endtime:
            endtime = int(endtime)
        if test == "true":
            test = 1
        elif test == "false":
            test = 0
        else:
            test = None

        if not fromtime and not endtime:
            # 默认取昨天的数据
            now = millis_now() / 1000
            start_of_day = (now + 8 * 3600) / 86400 * 86400 - 8 * 3600
            fromtime = (start_of_day - 86400) * 1000
            endtime = start_of_day * 1000

        ND = NoticeDao()
        try:
            _, _, notices = ND.get_notices(
                key=key, fromtime=fromtime, endtime=endtime, strategies=strategies, scene_types=scene_types,
                check_types=check_types, decisions=decisions, is_checking=False, test=test, limit=100000
            )

            # 写excel文件
            import xlwt
            import datetime
            f = xlwt.Workbook()
            sheet1 = f.add_sheet(u'报警列表', cell_overwrite_ok=True)

            headers = [u'命中时间', u'值类型', u'风险值', u'风险决策', u'策略名称', u'风险场景', u'子场景', u'过期时间', u'测试状态',
                       u'风险分值', u'省', u'市', u'关联页面', u'风险备注']
            widths = [20, 10, 15, 10, 20, 10, 10, 20, 10, 5, 10, 10, 50, 50]
            # 生成第一行
            for i in range(0, len(headers)):
                sheet1.write(0, i, headers[i])
                sheet1.col(i).width = widths[i] * 256

            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'yyyy/MM/dd HH:mm:ss'
            for lineno, n in enumerate(notices):
                row = lineno + 1
                sheet1.write(row, 0, datetime.datetime.fromtimestamp(n.timestamp/1000), date_format)
                sheet1.write(row, 1, n.check_type)
                sheet1.write(row, 2, n.key)
                sheet1.write(row, 3, n.decision)
                sheet1.write(row, 4, n.strategy_name)
                sheet1.write(row, 5, n.scene_name)
                sheet1.write(row, 6, n.checkpoints)
                sheet1.write(row, 7, datetime.datetime.fromtimestamp(n.expire/1000), date_format)
                sheet1.write(row, 8, n.test)
                sheet1.write(row, 9, n.risk_score)
                sheet1.write(row, 10, n.geo_province)
                sheet1.write(row, 11, n.geo_city)
                sheet1.write(row, 12, n.uri_stem)
                sheet1.write(row, 13, n.remark)

            filename = datetime.datetime.fromtimestamp(fromtime/1000).strftime("%Y%m%d") + ".xls"

            self.set_header('Content-Type', 'application/msexcel')
            self.set_header('Content-Disposition', 'attachment; filename='+filename)
            f.save(self) #保存文件
        except Exception as err:
            print_exc()
            logger.error(err)
            self.set_header('content-type', 'application/json')
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))


class TriggerEventHandler(BaseHandler):
    REST_URL = "/platform/notices/trigger_event"

    @authenticated
    def get(self):
        """
        查询风险名单触发事件详情

        @API
        summary: get all trigger events
        tags:
          - platform
        parameters:
          - name: key
            in: query
            required: true
            type: string
            description: notice key包含的字符串
          - name: strategy
            in: query
            required: true
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
            required: false
            type: timestamp
            description: notice报警时间应大于等于fromtime
          - name: endtime
            in: query
            required: false
            type: timestamp
            description: notice报警时间应小于等于endtime
          - name: filter_expire
            in: query
            required: false
            type: boolean
            description: notice是否过期
          - name: test
            in: query
            required: false
            type: boolean
            description: notice是否是测试名单
        """

        key = self.get_argument("key")

        strategy = self.get_argument("strategy")

        fromtime = self.get_argument("fromtime", default=None)

        endtime = self.get_argument("endtime", default=None)

        scene_types = self.get_arguments("sceneType")

        check_types = self.get_arguments("checkType")

        decisions = self.get_arguments("decision")

        filter_expire = self.get_argument('filter_expire', default='false')
        filter_expire = True if filter_expire == 'true' else False

        test = self.get_argument('test', default=None)

        self.set_header('content-type', 'application/json')

        try:
            notice_dao = NoticeDao()
            trigger_events = notice_dao.get_trigger_events(
                key=key, strategy=strategy, fromtime=fromtime, endtime=endtime,
                scene_types=scene_types, check_types=check_types, decisions=decisions,
                filter_expire=filter_expire, test=test
            )

            self.finish(json_dumps({"status": 200, "msg": "ok", "values": trigger_events}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))
