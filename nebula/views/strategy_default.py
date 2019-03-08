#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging
import traceback

from threathunter_common.util import json_dumps, millis_now
from nebula_meta.model import Strategy

from .base import BaseHandler
from ..dao.strategy_dao import StrategyDefaultDao

from nebula_strategy.generator.online_gen import gen_variables_from_strategy
from nebula.dao.user_dao import authenticated

logger = logging.getLogger('nebula.api.strategy_default')


class StrategyListHandler(BaseHandler):
    REST_URL = "/default/strategies"

    @authenticated
    def get(self):
        """
        list proper strategies
        
        @API
        summary: get proper strategy
        notes: "get strategies belong to some app or have some specific status"
        tags:
          - default
        parameters:
          -
            name: app
            in: query
            required: false
            type: string
            description: the app of the strategies that belong to
          - 
            name: status
            in: query
            required: false
            type: string
            description: the status of the strategy that should be
        produces:
          - application/json
        """
        app = self.get_argument("app", default="")
        status = self.get_argument("status", default="")
        self.set_header('content-type', 'application/json')
        try:
            result = StrategyDefaultDao().list_all_strategies()
            if app:
                result = filter(lambda s: s.app == app or s.app == "__all__", result)

            if status:
                result = filter(lambda s: s.status == status, result)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": [_.get_dict() for _ in result]}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    @authenticated
    def delete(self):
        """
        delete proper strategies
        
        @API
        summary: delete proper strategies
        notes: delete strategies belong to some app
        tags:
          - default
        parameters:
          -
            name: app
            in: query
            required: false
            type: string
            description: the app of the strategies that belong to
        produces:
          - application/json
        """
        app = self.get_argument("app", default="")
        self.set_header('content-type', 'application/json')
        try:
            StrategyDefaultDao().delete_strategy_list_by_app(app)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to delete data in database"}))

    @authenticated
    def post(self):
        """
        add or modify a list of strategies
        
        @API
        summary: add or modify a list of strategies
        notes: add new strategies or modify existing strategies
        tags:
          - default
        parameters:
          -
            name: strategies
            in: body
            required: true
            type: json
            description: the list of the strategy json
        produces:
          - application/json   
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body
        try:
            strategies = [Strategy.from_dict(_) for _ in json.loads(body)]
        except Exception as err:
            return self.process_error(400, "invalid request body: {}".format(err.message))

        for _ in strategies:
            # add current time as version, for backwards compatability
            _["version"] = millis_now()

        try:
            for s in strategies:
                gen_variables_from_strategy(s, effective_check=False)

            for s in strategies:
                s.version = millis_now()

            dao = StrategyDefaultDao()
            for s in strategies:
                dao.add_strategy(s)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            traceback.print_exc()
            return self.process_error(500, err.message)


class StrategyQueryHandler(BaseHandler):
    REST_URL = "/default/strategies/strategy/{app}/{name}"

    @authenticated
    def get(self, app, name):
        """
        get a specific strategy
        
        @API
        summary: get a specific strategy
        notes: get an strategy according to its app and name
        tags:
          - default
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: the app of the strategy
          -
            name: name
            in: path
            required: true
            type: string
            description: the name of the strategy
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        try:
            result = StrategyDefaultDao().get_strategy_by_app_and_name(app, name)
            if result:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [result.get_dict()]}))
            else:
                self.finish(json_dumps({"status": 404, "msg": "not exist"}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    @authenticated
    def delete(self, app, name):
        """
        delete strategy by its name and app
        @API
        summary: delete strategy by its name and app
        notes: delete an strategy by its name and app
        tags:
          - default
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: the app of the strategy
          -
            name: name
            in: path
            required: true
            type: string
            description: the name of the strategy
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        try:
            StrategyDefaultDao().delete_strategy_by_app_and_name(app, name)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

    @authenticated
    def post(self, app, name):
        """
        add or modify a specific strategy

        @API
        summary: add or modify a specific strategy
        notes: add or modify an strategy according to its app and name
        tags:
          - default
        parameters:
          -
            name: app
            in: path
            required: true
            type: string
            description: the app of the strategy
          -
            name: name
            in: path
            required: true
            type: string
            description: the name of the strategy
          -
            name: strategy
            in: body
            required: true
            type: json
            description: the json of the strategy
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        body = self.request.body

        # add current time as version, for backwards compatability
        body["version"] = millis_now()

        try:
            new_strategy = Strategy.from_json(body)
        except Exception as err:
            return self.process_error(400, "invalid request content: {}".format(err.message))

        try:
            gen_variables_from_strategy(new_strategy, effective_check=False)
            new_strategy.version = millis_now()
            StrategyDefaultDao().add_strategy(new_strategy)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            logger.error(err)
            self.process_error(500, "fail to add meta to database")


status_set = {"inedit", "online", "outline", "test"}
status_transfer = {
    "inedit": ["test"],
    "test": ["inedit", "online"],
    "online": ["outline"],
    "outline": ["inedit", "online"],
}


def isStatusChangeAllowed(old_status, new_status):
    if old_status not in status_set:
        return False

    if new_status not in status_set:
        return False

    if new_status not in status_transfer[old_status]:
        return False

    return True


class StrategyStatusHandler(BaseHandler):
    REST_URL = "/default/strategies/changestatus/"

    @authenticated
    def get(self):
        """
        change status of one strategy
        
        @API
        summary: add or modify a specific strategy
        notes: add or modify an strategy according to its app and name
        tags:
          - default
        parameters:
          -
            name: app
            in: query
            required: true
            type: string
            description: the app of the strategy
          -
            name: name
            in: query
            required: true
            type: string
            description: the name of the strategy
          -
            name: newstattus
            in: query
            required: true
            type: string
            description: the new status of the strategy
        produces:
          - application/json        
        """
        self.set_header('content-type', 'application/json')
        app = self.get_argument("app", "")
        name = self.get_argument("name", "")
        newstatus = self.get_argument("newstatus", "")
        if not app or not name or not newstatus:
            return self.process_error(400, "the request parameter is invalid")

        try:
            while True:
                dao = StrategyDefaultDao()
                s = dao.get_strategy_by_app_and_name(app, name)
                if not s:
                    return self.process_error(404, "the strategy doesn't exist")
                oldstatus = s.status
                if not isStatusChangeAllowed(oldstatus, newstatus):
                    return self.process_error(400, "the status transfer is not allowed")

                dao.change_status(app, name, oldstatus, newstatus)
                s = dao.get_strategy_by_app_and_name(app, name)
                if s.status == newstatus:
                    return self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))

                # not successful, retry
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

