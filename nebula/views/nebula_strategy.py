#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#————————————————————————————————————————————————————
# FileName: nebula_strategy.py
# Version: 0.1
# Author : Rancho
# Email: 
# LastChange: 1/7/2019
# Desc:
# History:
#————————————————————————————————————————————————————
"""
import json
import traceback

from tornado.web import RequestHandler
# from service import log
# 写一个连接mysql 数据库 并且用本地的
import pymysql.cursors
from settings import MySQL_Host
from settings import MySQL_Port
from settings import MySQL_User
from settings import MySQL_Passwd
from settings import Nebula_DB
import logging

from ..dao.event_model_dao import EventModelCustDao

from threathunter_common.util import json_dumps
from nebula_meta.event_model import EventModel, add_event_to_registry

from nebula.dao.event_model_dao import fix_global_event_registry
from nebula_meta.variable_model import VariableModel
from ..dao.variable_model_dao import VariableModelCustDao
from .base import BaseHandler
from nebula.dao.user_dao import authenticated

fix_global_event_registry()

logger = logging.getLogger('nebula.api.nebula_strategy')

default_pycount = """
import json

def event(properties):
    properties = json.loads(properties)
    result = []
    r1 = dict()
    r1['properties'] = properties
    r1['event_name'] = 'None'
    r1['event_result'] = False
    result.append(r1)            
    return json.dumps(result)
