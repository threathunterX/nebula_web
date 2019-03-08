#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import json
from urllib import unquote

from tornado.web import RequestHandler

from threathunter_common.util import millis_now

from contrib.read_api_server.cache_property import get_notices, get_notice_cache

logger = logging.getLogger("read_api.notice")


class Notice_List_Handler(RequestHandler):

    def get(self):
        """
        将master的notice cache返回client
        """

        notice_cache = get_notice_cache()
        self.finish(json.dumps(notice_cache))


def get_error_response(reason):
    return dict(
        success=False,
        seq_id=1,
        error_code="拒绝原因: {}".format(reason),
        scene_type="",
        final_rule_hit="",
        final_decision="",
        final_key_hit="",
        final_value_hit="",
        final_desc="",
        expire_time=0,
        rule_hits=[])


def check_request_argument(method):
    """
    检测API请求参数是否满足要求,格式为json
    """
    def request_decorator(func):
        def func_wrapper(self, *args, **kwargs):
            self.set_header("content-type", "application/json")

            try:
                query = unquote(self.get_argument("query", "")
                                ) if method == "get" else self.request.body
                json.loads(query)
            except Exception as err:
                logger.error(err)
                result = get_error_response("错误的查询请求")
                self.finish(json.dumps(result))

            return func(self, *args, **kwargs)

        return func_wrapper
    return request_decorator


def check_blacklist(method):
    """
    API请求参数校验黑名单
    """
    def request_decorator(func):
        def func_wrapper(self, *args, **kwargs):
            self.set_header("content-type", "application/json")
            query = unquote(self.get_argument("query", "")
                            ) if method == "get" else self.request.body
            query = json.loads(query)
            full_respond = bool(query.get("full_respond", ""))
            test = self.request.path.lower().endswith("test")

            try:
                check(query, test, full_respond)
            except Exception as err:
                logger.error(err)
                result = get_error_response("校验黑名单失败")
                self.finish(json.dumps(result))

            return func(self, *args, **kwargs)

        return func_wrapper
    return request_decorator


class Notice_Cache_Handler(RequestHandler):

    @check_request_argument("get")
    def get(self):
        """
        Check against the white/black lists in nebula.

        @param query: the query data in the form of url-encoded json
        @defaultvalue query:
        @paramtype query: query
        @required query: true
        @datatype query: string
        """

        self.set_header("content-type", "application/json")
        query = self.get_argument("query", default="")
        query = unquote(query)
        query = json.loads(query)
        full_respond = bool(query.get("full_respond", ""))
        test = self.request.path.lower().endswith("test")

        try:
            result = check(query, test, full_respond)
        except Exception as err:
            logger.error(err)
            result = get_error_response("校验黑名单失败")

        self.finish(json.dumps(result))

    @check_request_argument("post")
    def post(self):
        """
        @param query: the query of the request
        @paramtype query: body
        @defaultvalue query:
        @required query: true
        @datatype query: json
        """

        self.set_header("content-type", "application/json")
        query = self.request.body
        query = json.loads(query)
        full_respond = bool(query.get("full_respond", ""))
        test = self.request.path.lower().endswith("test")

        try:
            result = check(query, test, full_respond)
        except Exception as err:
            logger.error(err)
            result = get_error_response("校验黑名单失败")

        self.finish(json.dumps(result))


class CheckRiskTestHandler(RequestHandler):

    def get_result(self, full_respond):
        return dict()

    @check_request_argument("get")
    @check_blacklist("get")
    def get(self):
        self.set_header("content-type", "application/json")
        query = self.get_argument("query", default="")
        query = unquote(query)
        query = json.loads(query)
        full_respond = bool(query.get("full_respond", ""))

        # hack the result
        result = self.get_result(full_respond)
        self.finish(json.dumps(result))

    @check_request_argument("post")
    @check_blacklist("post")
    def post(self):
        self.set_header("content-type", "application/json")
        query = self.request.body
        query = json.loads(query)
        full_respond = bool(query.get("full_respond", ""))

        # hack the result
        result = self.get_result(full_respond)
        self.finish(json.dumps(result))


class GiveMeAcceptHandler(CheckRiskTestHandler):

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
        Check against the white/black lists in nebula.

        @param query: the query data in the form of url-encoded json
        @defaultvalue query:
        @paramtype query: query
        @required query: true
        @datatype query: string
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        @param query: the query of the request
        @paramtype query: body
        @defaultvalue query:
        @required query: true
        @datatype query: json
        """
        return CheckRiskTestHandler.post(self)


class GiveMeReviewHandler(CheckRiskTestHandler):

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
        Check against the white/black lists in nebula.

        @param query: the query data in the form of url-encoded json
        @defaultvalue query:
        @paramtype query: query
        @required query: true
        @datatype query: string
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        @param query: the query of the request
        @paramtype query: body
        @defaultvalue query:
        @required query: true
        @datatype query: json
        """
        return CheckRiskTestHandler.post(self)


class GiveMeRejectHandler(CheckRiskTestHandler):

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
        Check against the white/black lists in nebula.

        @param query: the query data in the form of url-encoded json
        @defaultvalue query:
        @paramtype query: query
        @required query: true
        @datatype query: string
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        @param query: the query of the request
        @paramtype query: body
        @defaultvalue query:
        @required query: true
        @datatype query: json
        """
        return CheckRiskTestHandler.post(self)


class GiveMeNothingHandler(CheckRiskTestHandler):

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
        Check against the white/black lists in nebula.

        @param query: the query data in the form of url-encoded json
        @defaultvalue query:
        @paramtype query: query
        @required query: true
        @datatype query: string
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        @param query: the query of the request
        @paramtype query: body
        @defaultvalue query:
        @required query: true
        @datatype query: json
        """
        return CheckRiskTestHandler.post(self)


class GiveMeErrorHandler(CheckRiskTestHandler):

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
        Check against the white/black lists in nebula.

        @param query: the query data in the form of url-encoded json
        @defaultvalue query:
        @paramtype query: query
        @required query: true
        @datatype query: string
        """
        return CheckRiskTestHandler.get(self)

    def post(self):
        """
        @param query: the query of the request
        @paramtype query: body
        @defaultvalue query:
        @required query: true
        @datatype query: json
        """
        return CheckRiskTestHandler.post(self)


def get_risk_data(test=False, check_items=[], scene_types=[]):
    notices = []
    for item in check_items:
        check_type = item.get("k")
        key = item.get("v")
        if not check_type:
            raise RuntimeError("the check item key should not be empty")
        if not key:
            raise RuntimeError("the check item value should not be empty")

        # Diff: use cache getter instead
        notices.extend(get_notices(None, check_type, key, test, scene_types))

    notices.sort(cmp=lambda a, b: cmp(a.timestamp, b.timestamp))
    return notices


def check(query, test=False, full_respond=False):
    check_items = query.get("check_item", [])
    scene_type = query.get("scene_type", "")
    scene_types = [scene_type] if scene_type else []

    try:
        notices = get_risk_data(test, check_items, scene_types)
    except Exception as err:
        logger.error(err)
        return get_error_response("无法获取黑名单数据")

    result = dict()
    if notices:
        #@todo 排序
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
            result["rule_hits"] = [dict(rule_name=_.strategy_name, key_hit=_.check_type,
                                        key_value=_.key, decision=_.decision,
                                        remark=_.remark) for _ in notices]
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
