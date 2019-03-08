#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from .base import BaseHandler
from ..services import babel

from threathunter_common.event import Event
from threathunter_common.util import millis_now, json_dumps
from nebula.dao.user_dao import authenticated
from ..dao.notice_dao import NoticeDao


logger = logging.getLogger('nebula.api.monitor')
keyTopValueClient = babel.get_key_top_value_client()


class RiskyItemsHandler(BaseHandler):
    REST_URL = "/platform/monitor/riskyitems"

    @authenticated
    def get(self):
        """
        get all the risky items in last period.

        @API
        summary: get all the risky items in last period
        notes: get all the risky items in last period
        tags:
          - platform
        parameters:
          -
            name: period
            in: query
            required: false
            type: long
            default: 60
            description: the period of the risky items for the request
        produces:
          - application/json
        """

        period = self.get_argument("period", default='60')
        period = int(period)

        self.set_header('content-type', 'application/json')
        within_hit = 300 * 1000 # 默认5min内命中才显示 ,ps.多久之内又命中的持续报警才显示
        current = millis_now()
        within_time = current - within_hit
        ND = NoticeDao()
        whitelist_keys = set(ND.get_whitelist_keys(current))
        try:
            notices = ND.list_notices(fromtime=(current-period*1000), endtime=current)
            notices = notices or []
            notices = [_ for _ in notices if not _.test]

            stats = {
                "visit": {},
                "account": {},
                "fraud": {},
                "other": {}
            }

            for n in notices:
                scene_name = n.scene_name
                group_key = "{}__{}".format(n.strategy_name, n.key)
                if scene_name == "visit":
                    stat = stats["visit"]
                elif scene_name in {"login", "regist"}:
                    stat = stats["account"]
                elif scene_name == "fraud":
                    stat = stats["fraud"]
                else:
                    stat = stats["other"]

                if group_key not in stat:
                    stat[group_key] = dict(key=n.key, location=n.geo_city,
                                           strategy=n.strategy_name, count=0, test=n.test,
                                           timestamp=n.timestamp, check_type=n.check_type)
                stat[group_key]["count"] = stat[group_key]["count"] + 1

            for stat_key in stats.keys():
                stats[stat_key] = [ _ for _ in stats[stat_key].values() \
                                    if _['timestamp'] >= within_time and \
                                    (_['key'], _['check_type'], _['test']) not in whitelist_keys]
                # 过滤条件: 1.命中时间在5min内才需要显示 2. (key, check_type, test)有对应白名单不显示 (也会自动过滤掉白名单)
                stats[stat_key].sort(key=lambda x: x["count"], reverse=True)

            result = stats
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))


class TopTargetsHandler(BaseHandler):
    REST_URL = "/platform/monitor/toptargets"

    @authenticated
    def get(self):
        """
        get top targets in last period

        @API
        summary: get top targets in last period
        notes: get top targets in last period
        tags:
          - platform
        parameters:
          -
            name: period
            in: query
            required: false
            type: long
            default: 60
            description: the period of the top targets for the request
        produces:
          - application/json
        """

        period = self.get_argument("period", default='60')
        period = int(period)

        self.set_header('content-type', 'application/json')
        current = millis_now()
        try:
            notices = NoticeDao().list_notices(fromtime=(current-period*1000), endtime=current)
            notices = notices or []

            keys = {n.key for n in notices}

            top_host = {}
            top_url = {}

            for key in keys:
                property_values = dict()
                property_values["keypattern"] = key + "%"
                property_values["varname"] = 'http_count_byurl_ip'
                request = Event("__all__", "_global__variablekeytopvalue_request", "", millis_now(), property_values)
                response = keyTopValueClient.send(request, "", block=False, timeout=3)
                success, result_event = response
                if success:
                    values = result_event[0].property_values
                    for k, v in zip(values['keynames'], values['varvalues']):
                        k = k.split("@@", 1)[1]
                        if "/" in k:
                            host = k.split("/")[0]
                        else:
                            host = k

                        top_host[host] = top_host.setdefault(host, 0) + v
                        top_url[k] = top_url.setdefault(k, 0) + v

            top_host = top_host.items()
            top_host.sort(key=lambda (x,y): y)
            top_host = top_host[-10:]
            top_host = [[k,v] for k, v in top_host]

            top_url = top_url.items()
            top_url.sort(key=lambda (x,y): y)
            top_url = top_url[-10:]
            top_url = [[k,v] for k, v in top_url]
            result = {
                "top_host": top_host,
                "top_url": top_url
            }
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))


class TopCitiesHandler(BaseHandler):
    REST_URL = "/platform/monitor/topcities"

    @authenticated
    def get(self):
        """
        get top cities in last period

        @API
        summary: get top cities in last period
        notes: get top cities in last period
        tags:
          - platform
        parameters:
          -
            name: period
            in: query
            required: false
            type: long
            default: 60
            description: the period during which we are querying top cities
        produces:
          - application/json
        """

        period = self.get_argument("period", default='60')
        period = int(period)

        self.set_header('content-type', 'application/json')
        current = millis_now()
        try:
            notices = NoticeDao().list_notices(fromtime=(current-period*1000), endtime=current)
            notices = notices or []
            notices = [n for n in notices if not n.test and n.scene_name != 'visit']

            cities = {}
            for n in notices:
                city = n.geo_city
                if not city:
                    city = "unknown"

                if n.geo_city == n.geo_province and n.geo_city[:2] not in {'北京','上海','重庆','天津'}:
                    city = "unknown"
                cities[city] = cities.setdefault(city, 0) + 1

            cities = cities.items()
            cities.sort(key=lambda (x, y): y, reverse=True)
            cities = [{"name": c[0], "value": c[1]} for c in cities]
            result = {
                "cities": cities
            }
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))
