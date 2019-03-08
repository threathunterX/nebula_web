#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, logging
import unittest

from sqlalchemy.orm import sessionmaker

from nebula_meta.model import Strategy

from nebula.views import strategy
from nebula.dao.strategy_dao import StrategyCustDao
from nebula.tests.base import WebTestCase, wsgi_safe, Auth_Code

logging.basicConfig(level=logging.DEBUG)

# global application scope.  create Session class, engine
Session = sessionmaker()

Dummy_Strategies = '''
[
    {
      "status": "inedit",
      "terms": [
        {
          "scope": "realtime",
          "remark": "",
          "op": "==",
          "right": {
            "subtype": "",
            "config": {
              "value": "T"
            },
            "type": "constant"
          },
          "left": {
            "subtype": "",
            "config": {
              "field": "result",
              "event": [
                "nebula",
                "ACCOUNT_LOGIN"
              ]
            },
            "type": "event"
          }
        },
        {
          "scope": "profile",
          "remark": "",
          "op": ">",
          "right": {
            "subtype": "",
            "config": {
              "value": "10"
            },
            "type": "constant"
          },
          "left": {
            "subtype": "getvariable",
            "config": {
              "variable": [
                "nebula",
                "ip__login__succ__uid_count_distinct__1d__profile"
              ],
              "trigger": {
                "keys": [
                  "c_ip"
                ],
                "event": [
                  "nebula",
                  "ACCOUNT_LOGIN"
                ]
              }
            },
            "type": "func"
          }
        },
        {
          "scope": "profile",
          "remark": "",
          "op": "",
          "right": null,
          "left": {
            "subtype": "setblacklist",
            "config": {
              "remark": "",
              "name": "ACCOUNT",
              "checktype": "IP",
              "decision": "review",
              "checkvalue": "c_ip",
              "checkpoints": "",
              "ttl": 300
            },
            "type": "func"
          }
        }
      ],
      "tags": [],
      "app": "nebula",
      "starteffect": 1484046419489,
      "endeffect": 1641121620142,
      "modifytime": 1484046585354,
      "score": 0,
      "category": "ACCOUNT",
      "remark": "IP当天成功登录多个UID",
      "isLock": false,
      "name": "dummy_inedit_strategy",
      "version": 1508223538505,
      "group_id": 2,
      "createtime": 1484046585354
    },
{
      "status": "inedit",
      "terms": [
        {
          "scope": "realtime",
          "remark": "",
          "op": "==",
          "right": {
            "subtype": "",
            "config": {
              "value": "T"
            },
            "type": "constant"
          },
          "left": {
            "subtype": "",
            "config": {
              "field": "result",
              "event": [
                "nebula",
                "ACCOUNT_LOGIN"
              ]
            },
            "type": "event"
          }
        },
        {
          "scope": "profile",
          "remark": "",
          "op": ">",
          "right": {
            "subtype": "",
            "config": {
              "value": "10"
            },
            "type": "constant"
          },
          "left": {
            "subtype": "getvariable",
            "config": {
              "variable": [
                "nebula",
                "ip__login__succ__uid_count_distinct__1d__profile"
              ],
              "trigger": {
                "keys": [
                  "c_ip"
                ],
                "event": [
                  "nebula",
                  "ACCOUNT_LOGIN"
                ]
              }
            },
            "type": "func"
          }
        },
        {
          "scope": "profile",
          "remark": "",
          "op": "",
          "right": null,
          "left": {
            "subtype": "setblacklist",
            "config": {
              "remark": "",
              "name": "ACCOUNT",
              "checktype": "IP",
              "decision": "review",
              "checkvalue": "c_ip",
              "checkpoints": "",
              "ttl": 300
            },
            "type": "func"
          }
        }
      ],
      "tags": [],
      "app": "nebula",
      "starteffect": 1484046419489,
      "endeffect": 1641121620142,
      "modifytime": 1484046585354,
      "score": 0,
      "category": "ACCOUNT",
      "remark": "IP当天成功登录多个UID",
      "isLock": false,
      "name": "dummy_inedit_strategy_2",
      "version": 1508223538505,
      "group_id": 2,
      "createtime": 1484046585354
    },
{
      "status": "online",
      "terms": [
        {
          "scope": "realtime",
          "remark": "",
          "op": "==",
          "right": {
            "subtype": "",
            "config": {
              "value": "T"
            },
            "type": "constant"
          },
          "left": {
            "subtype": "",
            "config": {
              "field": "result",
              "event": [
                "nebula",
                "ACCOUNT_LOGIN"
              ]
            },
            "type": "event"
          }
        },
        {
          "scope": "profile",
          "remark": "",
          "op": ">",
          "right": {
            "subtype": "",
            "config": {
              "value": "10"
            },
            "type": "constant"
          },
          "left": {
            "subtype": "getvariable",
            "config": {
              "variable": [
                "nebula",
                "ip__login__succ__uid_count_distinct__1d__profile"
              ],
              "trigger": {
                "keys": [
                  "c_ip"
                ],
                "event": [
                  "nebula",
                  "ACCOUNT_LOGIN"
                ]
              }
            },
            "type": "func"
          }
        },
        {
          "scope": "profile",
          "remark": "",
          "op": "",
          "right": null,
          "left": {
            "subtype": "setblacklist",
            "config": {
              "remark": "",
              "name": "ACCOUNT",
              "checktype": "IP",
              "decision": "review",
              "checkvalue": "c_ip",
              "checkpoints": "",
              "ttl": 300
            },
            "type": "func"
          }
        }
      ],
      "tags": [],
      "app": "nebula",
      "starteffect": 1484046419489,
      "endeffect": 1641121620142,
      "modifytime": 1484046585354,
      "score": 0,
      "category": "ACCOUNT",
      "remark": "IP当天成功登录多个UID",
      "isLock": false,
      "name": "dummy_online_strategy",
      "version": 1508223538505,
      "group_id": 2,
      "createtime": 1484046585354
    }
  ]
'''

