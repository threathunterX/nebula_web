#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
from traceback import print_exc

from .base import BaseHandler
from ..dao.event_model_dao import EventModelCustDao
from nebula.dao.user_dao import authenticated

from threathunter_common.util import json_dumps
from nebula_meta.event_model import EventModel, add_event_to_registry

logger = logging.getLogger('nebula.api.event_model')


# init events
from nebula.dao.event_model_dao import fix_global_event_registry
fix_global_event_registry()


class EventListHandler(BaseHandler):
    REST_URL = "/platform/event_models"

    @authenticated
    def get(self):
        """
        获取相应的event配置类型

        @API
        summary: 获取相应的event配置类型
        notes: 根据app和类型来获取相应的event
        tags:
          - platform
        parameters:
          -
            name: app
            in: query
            required: false
            type: string
            description: event的app
          -
            name: type
            in: query
            required: false
            type: string
            description: event的类型
          -
            name: simple
            in: query
            required: false
            type: boolean
            default: false
            description: 是否采用精简模式输出
        produces:
          - application/json
        """

        app = self.get_argument("app", default="")
        type = self.get_argument("type", default="")
        simple = self.get_argument('simple', default="false")
        simple = simple == 'true'
        self.set_header('content-type', 'application/json')
        try:
            result = EventModelCustDao().list_all_models()
            if app:
                result = filter(lambda model: model.app == app or model.app == "__all__", result)

            if type:
                result = filter(lambda model: model.type == type, result)
            if simple:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [_.get_simplified_ordered_dict() for _ in result]}))
            else:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [_.get_ordered_dict() for _ in result]}))
        except Exception as err:
            print_exc()
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def delete(self):
        """
        删除相应的event配置

        @API
        summary: 删除满足条件的event
        notes: 根据类型和app
        tags:
          - platform
        parameters:
          -
            name: app
            in: query
            required: false
            type: string
            description: event的app，空表示所有
          -
            name: type
            in: query
            required: false
            type: string
            description: event的类型，为空表示所有
        produces:
          - application/json
        """

        app = self.get_argument("app", default="")
        type = self.get_argument("type", default="")
        self.set_header('content-type', 'application/json')
        try:
            EventModelCustDao().delete_model_list_by_app_type(app, type)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def post(self):
        """
        增加一组event

        @API
        summary: 增加一组event
        notes: 增加一组新的event，如果event已存在，则替代
        tags:
          - platform
        parameters:
          -
            name: events
            in: body
            required: true
            type: json
            description: event表示，list结构
        produces:
          - application/json   
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            events = list()
            for _ in json.loads(body):
                event = EventModel.from_dict(_)
                add_event_to_registry(event)
                events.append(event)
        except Exception as err:
            print_exc()
            return self.process_error(400, str(err))

        try:
            dao = EventModelCustDao()
            for event in events:
                dao.add_model(event)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            print_exc()
            return self.process_error(500, str(err))


class EventQueryHandler(BaseHandler):
    """
    对某个特定的event进行操作
    """

    REST_URL = "/platform/event_models/event/{app}/{name}"

    @authenticated
    def get(self, app, name):
        """
        获取一个特定的event

        @API
        summary: 获取一个特定的event
        notes: 根据app和name准确的定位一个event
        tags:
          - platform
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: event的app
          -
            name: name
            in: path
            required: true
            type: string
            description: event的名称
          -
            name: simple
            in: query
            required: false
            type: boolean
            default: false
            description: 是否采用精简模式输出
        produces:
          - application/json
        """

        simple = self.get_argument('simple', default="false")
        simple = simple == 'true'
        self.set_header('content-type', 'application/json')
        try:
            result = EventModelCustDao().get_model_by_app_name(app, name)
            if result:
                if simple:
                    self.finish(json_dumps({"status": 0, "msg": "ok", "values": [result.get_simplified_ordered_dict()]}))
                else:
                    self.finish(json_dumps({"status": 0, "msg": "ok", "values": [result.get_ordered_dict()]}))
            else:
                self.finish(json_dumps({"status": 404, "msg": "not exist"}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def delete(self, app, name):
        """
        删除一个特定的event

        @API
        summary: 删除一个特定的event
        notes: 根据app和名称删除一个特定的event
        tags:
          - platform
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: event的app
          -
            name: name
            in: path
            required: true
            type: string
            description: event的名称
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        try:
            EventModelCustDao().delete_model_by_app_name(app, name)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def post(self, app, name):
        """
        修改或新增一个event

        @API
        summary: 修改或新增一个event
        notes: 根据名称修改一个event
        tags:
          - platform
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: event的app
          -
            name: name
            in: path
            required: true
            type: string
            description: event的名称
          -
            name: event
            in: body
            required: true
            type: json
            description: event的json表示
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            new_model = EventModel.from_json(body)
        except Exception as err:
            return self.process_error(400, str(err))

        try:
            EventModelCustDao().add_model(new_model)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.process_error(500, str(err))


class EventModelBeautifyHandler(BaseHandler):
    """
    对event进行美化输出，不进行存储
    """

    REST_URL = "/platform/event_models_beautify"

    @authenticated
    def post(self):
        """
        美化一组event

        @API
        summary: 美化一组event
        notes: 美化一组event
        tags:
          - platform
        parameters:
          -
            name: event
            in: body
            required: true
            type: json
            description: 一组event的json表示
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            events = list()
            for _ in json.loads(body):
                event = EventModel.from_dict(_)
                events.append(event)
            events = [_.get_simplified_ordered_dict() for _ in events]
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": events}))
        except Exception as err:
            print_exc()
            return self.process_error(400, str(err))