"""


def log(*value):
    for i in value:
        print i, type(i)


def mysql_connection():
    db = pymysql.Connect(
        host=MySQL_Host,
        port=MySQL_Port,
        user=MySQL_User,
        passwd=MySQL_Passwd,
        db=Nebula_DB,
        charset='utf8',
    )
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    return (db, cursor)


def all_event_py(strategy):
    db, cursor = mysql_connection()
    sql = "select id, py_name, py_content, py_version, cast(create_time as char) as create_time,  cast(update_time as char) as update_time from event_py where py_name=%s"
    # sql = "select id, py_name, py_content, py_version from event_py where py_name=%s"
    cursor.execute(sql, (strategy))
    r = cursor.fetchone()
    db.close()
    return r


def all_event_py_test(strategy):
    db, cursor = mysql_connection()
    # sql = "select id, py_name, py_content, py_version, cast(create_time as char) as create_time,  cast(update_time as char) as update_time from event_py"
    sql = "select id, py_name, py_content, py_version from event_py"
    cursor.execute(sql)
    r = cursor.fetchall()
    db.close()
    return r


def py_name_only(name):
    db, cursor = mysql_connection()
    sql = "select * from event_py where py_name=%s"
    data = (name)
    cursor.execute(sql, data)
    r = cursor.fetchone()
    db.close()
    return r


def new_py(data):
    db, cursor = mysql_connection()
    try:
        # py_content 内容直接经过检验
        py_version = '1'
        sql = "insert ignore into event_py(`py_name`, `py_content`, `py_version`) values (%s, %s, %s)"
        py_name = data.get('py_name')
        py_content = data.get('py_content')
        data = (py_name, py_content, py_version)
        cursor.execute(sql, data)
        db.commit()
        db.close()
        return True
    except Exception as e:
        print traceback.format_exc()
        logging.error(e)
        db.rollback()
        db.close()
        return False


def change_db_data(data):
    db, cursor = mysql_connection()
    try:
        py_content = data.get('py_content')
        py_name = data.get('py_name')
        # 先获得版本号
        sql = "select py_version from event_py where py_name=%s"
        cursor.execute(sql, (py_name))
        r = cursor.fetchone()
        py_version = int(r.get('py_version', 1))
        py_version += 1
        # 如果 content = "", 那么 put 初始化版本
        if py_content == '':
            py_content = default_pycount
        else:
            pass

        sql = "update event_py set py_content=%s, py_version=%s where py_name=%s"
        d = (py_content, py_version, py_name)
        cursor.execute(sql, d)
        db.commit()
    except Exception as e:
        print("error", e)
        return False
    finally:
        db.close()
        return True


def delete_event_for_sniffer(py_name):
    db, cursor = mysql_connection()
    del_sql = "delete from event_py where py_name='{}'".format(py_name)
    cursor.execute(del_sql)
    db.commit()
    r = cursor.fetchone()
    db.close()
    return r


class NebulaStrategy(RequestHandler):
    def get(self):
        s = self.get_argument("strategy", "None")
        # if s == "None":
        #     py = all_event_py_test(s)
        #     print py
        # else:
        py = all_event_py(s)

        result = json.dumps(py)
        self.write(result)

    def post(self):
        agrs = self.request.body
        agrs = json.loads(agrs)
        py_name = agrs.get('py_name')
        if py_name == '':
            self.write('py_name error')
        else:
            o = py_name_only(py_name)
            if o is not None:
                self.write('py name not only')
            else:
                r = new_py(agrs)
                if r:
                    result = {
                        'result': 'success'
                    }
                else:
                    result = {
                        'result': 'fail'
                    }

                self.write(json.dumps(result))

    def put(self):
        agrs = self.request.body
        agrs = json.loads(agrs)
        py_name = agrs.get('py_name')

        result = dict(
            status_code=415,
            status_message='unsupported media type',
        )
        if py_name == '':
            result['status_code'] = 412
            result['status_message'] = 'Precondition Failed'
        else:
            found = py_name_only(py_name)
            if found is not None:
                success = change_db_data(agrs)
                if success:
                    result['status_code'] = 200
                    result['status_message'] = 'OK'
                else:
                    result['status_code'] = 415
                    result['status_message'] = 'unsupported media type'
            else:
                result['status_code'] = 404
                result['status_message'] = 'not found'

        self.write(json.dumps(result))


class NewNebulaStrategy(BaseHandler):
    """当新增事件时，需要调度此接口为保证sniffer可以正常抓取流量
    uri  /nebula/NewNebulaStrategy
    """
    @authenticated
    def put(self):
        body = self.request.body
        data = json.loads(body)
        app = data[0]["app"]
        name = data[0]["name"]
        existing = EventModelCustDao()._get_cust_model_by_app_name(app, name)
        if existing:
            self.finish({"status": -1, "msg": "faild !!! This event model existing "})
        else:
            if not self.add_event_to_platform(body):
                self.finish(json.dumps({"status": -1, "msg": "faild !!! add event to platform "}))
            elif not self.sync_to_base_events(body):
                EventModelCustDao().delete_model_by_app_name(app, name)
                self.finish(json.dumps({"status": -1, "msg": "faild !!! syn event to basedata "}))
            elif not self.add_stratigy_to_sniffer(body):
                # 删除第1步操作新加的数据
                EventModelCustDao().delete_model_by_app_name(app, name)
                # 删除第2步操作新加的数据，由于下面增加的时候会同步到base_event库，所以在删除的时候也同步这个操作
                VariableModelCustDao().delete_model_by_app_name(app, name)
                self.finish(json.dumps({"status": -1, "msg": "faild !!! add stratigy to sniffer "}))
            else:
                self.finish(json.dumps({"status": 0, "msg": "ok"}))

    @authenticated
    def delete(self):
        """
        删除相应的event配置
        """
        body = self.request.body
        data = json.loads(body)
        app = data["app"]
        name = data["name"]
        self.set_header('content-type', 'application/json')
        try:
            # 删除事件详情
            EventModelCustDao().delete_model_by_app_name(app, name)
            # 由于下面增加的时候会同步到base_event库，所以在删除的时候也同步这个操作
            VariableModelCustDao().delete_model_by_app_name(app, name)
            # 从sniffer脚本库中删除
            delete_event_for_sniffer(name)
            self.finish(json_dumps({"status": 0, "msg": "ok", "values": []}))
        except:
            logger.error(traceback.format_exc())
            self.finish(json_dumps({"status": -1, "msg": str(traceback.format_exc())}))

    def add_event_to_platform(self, body):
        """
        1，新增基础事件,参数同/platform/event_models 的post接口一样
        :param body:
        :return:
        """
        try:
            events = list()
            for _ in json.loads(body):
                event = EventModel.from_dict(_)
                add_event_to_registry(event)
                events.append(event)
        except:
            logger.error(traceback.format_exc())
            return False
        try:
            dao = EventModelCustDao()
            for event in events:
                dao.add_model(event)
            return True
        except Exception as err:
            logger.error(traceback.format_exc())
            return self.process_error(500, str(err))

    def sync_to_base_events(self, body):
        """
        第二步：新增基础事件到基础事件记录表
        参数：依赖/platform/event_models中post的参数
        :param body:
        :return:
        """
        try:
            events = list()
            base_event = dict()
            for _ in json.loads(body):
                # 自动设置一些默认值，无需前端重复传递
                base_event["status"] = "enable"
                base_event["type"] = "event"
                base_event["source"] = [{"app": _.get("app"), "name": _.get("name")}]

                # 获取body中我们需要的值
                base_event["app"] = _.get("app")
                base_event["name"] = _.get("name")
                base_event["visible_name"] = _.get("visible_name")
                base_event["remark"] = _.get("remark")
                base_event["module"] = _.get("type")
                event = VariableModel.from_dict(base_event)
                events.append(event)
        except:
            logger.error(traceback.format_exc())
            return False
        try:
            dao = VariableModelCustDao()
            for event in events:
                dao.add_model(event)
            return True
        except:
            logger.error(traceback.format_exc())
            return False

    def add_stratigy_to_sniffer(self, body):
        """第三步，获取数据，将数据中的脚本同步到event_py库中，
        保证sniffer会抓取流量当做基础事件
        """
        datas = json.loads(body)
        for data in datas:
            try:
                print data
                # if py_name_only(data["py_name"]):
                #     return False
                # else:
                py_name = data.get("py_name", None)
                py_content = data.get("py_content", default_pycount)
                if py_name and py_content:
                    result = new_py(data)
                    return result
                else:
                    return False
            except:
                logger.error(traceback.format_exc())
                return False