@wsgi_safe
class TestBatchStrategiesHandler(WebTestCase):
    # 批量修改策略状态，批量删除策略 @Nebula 2.13
    
    def get_handlers(self):
        return [
            ("/nebula/strategies/changestatus/", strategy.StrategyStatusHandler),
            ("/nebula/strategies/delete",strategy.StrategyBatchDelHandler)
        ]

    @classmethod
    def setUpClass(cls):
        cls.dao = StrategyCustDao()
        for app, name in (("nebula", "dummy_inedit_strategy"), ("nebula", "dummy_inedit_strategy_2"),("nebula", "dummy_online_strategy")):
            cls.dao.delete_strategy_by_app_and_name(app, name)
        # delete dummy first

    def tearDown(self):
        for app, name in (("nebula", "dummy_inedit_strategy"), ("nebula", "dummy_inedit_strategy_2"),("nebula", "dummy_online_strategy")):
            self.dao.delete_strategy_by_app_and_name(app, name)

    def testBatchChangeStatus(self):
        url = "/nebula/strategies/changestatus/"
        url = "{}?auth={}".format(url, Auth_Code)
        try:
            for _ in json.loads(Dummy_Strategies):
                self.dao.add_strategy(Strategy.from_dict(_))
                
            request_body = [
                dict(app="nebula", name="dummy_inedit_strategy", newstatus="test"),
                dict(app="nebula", name="dummy_inedit_strategy_2", newstatus="online"), # invalid
                dict(app="nebula", name="dummy_online_strategy", newstatus="outline"),
                ]
            response = self.fetch(url, method='POST', body=json.dumps(request_body))
            res = json.loads(response.body)
            self.assertEqual(res['status'], 0)
            print res['msg']
        finally:
            self.tearDown()
            
    def testBatchDeleteStrategy(self):
        url = "/nebula/strategies/delete"
        url = "{}?auth={}".format(url, Auth_Code)
        try:
            for _ in json.loads(Dummy_Strategies):
                self.dao.add_strategy(Strategy.from_dict(_))
            
            request_body = [
                dict(app="nebula", name="dummy_inedit_strategy"),
                dict(app="nebula", name="dummy_inedit_strategy_2"),
                dict(app="nebula", name="dummy_online_strategy"),
            ]
            # assert strategy exists
            for s in request_body:
                assert StrategyCustDao().get_strategy_by_app_and_name(s["app"], s["name"])

            response = self.fetch(url, method='PUT', body=json.dumps(request_body))
            res = json.loads(response.body)
            self.assertEqual(res['status'], 0)
            
            # assert strategy deleted
            for s in request_body:
                assert not StrategyCustDao().get_strategy_by_app_and_name(s["app"], s["name"])
            
        finally:
            self.tearDown()
    
if __name__ == '__main__':
    unittest.main()