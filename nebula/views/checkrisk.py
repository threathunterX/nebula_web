#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import urllib
import json

from .base import BaseHandler
#from nebula.middleware.tornado_rest_swagger.restutil import rest_class, rest_method
from ..dao.notice_dao import NoticeDao
from ..dao.strategy_dao import StrategyCustDao
from nebula.dao.user_dao import authenticated

from threathunter_common.util import json_dumps, millis_now

logger = logging.getLogger('web.api.checkrisk')


class CheckRiskHandler(BaseHandler):
    REST_URL = '/checkRisk'
    @authenticated
    def get(self):
        """
        查询黑白名单

        @API
        summary: check risk
        notes: "check for the actions on the given key, according to the white/black lists"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        query = self.get_argument("query", default="")
        try:
            query = urllib.unquote(query)
            query = json.loads(query)
        except Exception as err:
            result = get_error_response("错误的查询请求")
            logger.warn(err)
            self.finish(json_dumps(result))
            return

        full_respond = bool(query.get("full_respond", ""))
        test = self.request.uri.lower().endswith("test")

        try:
            result = check(query, test, full_respond)
        except Exception as err:
            logger.error(err)
            result = get_error_response("校验黑名单失败")

        self.finish(json_dumps(result))
        return
    @authenticated
    def post(self):
        """
        查询黑白名单

        @API
        summary: check risk
        notes: "check for the actions on the given key, according to the white/black lists"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        query = self.request.body
        try:
            query = json.loads(query)
        except Exception as err:
            result = get_error_response("错误的查询请求")
            logger.warn(err)
            self.finish(json_dumps(result))
            return

        full_respond = bool(query.get("full_respond", ""))
        test = self.request.uri.lower().endswith("test")

        try:
            result = check(query, test, full_respond)
        except Exception as err:
            logger.error(err)
            result = get_error_response("校验黑名单失败")

        self.finish(json_dumps(result))
        return


class CheckRiskTestHandler(BaseHandler):
    REST_URL = '/checkRiskTest'

    def get_result(self, full_respond):
        return dict()
    @authenticated
    def get(self):
        """
        查询测试的黑白名单

        @API
        summary: check risk
        notes: "check for the Test actions on the given key, according to the white/black lists"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        query = self.get_argument("query", default="")
        try:
            query = urllib.unquote(query)
            query = json.loads(query)
        except Exception as err:
            result = get_error_response("错误的查询请求")
            logger.warn(err)
            self.finish(json_dumps(result))
            return

        full_respond = bool(query.get("full_respond", ""))
        test = self.request.uri.lower().endswith("test")

        try:
            result = check(query, test, full_respond)
        except Exception as err:
            logger.error(err)
            result = get_error_response("校验黑名单失败")
            self.finish(json_dumps(result))
            return

        # hack the result
        result = self.get_result(full_respond)
        self.finish(json_dumps(result))
        return
    
    @authenticated
    def post(self):
        """
        查询测试的黑白名单, 区别于get方法只是查询参数所在成了body

        @API
        summary: check risk
        notes: "check for the actions on the given key, according to the white/black lists"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        query = self.request.body
        try:
            query = json.loads(query)
        except Exception as err:
            result = get_error_response("错误的查询请求")
            logger.warn(err)
            self.finish(json_dumps(result))
            return

        full_respond = bool(query.get("full_respond", ""))
        test = self.request.uri.lower().endswith("test")

        try:
            result = check(query, test, full_respond)
        except Exception as err:
            logger.error(err)
            result = get_error_response("校验黑名单失败")
            self.finish(json_dumps(result))
            return

        # hack the result
        result = self.get_result(full_respond)
        self.finish(json_dumps(result))
        return

class GiveMeAcceptHandler(CheckRiskTestHandler):
    REST_URL = '/checkRiskTest/GiveMeAccept'
    
    def get_result(self, full_respond):
        result = dict()
        result["success"] = True
        result["seq_id"] = 1
        result["error_code"] = ""
        result["scene_type"] = "login"
        result["final_rule_hit"] = "test_rule"
        result["final_decision"] = "accept"
        result["final_key_hit"] = "ip"
        result["final_value_hit"] = "192.168.0.1"
        result["final_desc"] = "黑名单说明"
        result["expire_time"] = millis_now() + 3600 * 1000
        result["rule_hits"] = []
        if full_respond:
            result["rule_hits"] = [{"rule_name": "test_rule", "key_hit": "ip", "key_value": "192.168.0.1",
                                    "decision": "accept", "remark": "黑名单说明"}]
        return result

    def get(self):
        """
        查询测试的黑白名单, 并返回写死的白名单 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the accept result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        查询测试的黑白名单, 并返回写死的白名单 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "check for the actions on the given key, according to the white/black lists"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.post(self)

class GiveMeReviewHandler(CheckRiskTestHandler):
    REST_URL = "/checkRiskTest/GiveMeReview"
    
    def get_result(self, full_respond):
        result = dict()
        result["success"] = True
        result["seq_id"] = 1
        result["error_code"] = ""
        result["scene_type"] = "login"
        result["final_rule_hit"] = "test_rule"
        result["final_decision"] = "review"
        result["final_key_hit"] = "ip"
        result["final_value_hit"] = "192.168.0.1"
        result["final_desc"] = "黑名单说明"
        result["expire_time"] = millis_now() + 3600 * 1000
        result["rule_hits"] = []
        if full_respond:
            result["rule_hits"] = [{"rule_name": "test_rule", "key_hit": "ip", "key_value": "192.168.0.1",
                                    "decision": "review", "remark": "黑名单说明"}]
        return result

    def get(self):
        """
        查询测试的黑白名单, 并返回写死的灰名单 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the review result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        查询测试的黑白名单, 并返回写死的灰名单 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the review result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.post(self)


