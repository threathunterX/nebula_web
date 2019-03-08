#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging, json

from .base import BaseHandler
from ..dao.config_dao import ConfigCustDao
#from nebula.middleware.tornado_rest_swagger.restutil import rest_class, rest_method
from nebula.dao.user_dao import authenticated

from threathunter_common.util import json_dumps

logger = logging.getLogger('web.api.config')

class ConfigListHandler(BaseHandler):
    @authenticated
    def get(self):
        """
        get all config items list
        @API
        summary: get all config items list
        notes: get all config items
        tags:
          - platform
        parameters:
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            result = ConfigCustDao().list_all_config()
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))
    @authenticated
    def delete(self):
        """
        delete all the configs.
        @API
        summary: delete all the configs.
        notes: delete all the configs.
        tags:
          - platform
        parameters:
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            ConfigCustDao().clear()
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to delete data in database"}))
    @authenticated
    def post(self):
        """
        add a list of new config items
        @API
        summary: add a list of new config items
        notes: add a list of new config items
        tags:
          - platform
        parameters:
          -
            name: configs
            in: body
            required: true
            type: json
            description: the list of the config json item
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            items = json.loads(body)
        except Exception as error:
            return self.process_error(404, "invalid request body: {}".format(error.message))

        try:
            dao = ConfigCustDao()
            for item in items:
                dao.add_config(item["key"], item["value"])

            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as error:
            return self.process_error(500, "fail to add notice to database: {}".format(error.message))


class ConfigPropertiesHandler(BaseHandler):
    REST_URL = "/platform/configproperties"

    @authenticated
    def get(self):
        """
        get config list as in properties format
        @API
        summary: get config list as in properties format
        notes: get config list as in properties format
        tags:
          - platform
        parameters:
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            result = ConfigCustDao().list_all_config()
            items = ["{}={}".format(_["key"], _["value"]) for _ in result if _["value"]]
            response = "\n".join(items)
            self.finish(response)
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    @authenticated
    def delete(self):
        """
        delete all platform the configs.
        @API
        summary: delete all platform the configs.
        notes: delete all platform the configs.
        tags:
          - platform
        parameters:
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            ConfigCustDao().clear()
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to delete data in database"}))
    @authenticated
    def post(self):
        """
        add a list of new config items in properties format
        @API
        summary: add a list of new config items in properties format
        notes: add a list of new config items in properties format
        tags:
          - platform
        parameters:
          -
            name: configs
            in: body
            required: true
            type: json
            description: the list of the config json item
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        body = self.request.body
        items = body.split("\n")
        items = [_.strip().split("=") for _ in items]
        try:
            dao = ConfigCustDao()
            for item in items:
                dao.add_config(item[0], item[1])

            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as error:
            return self.process_error(500, "fail to add notice to database: {}".format(error.message))


class ConfigHandler(BaseHandler):
    REST_URL = "/platform/config/{key}"

    @authenticated
    def get(self, key):
        """
        get config by its key
        @API
        summary: get config by its key
        notes: get config by its key
        tags:
          - platform
        parameters:
          -
            name: key
            in: path
            required: true
            type: string
            description: the key of the config item
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            result = ConfigCustDao().get_config_by_key(key)
            if result:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [result]}))
            else:
                self.process_error(404, "not found")
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    def delete(self, key):
        """
        delete config by its key
        @API
        summary: delete config by its key
        notes: delete config by its key
        tags:
          - platform
        parameters:
          -
            name: key
            in: path
            required: true
            type: string
            description: the key of the config item
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            ConfigCustDao().remove_config(key)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to delete data in database"}))

    @authenticated
    def post(self, key):
        """
        add a new config
        
        @API
        summary: add a new config
        notes: add a new config
        tags:
          - platform
        parameters:
          -
            name: value
            in: body
            required: true
            type: string
            description: the json of the config item
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        body = self.request.body

        try:
            dao = ConfigCustDao()
            dao.add_config(key, body)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as error:
            return self.process_error(500, "fail to add notice to database: {}".format(error.message))
