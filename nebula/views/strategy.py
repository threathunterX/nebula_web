#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import traceback

from threathunter_common.util import json_dumps, millis_now
from nebula_meta.model import Strategy

from .base import BaseHandler
#from nebula.middleware.tornado_rest_swagger.restutil import rest_class, rest_method
from ..dao.strategy_dao import StrategyCustDao
from ..dao.tag import TagDao
from nebula.dao import cache
from ..dao.user_dao import authenticated, is_auth_internal
from nebula.dao.group_dao import GroupPermissionDao
from nebula_strategy.generator.online_gen import *

logger = logging.getLogger('nebula.api.strategy')


class TagQueryHandler(BaseHandler):
    REST_URL = '/nebula/tag/{tag_id}'
    
    @authenticated
    def get(self, tag_id):
        """
        根据id获取tag
        
        @API
        summary: 根据id获取tag
        notes: 根据id获取tag
        tags:
          - nebula
        parameters:
          -
            name: tag_id
            in: path
            required: true
            type: int
            description: the id of the tag
        produces:
          - application/json
        """
        try:
            tag_id = int(tag_id)
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "invalid tag id"}))
        dao = TagDao()
        try:
            result = dao.get_tag(tag_id)
            if result:
                self.finish(json_dumps({"status": 0, "msg": "ok", "values": [result, ]}))
            else:
                self.finish(json_dumps({"status": 404, "msg": "not exist"}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))
    
class TagsHandler(BaseHandler):
    REST_URL = "/nebula/tags"
    
    @authenticated
    def get(self):
        """
        获取所有的tags

        @API
        summary: 获取所有的tags
        notes: 获取所有的tags
        tags:
          - nebula
        produces:
          - application/json
        """
        try:
            tags = TagDao().list_all_tags()
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": tags}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))
        
    @authenticated
    def post(self):
        """
        新增tag
        
        @API
        summary: add a list of tags
        notes: add new tags
        tags:
          - nebula
        parameters:
          -
            name: tags
            in: body
            required: true
            type: json
            description: the list of the tags json
        produces:
          - application/json        
        """
        body = self.request.body
        try:
            tags = [ dict(app='nebula', name=_['name']) for _ in json.loads(body)]
        except Exception as err:
            return self.process_error(400, "invalid request body: {}".format(err.message))

        try:
            dao = TagDao()
            for t in tags:
                dao.add_tag(t)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except Exception as err:
            traceback.print_exc()
            return self.process_error(500, err.message)

class StrategyWeighHandler(BaseHandler):
    REST_URL = "/nebula/strategyweigh"
    
    @authenticated
    def get(self):
        """
        获取策略的id、场景、权重、标签信息
        {
          "status": 0,
          "msg": "ok",
          "values": [ {'app':.., 'name':.., 'id':.., 'tags':.., 'scene_name':.., 'scene_score':..}]
        }
        @API
        summary: "获取策略的id、场景、权重、标签信息"
        notes: "获取策略的id、场景、权重、标签信息"
        tags:
          - nebula
        produces:
          - application/json
        """
        try:
            if cache.Strategy_Weigh_Cache is None:
                from nebula.dao.strategy_dao import init_strategy_weigh
                init_strategy_weigh()
            self.finish(json_dumps({"status": 0, "msg": "ok", "values":cache.Strategy_Weigh_Cache.values()}))
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database"}))

