#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#————————————————————————————————————————————————————
# FileName: supervisor.py
# Version: 0.1
# Author : Rancho
# Email: 
# LastChange: 1/30/2019
# Desc:
# History:
#————————————————————————————————————————————————————
"""
import json
import xmlrpclib
from tornado.web import RequestHandler
from nebula.dao.user_dao import authenticated
import logging
logger = logging.getLogger('nebula.api.supervisor')


class Supervisor(RequestHandler):
    @authenticated
    def get(self):
        # getAllProcessInfo and read ProcessStd tail outLog (1000)
        """
        :argument
        info: process_info / stdout_log
        process_name: None / process_name
        :return:
        status_code: status code
        status_message: status message
        result: result
        """
        result = dict(
            status_code=500,
            status_message='program error',
            result=[],
        )
        content = self.get_argument("info", "process_info")
        process_name = self.get_argument("process_name", "")
        server = xmlrpclib.Server('http://threathunter:threathunter@localhost:8086/RPC2')
        if content == 'stdout_log':
            logger.debug('in stdout log')
            data = server.supervisor.tailProcessStdoutLog(process_name, 0, 1000)
            result['status_code'] = 200
            result['status_message'] = 'ok'
            result['result'] = data
        elif content == "process_info":
            data = server.supervisor.getAllProcessInfo()
            result['status_code'] = 200
            result['status_message'] = 'ok'
            result['result'] = data
        else:
            result['status_code'] = 412
            result['status_message'] = 'argument error'

        self.write(json.dumps(result))

    @authenticated
    def put(self):
        # start stop Process
        """
        :argument
        process_name: process name
        status: start or stop
        :return:
        status_code: status code
        status_message: status message
        result: result
        """
        result = dict(
            status_code=500,
            status_message='program error',
            result=[],
        )
        agrs = self.request.body
        agrs = json.loads(agrs)
        process_name = agrs.get('process_name')
        status = agrs.get('status')
        server = xmlrpclib.Server('http://threathunter:threathunter@localhost:8086/RPC2')
        if process_name is not None:
            if status == 'start':
                b = server.supervisor.startProcess(process_name)
                result['status_code'] = '200'
                result['status_message'] = b
            elif status == 'stop':
                b = server.supervisor.stopProcess(process_name)
                result['status_code'] = '200'
                result['status_message'] = b
            else:
                pass
        else:
            result['status_code'] = 412
            result['status_message'] = "argument error or can't find process name"
        self.write(json.dumps(result))
