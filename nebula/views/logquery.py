#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json

from nebula.dao.user_dao import authenticated
from ..dao.logquery_dao import LogQueryDao
from .base import BaseHandler

logger = logging.getLogger('nebula.api.logquery')


class LogQueryConfigHandler(BaseHandler):
    REST_URL = '/platform/logquery_config'

    @authenticated
    def get(self):
        """
        根据用户id搜索日志查询列表
        :return: [{fromtime:, endtime:, terms:, show_cols:}]

        @API
        summary: 获取日志查询列表
        notes: 获取日志查询列表
        tags:
          - platform
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        user_id = self.user.id
        try:
            query_result = LogQueryDao().get_user_logquerys(user_id)
            logquerys = [_.to_dict() for _ in query_result]
            self.finish(json.dumps(
                {"status": 0, "msg": "ok", "values": logquerys}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '查询日志查询列表失败')

    @authenticated
    def post(self):
        """
        添加或者修改日志查询

        @API
        summary: 添加或者修改日志查询
        notes: 以有无id判断是添加或修改操作
        tags:
          - platform
        parameters:
          -
            name: logquery
            in: body
            required: true
            type: json
            description: logquery json
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            logquery = json.loads(self.request.body)
            logquery['user_id'] = self.user.id
            result = LogQueryDao().update_logquery(**logquery)
            if result:
                self.finish(json.dumps(
                    {"status": 0, "msg": "ok", "data": result}))
            else:
                self.process_error(-1, '日志查询不存在')
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '新增日志查询失败')

    @authenticated
    def delete(self):
        """
        删除日志查询
        @API
        summary: 根据id删除日志查询
        notes: 根据id删除日志查询
        tags:
          - platform
        parameters:
          -
            name: id
            in: query
            required: true
            type: json
            description: the id of logquery
        """

        self.set_header('content-type', 'application/json')
        query_id = self.get_argument('id', None)

        try:
            if query_id:
                query_id = int(query_id)
                LogQueryDao().delete_logquery(query_id)
                self.finish(json.dumps(
                    {"status": 0, "msg": "ok", "values": []}))
            else:
                self.process_error(-1, '请输入日志查询 id')
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '删除日志查询失败')
