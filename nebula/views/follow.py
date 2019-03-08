#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, traceback
import logging

from nebula.dao.user_dao import authenticated
from nebula.dao.follow_dao import FollowKeywordDao
from nebula.views.base import BaseHandler

logger = logging.getLogger("nebula.api.crawler")


class FollowKeywordHandler(BaseHandler):
    REST_URL = '/platform/follow_keyword'

    @authenticated
    def get(self):
        """
        关注管理关键字列表

        @API
        summary: 查询所有爬虫关注关键字
        tags:
          - platform
        parameters:
          - name: is_followed
            required: false
            in: query
            type: boolean
            description: 关键字是否关注
          - name: is_ignored
            required: false
            in: query
            type: boolean
            description: 关键字是否忽略
          - name: keyword_type
            required: true
            in: query
            type: string
            description: 关键字类型        
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        followed_str = self.get_argument('is_followed', default=None)
        ignored_str = self.get_argument('is_ignored', default=None)
        keyword_type = self.get_argument('keyword_type', default=None)
        Dimensions = ("page", "did", "uid", "ip")
        if keyword_type not in Dimensions:
            self.process_error(400, '获取关注关键字列表数据库出错')
            return

        is_followed = False
        if followed_str == "true":
            is_followed = True
        
        is_ignored = False
        if ignored_str == "true":
            is_ignored = True

        try:
            d = FollowKeywordDao()
            follow_keyword_list = d.get_follow_keyword_list(keyword_type=keyword_type,
                is_followed=is_followed, is_ignored=is_ignored)
            self.finish(json.dumps(
                {'status': 200, 'msg': 'ok', 'values': follow_keyword_list}))
        except Exception as e:
            logger.error(e)
            self.process_error(400, '获取关注关键字列表数据库出错')

    @authenticated
    def post(self):
        """
        增加关注关键字列表

        @API
        summary: 新增关注关键字
        tags:
          - platform
        parameters:
          - name: follow_keywords
            in: body
            required: true
            type: json
            description: 关注关键字
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')

        try:
            input_follow_keywords = json.loads(self.request.body)
        except Exception as e:
            logger.error(e)
            self.process_error(400, '参数格式不为json')

        for fk in input_follow_keywords:
            if not fk.has_key("keyword") and (not fk.has_key("keyword_type")):
                self.process_error(400, '参数keyword或keyword_type缺失.')
                return

        try:
            d = FollowKeywordDao()
            msg = []
            for fk in input_follow_keywords:
                success, err = d.add_follow_keyword(fk)
                if not success:
                    msg.append("当添加关键字: %s 时, %s" % ( fk["keyword"].encode("utf8"), err))
            if msg:
                self.process_error(400, ";".join(msg))
                return
            self.finish(json.dumps({'status': 200, 'msg': 'ok', 'values': []}))
        except Exception:
            logger.error(traceback.format_exc())
            self.process_error(500, '新增关注关键字到数据库失败')

class FollowKeywordAnotherHandler(BaseHandler):
    REST_URL = '/platform/follow_keyword/{keyword_type}'
    @authenticated
    def delete(self, keyword_type):
        """
        删除关键字列表
        @API
        summary: 删除关注关键字
        tags:
          - platform
        parameters:
          - name: follow_keywords
            in: body
            required: true
            type: list
            description: 关注关键字列表
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')

        try:
            follow_keywords = json.loads(self.request.body)
            logger.debug("Input paramter, keyword_type: %s, keywords: %s(%s)", \
                         keyword_type,follow_keywords, type(follow_keywords))
            if not isinstance(follow_keywords, list):
                self.process_error(400, '关注关键字列表参数错误')
                return
        except Exception as e:
            logger.error(e)
            self.process_error(400, '关注关键字列表参数错误')

        try:
            d = FollowKeywordDao()
            d.delete_follow_keywords(follow_keywords, keyword_type)
            self.finish(json.dumps({'status': 200, 'msg': 'ok', 'values': []}))
        except Exception:
            logger.error(traceback.format_exc())
            self.process_error(500, '删除数据库关键字列表错误')
