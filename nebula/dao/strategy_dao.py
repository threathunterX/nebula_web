#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging

from threathunter_common.util import millis_now
from nebula_meta.model import Strategy
from .base_dao import BaseDao, BaseDefaultDao
from . import cache
from ..models.default import StrategyDefaultModel as Model, StrategyDefaultModel
from ..models import StrategyCustModel as CustModel

logger = logging.getLogger('nebula.dao.strategy')

#TODO more nodes
def is_strategy_weigh_cache_avail():
    if cache.Strategy_Weigh_Cache is None:
        logger.warn('strategy weigh cache is None')
        return False
    return True

def add_strategy_weigh_cache(s):
    if not is_strategy_weigh_cache_avail():
        return

    new_weigh = get_strategy_weigh(s)
    cache.Strategy_Weigh_Cache[new_weigh['name']] = new_weigh


def delete_strategy_weigh_cache(app=None, name=None):
    # @todo
    if not is_strategy_weigh_cache_avail():
        return
    weighs = cache.Strategy_Weigh_Cache.values()

    if app:
        if name:
            weighs = list(filter(lambda w: w['app'] != app or w['name'] != name, weighs))
        else:
            weighs = list(filter(lambda x: x['app'] != app, weighs))

        cache.Strategy_Weigh_Cache = dict((weigh['name'], weigh) for weigh in weighs)
    else:
        cache.Strategy_Weigh_Cache = dict()


def get_strategy_weigh(s):
    blacklist_info = None
    config = json.loads(s.config)
    terms = config.get('terms', [])
    for term in terms:
        if term['left']['subtype'] == 'setblacklist':
            blacklist_info = term['left']['config']
            if blacklist_info is None:
                logger.error(u'app:%s, name:%s 的策略没有设置黑名单的配置', s.app, s.name)
                    
            return {
            'app': s.app,
            'name': s.name,
            'tags': (s.tags or '').split(','),
            'category': s.category,
            'score': s.score,
            'expire': s.endeffect,
            'remark': s.remark,
            'test': True if s.status == 'test' else False,
            'scope': term.get('scope', ''),
            'checkpoints': blacklist_info.get('checkpoints', ''),
            'checkvalue': blacklist_info.get('checkvalue', ''),
            'checktype': blacklist_info.get('checktype', ''),
            'decision': blacklist_info.get('decision', ''),
            'ttl': blacklist_info.get('ttl', 300)
            }

def update_strategy_weigh_cache(s):
    if not is_strategy_weigh_cache_avail():
        return
        
    new_weigh = get_strategy_weigh(s)
    cache.Strategy_Weigh_Cache[new_weigh['name']] = new_weigh

def init_strategy_weigh():
    strategies = StrategyCustDao().list_all_strategies_raw()
    result = dict()
    for s in strategies:
        weigh = get_strategy_weigh(s)
        if not weigh:
            continue
        result[weigh['name']] = weigh
    cache.Strategy_Weigh_Cache = result

class StrategyDefaultDao(BaseDefaultDao):

    cached_online_strategies = set()
    last_cache_update_ts = 0

    def get_strategy_by_app_and_name(self, app, name):
        """
        get strategy by app and name.
        """

        query = self.session.query(Model)
        result = query.filter(Model.name == name, Model.app == app).first()
        if result:
            return result.to_strategy()

    def _get_model_by_app_and_name(self, app, name):
        query = self.session.query(Model)
        return query.filter(Model.name == name, Model.app == app).first()

    def get_strategy_by_id(self, id):
        """
        get strategy by id.
        """

        query = self.session.query(Model)
        result = query.filter(Model.id == id).first()
        if result:
            return result.to_strategy()

    def list_all_strategies(self):
        """
        get all strategies
        """

        query = self.session.query(Model)
        result = query.all() or []
        result = [_.to_strategy() for _ in result]
        return result

    def list_all_strategies_by_status(self, status):
        """
        get all strategies
        """

        return filter(lambda s: s.status == status, self.list_all_strategies())

    def list_all_strategies_by_app(self, app):
        """
        get all strategies
        """

        return filter(lambda s: s.app == app, self.list_all_strategies())

    def list_all_strategies_in_effect(self):
        now = millis_now()
        result = self.list_all_strategies() or []
        return filter(lambda s: s.start_effect <= now <= s.end_effect, result)

    def list_all_online_strategy_names_in_effect(self):
        now = millis_now()
        result = self.list_all_strategies() or []
        result = filter(lambda s: s.start_effect <= now <= s.end_effect and s.status == "online", result)
        result = map(lambda s: s.name, result)
        return result

    def get_cached_online_strategies(self):
        current = millis_now()
        if current - StrategyDefaultDao.last_cache_update_ts< 5000:
            return StrategyDefaultDao.cached_online_strategies

        strategies = self.list_all_online_strategy_names_in_effect()
        StrategyDefaultDao.cached_online_strategies = set(strategies)
        StrategyDefaultDao.last_cache_update_ts = millis_now()
        return StrategyDefaultDao.cached_online_strategies

    def add_strategy(self, s):
        new = StrategyDefaultModel.from_strategy(s)
        new.last_modified = millis_now()
        existing = self._get_model_by_app_and_name(s.app, s.name)
        if existing:
            # update
            new.id = existing.id
            self.session.merge(new)
            update_strategy_weigh_cache(new)
        else:
            # insert
            self.session.add(new)
            add_strategy_weigh_cache(new)
        self.session.commit()

    def change_status(self, app, name, old_status, new_status):

        result = self._get_model_by_app_and_name(app, name)

        # check whether the internal status is right
        if not result:
            return
        result_strategy = result.to_strategy()
        if result_strategy.status != old_status:
            return

        result_strategy.status = new_status
        new_model = StrategyDefaultModel.from_strategy(result_strategy)
        new_model.id = result.id
        self.session.merge(new_model)
        self.session.commit()

    def delete_strategy_by_app_and_name(self, app, name):
        query = self.session.query(Model)
        query.filter(Model.name == name, Model.app == app).delete()
        self.session.commit()
        delete_strategy_weigh_cache(app=app, name=name)

    def delete_strategy(self, s):
        self.delete_strategy_by_app_and_name(s.app, s.name)

    def delete_strategy_list_by_app(self, app):
        query = self.session.query(Model)
        if app:
            query.filter(Model.app == app).delete()
            delete_strategy_weigh_cache(app=app)
        else:
            query.filter().delete()
            delete_strategy_weigh_cache()
        self.session.commit()

    def clear(self):
        """
        clear all the records
        """

        query = self.session.query(Model)
        query.delete()
        self.session.commit()
        delete_strategy_weigh_cache()

    def count(self):
        query = self.session.query(Model)
        return query.count()

