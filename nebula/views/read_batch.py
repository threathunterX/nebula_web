#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from .base import BaseHandler
from ..dao.notice_dao import NoticeDao


logger = logging.getLogger('nebula.api.batch_notice')


class BatchBWListHandler(BaseHandler):

    def get(self):
        """
        批量查询当前未过期黑白灰名单的值集合接口.

        @API
        summary: 批量查询当前未过期黑白灰名单的值集合接口.
        notes: 批量查询当前未过期黑白灰名单的值集合接口, 返回逗号分隔的黑白灰名单值.
        tags:
          - platform
        parameters:
          -
            name: strategy
            in: query
            required: false
            type: string
            description: filter by strategy name
          -
            name: scene_type
            in: query
            required: false
            type: string
            description: scene type filter statement, ex. login, visit
          -
            name: check_type
            in: query
            required: false
            type: string
            default: IP
            description: check Type filter statement, ex. IP, MOBILE
          -
            name: decision
            in: query
            required: false
            default: reject
            type: string
            description: decision filter statement, ex. accept, reject
          -
            name: test
            in: query
            required: false
            type: string
            default: false
            description: test notice is test or production
        produces:
          - text/plain
        """

        strategy = self.get_argument('strategy', None)
        scene_type = self.get_argument('scene_type', None)
        check_type = self.get_argument('check_type', 'IP')
        decision = self.get_argument('decision', "reject")
        test = self.get_argument('test', 'false')
        if test == "true":
            test = 1
        elif test == "false":
            test = 0
        else:
            test = None

        result = ''

        try:
            ND = NoticeDao()
            data = ND.get_unexpired_notice_data(strategy=strategy, check_type=check_type, decision=decision, test=test,
                                         scene_type=scene_type)
            result = ",".join(data)
        except Exception as err:
            logger.error(err)

        self.set_header('content-type', 'text/plain')
        self.write(result)
