#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json

from threathunter_common.util import json_dumps

from nebula.dao.user_dao import authenticated
from nebula_parser.parser_initializer import init_parser
from nebula_parser.autoparser import test_parsers
from ..dao.logparser_dao import LogParserCustDao
from .base import BaseHandler

logger = logging.getLogger('nebula.api.logparser')


# initialize parser
from .nebula_config import context
def load_event_schema():
    events = [_.get_dict() for _ in context.nebula_events]
    event_schema = dict()
    for event in events:
        properties = {p["name"]: p["type"] for p in event["properties"]}
        event_schema[event["name"]] = properties
    return event_schema


init_parser(load_event_schema, None)


class LogParserListHandler(BaseHandler):
    REST_URL = '/platform/logparser'

    @authenticated
    def get(self):
        """
        Return:
        Parser Config: {source: , dest: , terms: , remark: , status: , id:}
        {"status": 0, "msg": "ok", "values": {'total_page': total, 'count': count, 'items': [ parser configs]}}
        @API
        summary: 获取日志解析配置列表
        notes: 获取日志解析配置列表
        tags:
          - platform
        parameters:
          -
            name: name
            in: query
            required: false
            type: string
            description: parser name
          -
            name: host
            in: query
            required: false
            type: string
            description: parser host
          -
            name: url
            in: query
            required: false
            type: string
            description: parser url
          -
            name: status
            in: query
            required: false
            type: int
            description: parser status
          -
            name: offset
            in: query
            required: false
            type: long
            default: 1
            description: page number
          -
            name: limit
            in: query
            required: false
            type: int
            default: 20
            description: the max number of parser config that should be return
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        # 查询dest名称
        name = self.get_argument('name', None)

        # 查询terms中的host
        host = self.get_argument('host', None)

        # 查询terms中的url
        url = self.get_argument('url', None)

        # 查询parser的status
        status = self.get_argument('status', None)

        offset = int(self.get_argument('offset', 1))
        limit = int(self.get_argument('limit', 20))

        try:
            parser_list = LogParserCustDao().get_all_logparsers(
                name=name, host=host, url=url, status=status)
            # 返回logparser总数，根据limit算出页数，并返回指定页数的logparser
            count = len(parser_list)
            if count % limit == 0:
                total_page = count / limit
            else:
                total_page = count / limit + 1

            split_parser_list = [parser.to_dict() for parser in parser_list[
                (offset - 1) * limit:offset * limit]]

            self.finish(json_dumps({"status": 0, "msg": "ok", "count": count,
                                    "total_page": total_page, "values": split_parser_list}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询logparser失败')

    @authenticated
    def post(self):
        """
        add or update custom logparser

        @API
        summary: add or update custom logparser
        notes: add or update custom logparser
        tags:
          - platform
        parameters:
          -
            name: logparsers
            in: body
            required: true
            type: json
            description: logparser json
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')

        try:
            logparser = json.loads(self.request.body)
            # validation
            test_parsers([logparser])

            result = LogParserCustDao().upsert_logparser(**logparser)
            if result:
                self.finish(json_dumps(
                    {"status": 0, "msg": "ok", "values": []}))
            else:
                self.process_error(-1, 'log parser不存在')
        except Exception as e:
            # 打印出错信息
            logger.error(e)
            self.process_error(-1, u'%s' % e)

    @authenticated
    def delete(self):
        """
        delete specific logparser
        @API
        summary: delete a custom logparser
        notes: delete a custom logparser
        tags:
          - platform
        parameters:
          -
            name: id
            in: query
            required: true
            type: json
            description: the id of logparser
        """

        self.set_header('content-type', 'application/json')
        parser_id = self.get_argument('id', None)

        try:
            if parser_id:
                parser_id = int(parser_id)
                LogParserCustDao().delete_logparser(parser_id)
                self.finish(json_dumps(
                    {"status": 0, "msg": "ok", "values": []}))
            else:
                self.process_error(-1, '请输入log parser id')
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '删除log parser失败')
