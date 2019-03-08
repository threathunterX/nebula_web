#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from .base import BaseHandler
from nebula.dao.user_dao import authenticated
from threathunter_common.event import Event
from threathunter_common.util import json_dumps, millis_now
#from nebula.middleware.tornado_rest_swagger.restutil import rest_class, rest_method
from nebula.services import babel

logger = logging.getLogger('nebula.api.variable_value')

keyValueClient = babel.get_key_value_client()
globalValueClient = babel.get_global_value_client()
topValueClient = babel.get_top_value_client()
keyTopValueClient = babel.get_key_top_value_client()


class VariableValueQueryHandler(BaseHandler):
    REST_URL = "/platform/variabledata/latest/{name}"

    @authenticated
    def get(self, name):
        """
        get variable value
        
        @API
        summary: get variable value
        notes: get the latest value of given variable on special key
        tags:
          - platform
        parameters:
          -
            name: name
            in: path
            required: true
            type: string
            description: the name of the variable
          - 
            name: key
            in: query
            required: false
            type: string
            description: the key of the variable
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            key = self.get_argument("key", "")
            property_values = dict()
            property_values["count"] = 1
            property_values["varnames"] = [name]

            if key:
                request = Event("__all__", "_global__variablekeyvalue_request", key, millis_now(), property_values)
                response = keyValueClient.send(request, key, block=False, timeout=3)
                if response[0]:
                    value = response[1].property_values.get("varvalues")[0]
                    self.finish(json_dumps({"status": 0, "msg": "ok", "values": [value]}))
                else:
                    return self.process_error(404, "the value doesn't exist")
            else:
                #broadcast
                request = Event("__all__", "_global__variableglobalvalue_request", key, millis_now(), property_values)
                response = globalValueClient.send(request, "nebula", block=False, timeout=3)
                if response[0]:
                    value = 0
                    for resultEvent in response[1]:
                        if resultEvent.property_values.get("count") > 0 and resultEvent.property_values.get("varvalues")[0] is not None:
                            value += resultEvent.property_values.get("varvalues")[0]
                    self.finish(json_dumps({"status": 0, "msg": "ok", "values": [{name: value}]}))
                else:
                    return self.process_error(404, "the value doesn't exist")

        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get variable data"}))
        finally:
            pass


class VariableValueListHandler(BaseHandler):
    REST_URL = "/platform/variabledata/list/{key}"

    @authenticated
    def get(self, key):
        """
        get values of all the variable of a specific key
        
        @API
        summary: get values of all the variable of a specific key
        notes: get the latest value of given variable on special key
        tags:
          - platform
        parameters:
          - 
            name: key
            in: path
            required: true
            type: string
            description: the key of the variable
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            property_values = dict()
            property_values["count"] = 0
            property_values["varnames"] = []

            if key:
                request = Event("__all__", "_global__variablekeyvalue_request", key, millis_now(), property_values)
                response = keyValueClient.send(request, key, block=False, timeout=3)
                if response[0]:
                    value = []
                    if response[1] and response[1].property_values["count"]:
                        value = {response[1].property_values["varnames"][i]: response[1].property_values["varvalues"][i]
                                 for i in range(response[1].property_values["count"])}
                    self.finish(json_dumps({"status": 0, "msg": "ok", "values": [value]}))
                else:
                    return self.process_error(404, "the value doesn't exist")

        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get variable data: {}".format(err.message)}))
        finally:
            pass

class VariableValueTopHandler(BaseHandler):
    REST_URL = "/platform/variabledata/top/{name}"

    @authenticated
    def get(self, name):
        """
        get top values of one variable
        
        @API
        summary: get top values of one variable
        notes: get variable top values
        tags:
          - platform
        parameters:
          -
            name: name
            in: path
            required: true
            type: string
            description: the name of the variable
          - 
            name: limit
            in: query
            required: false
            type: int
            description: the max number of the returned records.
        produces:
          - application/json
        """
        try:
            self.set_header('content-type', 'application/json')
            limit = int(self.get_argument("limit", 10))

            request = Event("__all__", "variabletopvalue_request", "", millis_now(), {"varname": name})
            response = topValueClient.send(request, "", block=False, timeout=3)
            if response[0]:
                data = {}
                for response_event in response[1]:
                    if not response_event.property_values["count"]:
                        continue
                    for i in range(response_event.property_values["count"]):
                        data[response_event.property_values["keynames"][i]] = response_event.property_values["varvalues"][i]
                value = list()
                for k, v in data.iteritems():
                    value.append((k, v))
                value.sort(cmp=lambda a, b: cmp(b[1], a[1]))
                value = value[:limit]
                value = [{k: v} for k, v in value]
                return self.finish(json_dumps({"status": 0, "msg": "ok", "values": value}))

            else:
                return self.process_error(404, "the value doesn't exist")
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get variable data: {}".format(err.message)}))


class VariableValueKeyTopHandler(BaseHandler):
    REST_URL = "/platform/variabledata/keytop/{name}"

    @authenticated
    def get(self, name):
        """
        get top values of one variable on special keys
        
        @API
        summary: get top values of one variable on special keys
        notes: get top values of variables whose key match special pattern
        tags:
          - platform
        parameters:
          -
            name: name
            in: path
            required: true
            type: string
            description: the name of the variable
          - 
            name: keypattern
            in: query
            required: true
            type: string
            description: the pattern of the variable key
          - 
            name: limit
            in: query
            required: false
            type: int
            description: the max number of the returned records.
        produces:
          - application/json
        """

        try:
            self.set_header('content-type', 'application/json')
            keypattern = self.get_argument("keypattern")
            limit = int(self.get_argument("limit", 10))

            property_values = dict()
            property_values["keypattern"] = keypattern
            property_values["varname"] = name

            request = Event("__all__", "_global__variablekeytopvalue_request", "", millis_now(), property_values)
            response = keyTopValueClient.send(request, "", block=False, timeout=3)
            if response[0]:
                data = {}
                for response_event in response[1]:
                    if not response_event.property_values["count"]:
                        continue
                    for i in range(response_event.property_values["count"]):
                        data[response_event.property_values["keynames"][i]] = response_event.property_values["varvalues"][i]
                value = list()
                for k, v in data.iteritems():
                    value.append((k, v))
                value.sort(cmp=lambda a, b: cmp(b[1], a[1]))
                value = value[:limit]
                value = value[::-1]
                value = [{k: v} for k, v in value]
                return self.finish(json_dumps({"status": 0, "msg": "ok", "values": value}))

            else:
                return self.process_error(404, "the value doesn't exist")
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get variable data"}))
        finally:
            pass