class GiveMeRejectHandler(CheckRiskTestHandler):
    REST_URL = "/checkRiskTest/GiveMeReject"

    def get_result(self, full_respond):
        result = dict()
        result["success"] = True
        result["seq_id"] = 1
        result["error_code"] = ""
        result["scene_type"] = "login"
        result["final_rule_hit"] = "test_rule"
        result["final_decision"] = "reject"
        result["final_key_hit"] = "ip"
        result["final_value_hit"] = "192.168.0.1"
        result["final_desc"] = "黑名单说明"
        result["expire_time"] = millis_now() + 3600 * 1000
        result["rule_hits"] = []
        if full_respond:
            result["rule_hits"] = [{"rule_name": "test_rule", "key_hit": "ip", "key_value": "192.168.0.1",
                                    "decision": "reject", "remark": "黑名单说明"}]
        return result

    def get(self):
        """
        查询测试的黑白名单, 并返回写死的黑名单 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the reject result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        查询测试的黑白名单, 并返回写死的黑名单 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the reject result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.post(self)

class GiveMeNothingHandler(CheckRiskTestHandler):
    REST_URL = "/checkRiskTest/GiveMeNothing"

    def get_result(self, full_respond):
        result = dict()
        result["success"] = True
        result["seq_id"] = 1
        result["error_code"] = ""
        result["scene_type"] = ""
        result["final_rule_hit"] = ""
        result["final_decision"] = ""
        result["final_key_hit"] = ""
        result["final_value_hit"] = ""
        result["final_desc"] = ""
        result["expire_time"] = 0
        result["rule_hits"] = []
        return result

    def get(self):
        """
        查询测试的黑白名单, 并返回写死的成功无命中 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the nothing result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        查询测试的黑白名单, 并返回写死的成功无命中 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the nothing result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.post(self)


class GiveMeErrorHandler(CheckRiskTestHandler):
    REST_URL = "/checkRiskTest/GiveMeError"

    def get_result(self, full_respond):
        result = dict()
        result["success"] = False
        result["seq_id"] = 1
        result["error_code"] = "拒绝原因: {}".format("错误的请求")
        result["scene_type"] = ""
        result["final_rule_hit"] = ""
        result["final_decision"] = ""
        result["final_key_hit"] = ""
        result["final_value_hit"] = ""
        result["final_desc"] = ""
        result["expire_time"] = 0
        result["rule_hits"] = []
        return result

    def get(self):
        """
        查询测试的黑白名单, 并返回写死的错误返回 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the error result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: query
            required: true
            type: string
            description: "the query data in the form of url-encoded json"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        查询测试的黑白名单, 并返回写死的错误返回 ps. 其实也需要正确的payload跑去查询了测试的黑白名单，并不是直接不管payload的正确性直接返回写死的测试数据的@todo

        @API
        summary: check risk
        notes: "give the error result for test"
        tags:
          - blacklist
        parameters:
          -
            name: query
            in: body
            required: true
            type: json
            description: "the query of the request"
        produces:
          - application/json
        """
        return CheckRiskTestHandler.post(self)


def get_error_response(reason):
    result = dict()
    result["success"] = False
    result["seq_id"] = 1
    result["error_code"] = "拒绝原因: {}".format(reason)
    result["scene_type"] = ""
    result["final_rule_hit"] = ""
    result["final_decision"] = ""
    result["final_key_hit"] = ""
    result["final_value_hit"] = ""
    result["final_desc"] = ""
    result["expire_time"] = 0
    result["rule_hits"] = []
    return result


def get_risk_data(test=False, check_items=[], scene_types=[]):
    dao = NoticeDao()
    notices = []
    for item in check_items:
        check_type = item.get("k")
        key = item.get("v")
        if not check_type:
            raise RuntimeError("the check item key should not be empty")
        if not key:
            raise RuntimeError("the check item value should not be empty")

        notices.extend(dao.get_notices_for_checking(check_type, key, test, scene_types))

    notices.sort(cmp=lambda a, b: cmp(a.timestamp, b.timestamp))
    return notices


def filter_by_realtime_strategies(notices):
    """
    Filter the notices whose
    :return:
    """

    if not notices:
        return []

    online_s = StrategyCustDao().get_cached_online_strategies()
    return [n for n in notices if n.name in online_s]


def check(query, test=False, full_respond=False):
    check_items = query.get("check_item", [])
    scene_type = query.get("scene_type", "")
    scene_types = [scene_type] if scene_type else []

    try:
        notices = get_risk_data(test, check_items, scene_types)
    except Exception as err:
        logger.error(err)
        return get_error_response("无法获取黑名单数据")

    result = {}
    if notices:
        n = notices[0]
        result["success"] = True
        result["seq_id"] = 1
        result["error_code"] = ""
        result["scene_type"] = n.scene_name
        result["final_rule_hit"] = n.strategy_name
        result["final_decision"] = n.decision
        result["final_key_hit"] = n.check_type
        result["final_value_hit"] = n.key
        result["final_desc"] = n.remark
        result["expire_time"] = n.expire
        if full_respond:
            result["rule_hits"] = [{"rule_name": _.strategy_name, "key_hit": _.check_type, "key_value": _.key,
                                    "decision": _.decision, "remark": _.remark} for _ in notices]
        else:
            result["rule_hits"] = []
    else:
        result["success"] = True
        result["seq_id"] = 1
        result["error_code"] = ""
        result["scene_type"] = ""
        result["final_rule_hit"] = ""
        result["final_decision"] = ""
        result["final_key_hit"] = ""
        result["final_value_hit"] = ""
        result["final_desc"] = ""
        result["expire_time"] = 0
        result["rule_hits"] = []

    return result