class StrategyCustDao(BaseDao):

    cached_online_strategies = set()
    last_cache_update_ts = 0

    def get_strategy_by_app_and_name(self, app, name):
        """
        get strategy by app and name. 定制的覆盖默认的strategy
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        result = self._get_model_by_app_and_name(app, name)
        if result:
            return result.to_strategy()

    def _get_model_by_app_and_name(self, app, name):
        """
        只根据key获取strategy custmize优先default
        @add within v2.0
        """
        query = self.session.query(CustModel).filter(CustModel.app == app, CustModel.name == name)
        cust_strategy =  query.first()
        if not cust_strategy:
            query = StrategyDefaultDao().session.query(Model).filter(Model.app == app, Model.name == name)
            return query.first()
        else:
            return cust_strategy
        
    def _get_cust_model_by_app_name(self, app, name):
        """
        只根据key获取定制化的strategy
        @add within v2.0
        """
        query = self.session.query(CustModel)
        return query.filter(CustModel.app == app, CustModel.name == name).first()

    def get_strategy_by_id(self, id):
        """
        get strategy by id. custmize 优先于default
        @keep 接口功能不变，含义变了 with v1.0
        """
        query = self.session.query(CustModel).filter(CustModel.id == id)
        cust_strategy =  query.first()
        if not cust_strategy:
            query = StrategyDefaultDao().session.query(Model).filter(Model.id == id)
            return query.first()
        else:
            return cust_strategy

        query = self.session.query(CustModel)
        result = query.filter(CustModel.id == id).first()
        if result:
            return result.to_strategy()

    def get_cust_strategy_by_id(self, id):
        """
        get cust strategy by id.
        @add
        """
        query = self.session.query(CustModel)
        result = query.filter(CustModel.id == id).first()
        if result:
            return result.to_strategy()
            
    def list_all_strategies_raw(self):
        """
        @new v2.0
        """
        default_query = StrategyDefaultDao().session.query(Model)
        strategies = dict( ( (_.app, _.name), _) for _ in default_query.all())
        # key: strategy obj
        cust_query = self.session.query(CustModel)
        for cq in cust_query.all():
            strategies[(cq.app, cq.name)] = cq
        return strategies.values()

    def list_all_strategies(self):
        """
        list all strategies, 取定制的和默认的strategies的合集，定制的覆盖默认的strategies
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        default_query = StrategyDefaultDao().session.query(Model)
        strategies = dict( ( (_.app, _.name), _.to_strategy()) for _ in default_query.all())
        # key: strategy obj
        cust_query = self.session.query(CustModel)
        for cq in cust_query.all():
            strategies[(cq.app, cq.name)] = cq.to_strategy()
        return strategies.values()

    def list_all_cust_strategies(self):
        """
        list all custmize strategies
        @add within v2.0
        """
        query = self.session.query(CustModel)
        result = query.all() or []
        result = [_.to_strategy() for _ in result]
        return result
        
    def list_all_strategies_by_status(self, status):
        """
        get strategies with certain status
        @keep 保持接口功能不变 with v1.0
        """
        return filter(lambda s: s.status == status, self.list_all_strategies())

    def list_all_strategies_by_app(self, app):
        """
        get strategies with certain status
        @keep 保持接口功能不变 with v1.0
        """
        return filter(lambda s: s.app == app, self.list_all_strategies())

    def list_all_strategies_in_effect(self):
        """
        get strategies not expire yet
        @keep 保持接口功能不变 with v1.0
        """
        now = millis_now()
        result = self.list_all_strategies() or []
        return filter(lambda s: s.start_effect <= now <= s.end_effect, result)

    def list_all_online_strategy_names_in_effect(self):
        """
        get online strategies not expire yet
        @keep 保持接口功能不变 with v1.0
        """
        now = millis_now()
        result = self.list_all_strategies() or []
        result = filter(lambda s: s.start_effect <= now <= s.end_effect and s.status == "online", result)
        result = map(lambda s: s.name, result)
        return result

    def get_cached_online_strategies(self):
        """
        @keep 保持接口功能不变 with v1.0
        """
        current = millis_now()
        if current - StrategyCustDao.last_cache_update_ts< 5000:
            return StrategyCustDao.cached_online_strategies

        strategies = self.list_all_online_strategy_names_in_effect()
        StrategyCustDao.cached_online_strategies = set(strategies)
        StrategyCustDao.last_cache_update_ts = millis_now()
        return StrategyCustDao.cached_online_strategies

    def add_strategy(self, s):
        """
        only add custmize strategies, just override the default strategies, not delete key's strategies entirely.
        @keep 保持接口功能不变,含义变了 with v1.0
        """
        new = CustModel.from_strategy(s)
        new.last_modified = millis_now()
        existing = self._get_cust_model_by_app_name(s.app, s.name)
        if existing:
            # update
            new.id = existing.id
            new.group_id = existing.group_id
            self.session.merge(new)
            update_strategy_weigh_cache(new)
        else:
            # insert
            self.session.add(new)
            add_strategy_weigh_cache(new)
        self.session.commit()

    def change_status(self, app, name, old_status, new_status):
        """
        only change custmize strategies
        @keep 保持接口功能变了,含义变了 with v1.0
        """
        result = self._get_model_by_app_and_name(app, name)

        # check whether the internal status is right
        if not result:
            return
        result_strategy = result.to_strategy()
        if result_strategy.status != old_status:
            return

        result_strategy.status = new_status
        new_model = CustModel.from_strategy(result_strategy)
        new_model.id = result.id
        self.session.merge(new_model)
        self.session.commit()
        update_strategy_weigh_cache(new_model)

    def delete_strategy_by_app_and_name(self, app, name):
        """
        现在只能删除custmize的strategy
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(CustModel)
        query.filter(CustModel.name == name, CustModel.app == app).delete()
        self.session.commit()
        delete_strategy_weigh_cache(app=app, name=name)
        
    def delete_strategy(self, s):
        """
        现在只能删除custmize的strategy
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        self.delete_strategy_by_app_and_name(s.app, s.name)

    def delete_strategy_list_by_app(self, app):
        """
        现在只能删除custmize的strategy
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(CustModel)
        if app:
            query.filter(CustModel.app == app).delete()
            delete_strategy_weigh_cache(app=app)
        else:
            query.filter().delete()
            delete_strategy_weigh_cache()
        self.session.commit()

    def clear(self):
        """
        clear all Custmize strategy, reset to default strategy(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(CustModel)
        query.delete()
        self.session.commit()
        delete_strategy_weigh_cache()

    def count(self):
        """
        只获取custmize 的strategy个数
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(CustModel)
        return query.count()

if __name__ == "__main__":
    js = """{
        "app": "nebula",
        "name": "test_strategy",
        "remark": "test strategy",
        "version": 1430694092730,
        "status": "inedit",
        "createtime": 1430693092730,
        "modifytime": 1430693092730,
        "starteffect": 1430693092730,
        "endeffect": 1431095092730,
        "terms": [
            {
                "left":
                    {
                        "type": "event",
                        "subtype": "",
                        "config": {
                            "event": ["nebula", "http_static"],
                            "field": "c_bytes"
                        }
                    },
                "op": "between",
                "right":
                    {
                        "type": "constant",
                        "subtype": "",
                        "config": {
                            "value": "1,200"
                        }
                    }
            },
            {
                "left":
                    {
                        "type": "func",
                        "subtype": "count",
                        "config": {
                            "sourceevent": ["nebula", "http_dynamic"],
                            "condition": [
                                {
                                    "left": "method",
                                    "op": "==",
                                    "right": "get"
                                }
                            ],
                            "interval": 300,
                            "algorithm": "count",
                            "groupby": ["c_ip", "uri_stem"],
                            "trigger": {
                                "event": ["nebula", "http_static"],
                                "keys": ["c_ip","uri_stem"]
                            }
                        }
                    },
                "op": "<",
                "right":
                    {
                        "type": "constant",
                        "subtype": "",
                        "config": {
                            "value": "2"
                        }
                    }
            }
        ]

    }"""

    dao = StrategyDefaultDao()
    strategy = Strategy.from_json(js)
    print StrategyDefaultModel.from_strategy(strategy)
    dao.add_strategy(strategy)

    for i in dao.list_all_strategies():
        print i

    dao.list_all_strategies()
    dao.list_all_strategies_by_status("inedit")
    dao.list_all_strategies_in_effect()
    dao.count()
    # dao.delete_strategy(dao.get_strategy_by_app_and_name("app", "name"))
