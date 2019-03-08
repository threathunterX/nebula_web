#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging, operator, json

from .base import BaseHandler
#from nebula.middleware.tornado_rest_swagger.restutil import rest_class, rest_method
from ..dao.notice_dao import NoticeDao
from nebula.dao.user_dao import authenticated

from threathunter_common.util import json_dumps, millis_now
from nebula_meta.model.notice import Notice

logger = logging.getLogger('nebula.api.notice_default')

#没有注册到路由中. 实际是没用的.

class NoticeListHandler(BaseHandler):
    REST_URL = "/default/notices" 

    @authenticated
    def get(self):
        """
        Get the latest notices meet the give conditions.

        @API
        summary: get notice list 
        notes: get notices that meet the given conditions
        tags:
          - default
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
        produces:
          - application/json        
        """

        limit = self.get_argument("limit", default=None)
        key = self.get_argument("key", default=None)
        fromtime = self.get_argument("fromtime", default=None)
        endtime = self.get_argument("endtime", default=None)
        
        strategies = self.get_arguments("strategy") # 规则命中

        scene_types = self.get_arguments("sceneType")# 规则场景 login visit

        check_types = self.get_arguments("checkType")# 名单类型 ip email mobile

        decisions = self.get_arguments("decision")# 风险类型 accept reject

        page = self.get_argument("page", default=1)
        page = int(page)

        size = self.get_argument("size", default=20)
        size = int(size)

        self.set_header('content-type', 'application/json')
        try:
            count, total, notices = NoticeDao().get_notices(
                key=key, limit=limit, fromtime=fromtime, endtime=endtime,
                strategies=strategies, scene_types = scene_types,
                check_types = check_types, decisions = decisions, page=page, size=size
            )
#            notices = NoticeDao().list_notices(key=key, limit=limit, fromtime=fromtime, endtime=endtime)
#            notices = notices or []
            notices = [_.get_dict() for _ in notices]
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": {'total_page': total, 'count': count, 'items': notices}}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    @authenticated
    def delete(self):
        """
        Remove notices that meet given conditions.

        @API
        summary: delete notices
        notes: Remove notices that meet given conditions.
        tags:
          - default
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
          - default
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


last_query_timestamp = 0
cached_stats = dict()
def get_notice_stats(duration=3600):
    global last_query_timestamp, cached_stats

    current = millis_now()
    if current - last_query_timestamp < 30 * 1000:
        return cached_stats

    fromtime = millis_now() - 600000* 1000
    endtime = millis_now()
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
    REST_URL = "/default/noticestats"

    @authenticated
    def get(self):
        """
        Get top 10 cities notice stats

        @API
        summary: Get top 10 cities notice stats
        notes: get top 10 cities with more notices than others
        tags:
          - default
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