class StrategyListHandler(BaseHandler):
    REST_URL = "/nebula/strategies"

    @authenticated
    def get(self):
        """
        list proper strategies
        
        @API
        summary: get proper strategy
        notes: "get strategies belong to some app or have some specific status"
        tags:
          - nebula
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
        auth = self.get_argument('auth', default='')
        self.set_header('content-type', 'application/json')
        try:
            # list_all_strategies 新增app status groups 查询参数 @todo
            strategies = StrategyCustDao().list_all_strategies()
            if app:
                strategies = filter(lambda s: s.app == app or s.app == "__all__", strategies)

            if status:
                strategies = filter(lambda s: s.status == status, strategies)

            # sort by alpha order
            strategies.sort(key=lambda x: x.name)
            
            # 超级管理员不能查看策略
            # 管理员可以查看所有策略
            # 普通用户组可以查看本组策略，及允许查看的用户组策略
            # 如果是内部模块，则返回所有策略
            if auth and is_auth_internal(auth):
                strategies = [s.get_dict() for s in strategies]
                self.finish(json_dumps({"status": 200, "msg": "ok", "values": strategies}))
            elif self.group.is_root():
                self.process_error(-1, "root用户组没有权限查询策略")
            elif self.group.is_manager():
                strategies = [s.get_dict() for s in strategies]
                self.finish(json_dumps({"status": 200, "msg": "ok", "values": strategies}))
            else:
                view_strategy = GroupPermissionDao().get_group_strategy_block(self.group.id)
                be_block_groups_ids = view_strategy.get('be_blocked', [])

                # 筛选被禁止查看的用户组策略
                strategies = [_.get_dict() for _ in strategies if _.group_id not in be_block_groups_ids]
                for s in strategies:
                    s.pop('score')

                self.finish(json_dumps({"status": 200, "msg": "ok", "values": strategies}))
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
          - nebula
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
        # @1. 只能删自己组的和自己创建出来的用户组内的 @todo
        app = self.get_argument("app", default="")
        self.set_header('content-type', 'application/json')
        try:
            StrategyCustDao().delete_strategy_list_by_app(app)
            self.finish(json_dumps({"status": 200, "msg": "ok", "values": []}))
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
          - nebula
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
            # root用户组不可以创建策略
            # manager用户组、普通用户组可以创建策略
            if self.group.is_root():
                return self.process_error(-1, 'root用户组没有权限创建策略')

            strategies = []
            for _ in json.loads(body):
                _["group_id"] = self.group.id
                strategies.append(Strategy.from_dict(_))
        except Exception as err:
            return self.process_error(400, "invalid request body: {}".format(err.message))

        for _ in strategies:
            # add current time as version, for backwards compatability
            _.version = millis_now()

        try:
            for s in strategies:
                gen_variables_from_strategy(s, effective_check=False)

            for s in strategies:
                s.version = millis_now()

            dao = StrategyCustDao()
            for s in strategies:
                dao.add_strategy(s)
            self.finish(json_dumps({"status": 200, "msg": "ok", "values": []}))
        except Exception as err:
            traceback.print_exc()
            return self.process_error(500, err.message)

class StrategyBatchDelHandler(BaseHandler):
    REST_URL = "/nebula/strategies/delete"

    @authenticated
    def put(self):
        """
        batch delete strategies
        
        @API
        summary: batch delete strategies
        notes: delete strategies according to its app and name
        tags:
          - nebula
        parameters:
          -
            name: strategies
            in: body
            required: true
            type: json
            description: the list of strategies' app and name
        produces:
          - application/json        
        """
        # 所有策略的修改都要检查 @todo
        self.set_header('content-type', 'application/json')
        body = self.request.body
        request_data = json.loads(body)
        for d in request_data:
            if not d.get("app") or not d.get("name"):
                return self.process_error(400, u"列表中每项字典的app, name字段有缺失。")

        try:
            fail_msgs = []
            dao = StrategyCustDao()
            for d in request_data:
                app = d.get("app")
                name = d.get("name")
                try:
                    StrategyCustDao().delete_strategy_by_app_and_name(app, name)
                except Exception:
                    fail_msgs.append(u"策略app: %s, name: %s 删除失败: %s 。" %
                                     (app, name, traceback.format_exc()))
                    continue
            if len(fail_msgs) < len(request_data):
                self.finish(json_dumps({"status": 0, "msg": "\n".join(fail_msgs), "values": []}))
            else:
                self.finish(json_dumps({"status": 400, "msg": "\n".join(fail_msgs)}))
        except Exception:
            logger.error(traceback.format_exc())
            self.finish(json_dumps({"status": -1, "msg": "fail to delete strategies from database, %s" % traceback.format_exc()}))

class StrategyQueryHandler(BaseHandler):
    REST_URL = "/nebula/strategies/strategy/{app}/{name}"

    @authenticated
    def get(self, app, name):
        """
        get a specific strategy
        
        @API
        summary: get a specific strategy
        notes: get an strategy according to its app and name
        tags:
          - nebula
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
            # get_strategy_by_app_and_name 增加group_ids 列表查询字段
            strategy = StrategyCustDao().get_strategy_by_app_and_name(app, name).get_dict()

            # 超级管理员不能查看策略
            # 管理员可以查看所有策略
            # 普通用户组可以查看本组策略，及允许查看的用户组策略
            if self.group.is_root():
                self.process_error(-1, "root用户组没有权限查询策略")
            elif self.group.is_manager():
                self.finish(json_dumps({"status": 200, "msg": "ok", "values": [strategy]}))
            else:
                view_strategy = GroupPermissionDao().get_group_strategy_block(self.group.id)
                be_block_groups_ids = view_strategy.get('be_blocked', [])

                # 筛选被禁止查看的用户组策略
                # 只有管理员可以看见权重
                if strategy['group_id'] not in be_block_groups_ids:
                    strategy.pop('score')
                else:
                    strategy = {}

                self.finish(json_dumps({"status": 200, "msg": "ok", "values": [strategy]}))
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
          - nebula
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
        #所有策略的修改都要检查 @todo
        try:
            StrategyCustDao().delete_strategy_by_app_and_name(app, name)
            self.finish(json_dumps({"status": 200, "msg": "ok", "values": []}))
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
          - nebula
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
        #所有策略的修改都要检查 @todo
        self.set_header('content-type', 'application/json')
        body = self.request.body

        # add current time as version, for backwards compatability
        body["version"] = millis_now()
        body["group_id"] = self.group.id
        try:
            new_strategy = Strategy.from_json(body)
        except Exception as err:
            return self.process_error(400, "invalid request content: {}".format(err.message))

        try:
            gen_variables_from_strategy(new_strategy, effective_check=False)
            new_strategy.version = millis_now()
            StrategyCustDao().add_strategy(new_strategy)
            self.finish(json_dumps({"status": 200, "msg": "ok", "values": []}))
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
    REST_URL = "/nebula/strategies/changestatus/"

    @authenticated
    def post(self):
        """
        change status of one strategy
        
        @API
        summary: add or modify a specific strategy
        notes: add or modify an strategy according to its app and name
        tags:
          - nebula
        parameters:
          -
            name: strategies
            in: body
            required: true
            type: json
            description: the list of dict include app, name, newstatus args
        produces:
          - application/json        
        """
        # 所有策略的修改都要检查 @todo
        self.set_header('content-type', 'application/json')
        body = self.request.body
        request_data = json.loads(body)
        for d in request_data:
            if not d.get("app") or not d.get("name") or not d.get("newstatus"):
                return self.process_error(400, u"列表中每项参数app, name 和 newstatus有缺失。")

        try:
            fail_msgs = []
            dao = StrategyCustDao()

            for d in request_data:
                app = d.get("app")
                name = d.get("name")
                newstatus = d.get("newstatus")
                while True:
                    s = dao.get_strategy_by_app_and_name(app, name)
                    if not s:
                        fail_msgs.append(u"app: %s, name: %s 的策略不存在。" %
                                         (app, name))
                        break
                    oldstatus = s.status
                    if not isStatusChangeAllowed(oldstatus, newstatus):
                        fail_msgs.append(u"app: %s, name: %s 的策略状态不能从 %s 转换为 %s 。" % (app, name, oldstatus, newstatus) )
                        break
                    dao.change_status(app, name, oldstatus, newstatus)
                    s = dao.get_strategy_by_app_and_name(app, name)
                    if s.status == newstatus:
                        break
                    # not successful, retry
            if len(fail_msgs) < len(request_data):
                self.finish(json_dumps({"status": 0, "msg": "\n".join(fail_msgs), "values": []}))
            else:
                self.finish(json_dumps({"status": 400, "msg": "\n".join(fail_msgs)}))
        except Exception:
            logger.error(traceback.format_exc())
            self.finish(json_dumps({"status": -1, "msg": "fail to get data from database, %s" % traceback.format_exc()}))

