#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging
from traceback import print_exc

from .base import BaseHandler
from threathunter_common.util import json_dumps
from nebula.dao.user_dao import authenticated
from ..dao.variable_model_dao import VariableModelDefaultDao

from nebula_meta.variable_model import VariableModel, add_variable_to_registry

logger = logging.getLogger('nebula.api.variable_default')


# init events
from nebula.dao.event_model_dao import fix_global_event_registry
fix_global_event_registry()
from nebula.dao.variable_model_dao import fix_global_variable_registry
fix_global_variable_registry()


class VariableModelListHandler(BaseHandler):
    REST_URL = "/default/variable_models"

    @authenticated
    def get(self):
        """
        列出相应的变量列表

        @API
        summary: 列出相应的变量列表
        notes: 根据相关条件过滤出符合的变量列表
        tags:
          - default
        parameters:
          -
            name: app
            in: query
            required: false
            type: string
            description: 变量的app，空表示所有
          -
            name: type
            in: query
            required: false
            type: string
            description: 变量的类型，空表示所有
          -
            name: name
            in: query
            required: false
            type: string
            description: 变量的名称，空表示所有
          -
            name: modules
            in: query
            required: false
            type: string
            description: 变量的模块，空表示所有, 可以有多个值
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
        name = self.get_argument("name", default="")
        modules = self.get_arguments("modules")
        simple = self.get_argument('simple', default="false")
        simple = simple == 'true'

        self.set_header('content-type', 'application/json')
        try:
            result = VariableModelDefaultDao().list_all_models()
            if app:
                result = filter(lambda model: model.app == app or model.app == "__all__", result)

            if type:
                result = filter(lambda model: model.type == type, result)

            if name:
                result = filter(lambda model: model.name == name, result)

            # modules为module列表
            if modules:
                result = filter(lambda module: module.module in modules, result)

            if simple:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [_.get_simplified_ordered_dict() for _ in result]}))
            else:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [_.get_ordered_dict() for _ in result]}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def delete(self):
        """
        删除相应的变量

        @API
        summary: 删除相应的变量
        notes: 根据app等条件删除相应的变量
        tags:
          - default
        parameters:
          -
            name: app
            in: query
            required: false
            type: string
            description: 变量的app，空表示所有
          -
            name: type
            in: query
            required: false
            type: string
            description: 变量的type，空表示所有
          -
            name: module
            in: query
            required: false
            type: string
            description: 变量的模块，空表示所有
        produces:
          - application/json
        """

        app = self.get_argument("app", default="")
        type = self.get_argument("type", default="")
        module = self.get_argument("module", default='')
        self.set_header('content-type', 'application/json')
        try:
            VariableModelDefaultDao().delete_model_list_by_app_type_module(app, type, module)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def post(self):
        """
        增加一组变量

        @API
        summary: 增加一组变量
        notes: 增加一组变量，如果变量已存在，则修改
        tags:
          - default
        parameters:
          -
            name: variables
            in: body
            required: true
            type: json
            description: 变量的json表示，list结构
        produces:
          - application/json   
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            variables = list()
            for _ in json.loads(body):
                v = VariableModel.from_dict(_)
                add_variable_to_registry(v)
                variables.append(v)
        except Exception as err:
            return self.process_error(400, str(err))

        try:
            dao = VariableModelDefaultDao()
            for v in variables:
                dao.add_model(v)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            print_exc()
            return self.process_error(500, str(err))


class VariableModelQueryHandler(BaseHandler):
    REST_URL = "/default/variable_models/variable/{app}/{name}"

    @authenticated
    def get(self, app, name):
        """
        获取一个指定的变量

        @API
        summary: 获取一个指定的变量
        notes: 根据app和name获取一个指定的变量
        tags:
          - default
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: 变量的app
          -
            name: name
            in: path
            required: true
            type: string
            description: 变量的名称
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
            result = VariableModelDefaultDao().get_model_by_app_name(app, name)
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
        删除一个指定的变量

        @API
        summary: 删除一个指定的变量
        notes: 删除一个指定的变量
        tags:
          - default
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: 变量的app
          -
            name: name
            in: path
            required: true
            type: string
            description: 变量的名称
        produces:
          - application/json
        """
        
        self.set_header('content-type', 'application/json')
        try:
            VariableModelDefaultDao().delete_model_by_app_name(app, name)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": str(err)}))

    @authenticated
    def post(self, app, name):
        """
        增加/修改一个变量

        @API
        summary: 增加/修改一个变量
        notes: 增加/修改一个变量
        tags:
          - default
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: 变量的app
          -
            name: name
            in: path
            required: true
            type: string
            description: 变量的名称
          -
            name: variable
            in: body
            required: true
            type: json
            description: 变量的json表示
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            new_model = VariableModel.from_json(body)
        except Exception as err:
            return self.process_error(400, str(err))

        try:
            VariableModelDefaultDao().add_model(new_model)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.process_error(500, str(err))

