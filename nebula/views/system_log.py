#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import path
import logging

from threathunter_common.util import json_dumps

from nebula.views.base import BaseHandler
from nebula.dao.user_dao import authenticated
import settings

logger = logging.getLogger('nebula.api.system_log')

log_path = settings.Log_Path


class LogInfoHandler(BaseHandler):

    REST_URL = '/system/log'

    @authenticated
    def get(self):
        """
        通过API获取nebula各模块日志数据

        @API
        summary: 通过API获取nebula日志文件数据
        description: 读取nebula日志文件最后100行
        tags:
          - system
        parameters:
          - name: module
            in: query
            required: true
            type: string
            description: 日志模块
          - name: name
            in: query
            required: true
            type: string
            description: 日志文件名
          - name: size
            in: query
            required: false
            type: integer
            description: 返回日志字节大小
        produces:
          - application/json
        """

        module = self.get_argument("module", default="")
        file_name = self.get_argument("name", default="")
        size = self.get_argument("size", default=1000000)
        size = int(size)

        self.set_header('content-type', 'application/json')

        try:
            log_dir = path.join(log_path, module)
            if not path.exists(log_dir):
                self.process_error(-1, "服务器不存在日志目录%s" % log_dir)
                return

            log_file = path.join(log_dir, file_name)
            if not path.isfile(log_file):
                self.process_error(-1, "服务器不存在日志文件%s" % log_file)
                return

            read_logs = []
            with open(log_file, 'r') as f:
                f.seek(-size, 2)

                for row in f.readlines()[1:]:
                    read_logs.append(row.strip())

            self.write('\n'.join(read_logs).encode('utf-8'))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "读取日志文件失败"}))
