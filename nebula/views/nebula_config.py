#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import traceback
from traceback import print_exc

from flask import json

from .base import BaseHandler
from nebula.dao.user_dao import authenticated
from threathunter_common.util import json_dumps, millis_now, unicode_obj, text
from nebula_strategy.generator.online_gen import gen_variables_from_strategy
from ..dao.DBDataCache import DBDataContext
from ..dao.event_model_dao import EventModelCustDao
from ..dao.variable_model_dao import VariableModelCustDao
from nebula_meta.variable_model import get_variable_from_registry, VariableModel
from nebula_meta.variable_filter import Filter

logger = logging.getLogger('nebula.api.variable')

context = DBDataContext(5000)

class NebulaUIEventsHandler(BaseHandler):
    REST_URL = "/nebula/events"

    # @authenticated
    def get(self):
        """
        get nebula ui events, name 不以下划线打头的events
        
        @API
        summary: get nebula ui events
        notes: get an nebula ui events that user can use as data source
        tags:
          - nebula
        parameters:
        produces:
          - application/json        
        """

        self.set_header('content-type', 'application/json')
        try:
            variable_models = VariableModelCustDao().list_all_models()
            variable_models = filter(lambda v: v.type in {'event', 'filter'}, variable_models)
            variable_models = filter(lambda v: not v.name.endswith('DELAY'), variable_models)

            result = list()
            for v in variable_models:
                record = dict()
                record['name'] = v.name
                record['remark'] = v.visible_name
                fields = []
                record['fields'] = fields
                for p in v.get_properties():
                    fields.append({
                        'name': p.name,
                        'type': p.type,
                        'remark': p.visible_name
                    })

                result.append(record)

            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            logger.error(err)
            self.process_error(500, err.message)


class NebulaUIVariablesHandler(BaseHandler):
    REST_URL = "/nebula/variables"

    @authenticated
    def get(self):
        """
        get nebula ui variables, name 不以下划线打头的variable
        
        @API
        summary: get nebula ui variables
        notes: get nebula ui variables that user can use
        tags:
          - nebula
        parameters:
        produces:
          - application/json        
        """

        self.set_header('content-type', 'application/json')
        try:
            variables = context.nebula_ui_variables
            result = []
            for v in variables:
                if v.module not in {"realtime", "profile"}:
                    continue
                if not v.visible_name:
                    continue
                record = {}
                record["name"] = v.name
                record["remark"] = v.remark
                record["display_name"] = v.visible_name or v.remark
                result.append(record)

            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            traceback.print_exc()
            self.process_error(500, err.message)


class VariableGlossaryHandler(BaseHandler):
    REST_URL = "/nebula/glossary"

    @authenticated
    def get(self):
        """
        获取所有数据字典接口
        
        @API
        summary: get nebula all event glossary
        notes: get nebula all event glossary
        tags:
          - nebula
        parameters:
        produces:
          - application/json        
        """

        self.set_header('content-type', 'application/json')
        try:
            variables = context.nebula_events
            result = []
            for var in variables:
                record = dict()
                record["name"] = var.name
                record["app"] = var.app
                record["remark"] = var.remark
                record['srcId'] = None
                src = var.source[0] if var.source else {}
                if src and src['name'].startswith('_'):
                    continue

                record['srcId'] = [src]
                record["fields"] = []
                for p in var.properties:
                    remark = p.visible_name
                    record["fields"].append({
                        "name": p.name,
                        "type": p.type,
                        "remark": remark,
                    })

                result.append(record)

            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            print_exc()
            logger.error(err)
            self.process_error(500, err.message)


class NebulaOnlineVariablesHandler(BaseHandler):
    REST_URL = "/nebula/online/variables"

    @authenticated
    def get(self):
        """
        get nebula online variables
        
        @API
        summary: get nebula online variables
        notes: get nebula online variables for online kv
        tags:
          - nebula
        parameters:
        produces:
          - application/json        
        """

        self.set_header('content-type', 'application/json')
        # try:
        if True:
            default_variables = VariableModelCustDao().list_all_models()
            default_variables = filter(lambda model: model.module in {'base', 'realtime'}, default_variables)

            # hack for distinct count
            for dv in default_variables:
                if 'distinct' in dv.function.method and dv.function.object_type == 'string':
                    # 增加一个不为空的field
                    function = dv.function
                    not_null_filter = Filter(function.source, function.object, function.object_type,
                                             function.object_subtype, '!=', '', 'simple', '', [])
                    if dv.filter and not dv.filter.is_empty():
                        dv.filter = Filter('', '', '', '', '', '', 'and', '',
                                           [dv.filter.get_dict(), not_null_filter.get_dict()])
                    else:
                        dv.filter = Filter('', '', '', '', '', '', 'and', '', [not_null_filter.get_dict()])
            # end of hack

            all_generated_variables = []
            all_used_variables = []
            strategies = context.nebula_strategies
            strategies = filter(lambda s: (s.status in ["test", "online"] and
                                           s.start_effect <= millis_now() <= s.end_effect), strategies)
            for s in strategies:
                generated_variables, used_variables = gen_variables_from_strategy(s, effective_check=True)
                all_generated_variables.extend(generated_variables)
                all_used_variables.extend(used_variables)

            # recursively calcuated all_used_variables:
            while True:
                new_used_variable_found = False
                for used_variable_name in all_used_variables[:]:
                    for source in get_variable_from_registry('nebula', used_variable_name).source:
                        if source['name'] not in all_used_variables:
                            all_used_variables.append(source['name'])
                            new_used_variable_found = True
                if not new_used_variable_found:
                    break

            default_variables = [_ for _ in default_variables if _.name in all_used_variables or
                                 _.type in {'event', 'filter'}]
            result = default_variables + all_generated_variables
            result = [_.get_dict() for _ in result]
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        # except Exception as err:
        #     self.process_error(500, err.message)


class NebulaOnlineEventsHandler(BaseHandler):
    REST_URL = "/nebula/online/events"

    @authenticated
    def get(self):
        """
        get nebula online events
        
        @API
        summary: get nebula online events
        notes: get nebula online events for online kv
        tags:
          - nebula
        parameters:
        produces:
          - application/json        
        """

        self.set_header('content-type', 'application/json')
        try:
            result = EventModelCustDao().list_all_models()
            result = [_.get_dict() for _ in result]
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": result}))
        except Exception as err:
            self.process_error(500, err.message)


if __name__ == "__main__":
    c = DBDataContext(5000)
    c.check()
    c.nebula_online_variables
