#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json

from sqlalchemy import or_
from sqlalchemy import func
from threathunter_common.util import millis_now

from nebula_meta.util import unicode_string
from .base_dao import BaseDataDao
from ..models.data import NoticeModel as Model

class NoticeDao(BaseDataDao):

    def get_statistic_scene(self, from_time, end_time, scene=None):
        """
        统计每个场景命中的策略统计
        """
        # 按照strategy name进行分组统计
        from sqlalchemy import func
        query = self.session.query(Model.strategy_name, func.count(Model.strategy_name))\
            .group_by(Model.strategy_name).order_by(func.count(Model.strategy_name).desc())

        # 根据场景、开始时间、结束时间进行筛选
        query = query.filter(Model.timestamp >= from_time, Model.timestamp <= end_time)

        if scene:
            query = query.filter(Model.scene_name == scene)

        return query.all()

    def page_notices(self, fromtime=0, endtime=0, page=0, size=0, keyword=None):
        """
        page notices that qualified the given conditions.
        """

        query = self.session.query(Model).order_by(Model.timestamp.desc())

        if fromtime and fromtime > 0:
            query = query.filter(Model.timestamp >= fromtime)

        if endtime and endtime > 0:
            query = query.filter(Model.timestamp <= endtime)

        if keyword:
            keyword = unicode_string('%{}%'.format(keyword.encode('utf-8')))
            query = query.filter(or_(Model.key.like(keyword),
                                     Model.strategy_name.like(keyword),
                                     Model.scene_name.like(keyword),
                                     Model.check_type.like(keyword),
                                     Model.decision.like(keyword),
                                     Model.risk_score.like(keyword),
                                     Model.remark.like(keyword),
                                     Model.geo_province.like(keyword),
                                     Model.geo_city.like(keyword),
                                     Model.test.like(keyword),
                                     Model.tip.like(keyword),
                                     Model.uri_stem.like(keyword)))

        count = query.count()
        if size and size > 0 and page and page > 0:
            total_page = (count + size - 1) // size
            query = query.slice((page - 1) * size, page * size)
        else:
            total_page = 1

        return count, total_page, [Model.to_notice(_) for _ in query.all()]

    def get_statistic_count(self, start_time, end_time, test):
        """
        返回指定时间内所有小时的生产报警数目
        """
        test = 1 if test else 0
        # 根据相同小时时间戳进行group by，统计时间戳和数量
        query_string = 'SELECT unix_timestamp(from_unixtime(timestamp/1000,"%Y:%m:%d %H:00:00"))*1000, count(*) FROM notice WHERE timestamp >= {} AND timestamp <= {} AND test = {} GROUP BY from_unixtime(timestamp/1000, "%Y:%m:%d %H")'
        return self.session.execute(query_string.format(start_time, end_time, test)).fetchall()

    def list_notices(self, key=None, limit=None, fromtime=None, endtime=None):
        """
        list notices that qualified the given conditions.
        """

        query = self.session.query(Model).order_by(Model.timestamp.desc())
        if fromtime and fromtime > 0:
            query = query.filter(Model.timestamp >= fromtime)

        if endtime and endtime > 0:
            query = query.filter(Model.timestamp <= endtime)

        if key:
            query = query.filter(Model.key == key)

        if limit and limit > 0:
            query = query.limit(limit)

        return [Model.to_notice(_) for _ in query.all()]

    def get_valid_notices(self):
        now = millis_now()
        # 查询未过期的notice，按照decision进行分组统计
        query_sql = 'SELECT decision, COUNT(decision) FROM notice WHERE expire > %s AND test = FALSE GROUP BY decision' % now
        return self.session.execute(query_sql).fetchall()

    def white_or_black(self, test=False, check_type=None, decision=None):
        now = millis_now()
        query = self.session.query(Model).order_by(Model.timestamp.desc())

        query = query.filter(Model.expire >= now, Model.test == test)

        if check_type:
            query = query.filter(Model.check_type == check_type)

        if decision:
            query = query.filter(Model.decision == decision)

        return [ _.key for _ in query.all() ]

    def get_whitelist(self, fromtime=None):
        """
        获取未过期的白名单, 之后成(key, check_type):obj 的缓存? @todo
        """
        if fromtime is None:
            now = millis_now()
        else:
            now = fromtime

        query = self.session.query(Model).filter(Model.expire >= now).filter(Model.decision == 'accept')

        return ( Model.to_notice(_) for _ in query.all() )

    def get_whitelist_keys(self, fromtime=None):
        return ( (_.key, _.check_type, _.test) for _ in self.get_whitelist(fromtime) )

    def get_whitelist_whole(self, fromtime=None):
        '''
        返回生成器, 可用dict实例化,格式如下:
        { (key, check_type, test):{ check_type:"ip",
        key:"172.16.0.5",
        expire:1456215406040,
        test:false,
        remark:"permanent wechat white list",
        decision:"accept"}
        }
        '''
        return ( ((_.key, _.check_type, _.test), dict(check_type=_.check_type,key=_.key,
                                              expire=_.expire, test=_.test, remark=_.remark,
                                              decision=_.decision))
                 for _ in self.get_whitelist(fromtime) )

    def get_notices(self, is_checking=True, **kwargs):
        """
        will conbine get_notices_for_checking and list notices for cache
        """
        key = kwargs.get('key', None)
        fromtime = kwargs.get('fromtime', None)
        endtime = kwargs.get('endtime', None)
        check_types = kwargs.get('check_types', None)
        scene_types = kwargs.get('scene_types', None)
        strategies = kwargs.get('strategies', None)
        decisions = kwargs.get('decisions', None)
        limit = kwargs.get('limit', 10)
        page = kwargs.get('page', 1)
        filter_expire = kwargs.get('filter_expire', False)
        test = kwargs.get('test', None)

        if is_checking and key is None:
            raise ValueError, 'check risk can not without key.'

        # 只有当既不是is_checking, 且 filter_expire为false的时候不用过滤掉过期项
        if is_checking:
            query = self.session.query(Model).order_by(Model.expire.asc())
            now = millis_now()
            query = query.filter(Model.expire >= now, Model.test == test)
        else:
            query = self.session.query(Model).order_by(Model.timestamp.desc())
            if filter_expire:
                now = millis_now()
                query = query.filter(Model.expire >= now)

        if decisions:
            query = query.filter(Model.decision.in_(decisions))

        if strategies:
            query = query.filter(Model.strategy_name.in_(strategies))

        if check_types:
            query = query.filter(Model.check_type.in_(check_types))

        if scene_types:
            query = query.filter(Model.scene_name.in_(scene_types))

        if fromtime and fromtime > 0:
            query = query.filter(Model.timestamp >= fromtime)

        if endtime and endtime > 0:
            query = query.filter(Model.timestamp <= endtime)

        if key:
            # change to like
            query = query.filter(Model.key.like(key))

        if test is not None:
            test = True if test == 'true' else False
            query = query.filter(Model.test == test)

        count = query.count()
        total_page = (count + limit - 1) // limit
        query = query.slice((page - 1) * limit, page * limit)

        return count, total_page, [Model.to_notice(_) for _ in query.all()]

    def aggregate_notices(self, **kwargs):
        """
        查询风险名单，并根据key、strategy进行聚合
        """
        key = kwargs.get('key', None)
        fromtime = kwargs.get('fromtime', None)
        endtime = kwargs.get('endtime', None)
        check_types = kwargs.get('check_types', None)
        scene_types = kwargs.get('scene_types', None)
        strategies = kwargs.get('strategies', None)
        decisions = kwargs.get('decisions', None)
        limit = kwargs.get('limit', 25)
        page = kwargs.get('page', 1)
        filter_expire = kwargs.get('filter_expire', False)
        test = kwargs.get('test', None)

        ifAggregate = False
        if fromtime and endtime and int(endtime) - int(fromtime) <= 3600000:
            ifAggregate = True
        
        if ifAggregate:
            query = self.session.query(Model.timestamp, Model.key, Model.strategy_name,
                                   Model.scene_name, Model.checkpoints, Model.check_type,
                                   Model.decision, Model.risk_score, Model.expire,
                                   Model.remark, Model.variable_values, Model.geo_province,
                                   Model.geo_city, Model.test, Model.tip, Model.uri_stem,
                                   func.count(Model.key))
        else:
            query = self.session.query(Model.timestamp, Model.key, Model.strategy_name,
                                   Model.scene_name, Model.checkpoints, Model.check_type,
                                   Model.decision, Model.risk_score, Model.expire,
                                   Model.remark, Model.variable_values, Model.geo_province,
                                   Model.geo_city, Model.test, Model.tip, Model.uri_stem,)

        if filter_expire:
            now = millis_now()
            query = query.filter(Model.expire >= now)

        if decisions:
            query = query.filter(Model.decision.in_(decisions))

        if strategies:
            query = query.filter(Model.strategy_name.in_(strategies))

        if check_types:
            query = query.filter(Model.check_type.in_(check_types))

        if scene_types:
            query = query.filter(Model.scene_name.in_(scene_types))

        if fromtime and fromtime > 0:
            query = query.filter(Model.timestamp >= fromtime)

        if endtime and endtime > 0:
            query = query.filter(Model.timestamp <= endtime)

        if key:
            query = query.filter(Model.key.like("%%%s%%" % key))

        if test:
            test = True if test == 'true' else False
            query = query.filter(Model.test == test)
        query = query.order_by(Model.timestamp.desc())
        
        if ifAggregate:
            query = query.group_by(Model.key, Model.strategy_name)

        count = query.count()
        offset = (page-1) * limit
        query = query.offset(offset).limit(limit)
        total_page = int(count) / int(limit)
        if count % limit != 0:
            total_page += 1

        notices = []
        for _ in query.all():
            n = dict()
            if ifAggregate:
                n['timestamp'],n['key'], n['strategy_name'], n['scene_name'], \
                n['checkpoints'], n['check_type'], n['decision'], n['risk_score'], \
                n['expire'], n['remark'], n['variable_values'], n['geo_province'], \
                n['geo_city'], n['test'], n['tip'], n['uri_stem'], n['count'] = _
            else:
                n['timestamp'],n['key'], n['strategy_name'], n['scene_name'], \
                n['checkpoints'], n['check_type'], n['decision'], n['risk_score'], \
                n['expire'], n['remark'], n['variable_values'], n['geo_province'], \
                n['geo_city'], n['test'], n['tip'], n['uri_stem']= _
                n['count'] = 1

            notices.append(n)

        return count, total_page, notices

    def get_trigger_events(self, key, strategy, **kwargs):
        """
        查询风险名单触发事件详情
        """
        fromtime = kwargs.get('fromtime', None)
        endtime = kwargs.get('endtime', None)
        check_types = kwargs.get('check_types', None)
        scene_types = kwargs.get('scene_types', None)
        decisions = kwargs.get('decisions', None)
        filter_expire = kwargs.get('filter_expire', False)
        test = kwargs.get('test', None)

        query = self.session.query(Model.trigger_event).order_by(Model.timestamp.desc())
        query = query.filter(Model.key == key).filter(Model.strategy_name == strategy)

        if filter_expire:
            now = millis_now()
            query = query.filter(Model.expire >= now)

        if decisions:
            query = query.filter(Model.decision.in_(decisions))

        if check_types:
            query = query.filter(Model.check_type.in_(check_types))

        if scene_types:
            query = query.filter(Model.scene_name.in_(scene_types))

        if fromtime and fromtime > 0:
            query = query.filter(Model.timestamp >= fromtime)

        if endtime and endtime > 0:
            query = query.filter(Model.timestamp <= endtime)

        if test is not None:
            test = True if test == 'true' else False
            query = query.filter(Model.test == test)

        return [json.loads(_[0]) for _ in query.all()]

    def add_notice(self, notice):
        """
        add one notice
        """

        # if not NoticeDao.metrics_sender.is_start():
        #     NoticeDao.metrics_sender.start()
        # NoticeDao.metrics_sender.addValue(1)

        notice_model = Model.from_notice(notice)
        notice_model.last_modified = millis_now()
        self.session.add(notice_model)
        self.session.commit()

    def purge_notices(self, endtime):
        self.remove_notices(endtime=endtime)

    def remove_notices(self, key=None, fromtime=None, endtime=None):
        query = self.session.query(Model)
        if fromtime and fromtime > 0:
            query = query.filter(Model.timestamp >= fromtime)

        if endtime and endtime > 0:
            query = query.filter(Model.timestamp <= endtime)

        if key:
            query = query.filter(Model.key == key)

        # 过期notice才删除 @cancle
#        now = millis_now()
#        query = query.filter(Model.expire < now)
        query.delete()
        self.session.commit()

    def get_notices_for_checking(self, check_type, key, test, scene_names=[]):
        """
        Get notices for checking operation in asc order by timestamp
        """

        if not key:
            raise RuntimeError("invalid key")

        query = self.session.query(Model).order_by(Model.expire.asc())
        if check_type:
            query = query.filter(Model.check_type == check_type)
        query = query.filter(Model.key == key)
        query = query.filter(Model.test == test)
        now = millis_now()
        query = query.filter(Model.expire >= now)
        if scene_names:
            query = query.filter(Model.scene_name.in_(scene_names))
        return [Model.to_notice(_) for _ in query.all()]

    def get_unexpired_notice_data(self, strategy=None, check_type=None, decision=None, test=None, scene_type=None):
        from threathunter_common.util import text
        now = millis_now()
        query = self.session.query(Model.strategy_name, Model.check_type, Model.decision, Model.test, Model.scene_name,
                                   Model.key)
        if strategy is not None:
            query = query.filter(Model.strategy_name == strategy)
        if check_type is not None:
            query = query.filter(Model.check_type == check_type)
        if test is not None:
            query = query.filter(Model.test == test)
        if scene_type is not None:
            query = query.filter(Model.scene_name == scene_type)

        query = query.filter(Model.expire >= now)
        data = query.all()

        result = {}
        # 按照白黑灰的优先级选取
        result.update({_[-1]: _ for _ in data if text(_[-4]) == u"review"})
        result.update({_[-1]: _ for _ in data if text(_[-4]) == u"reject"})
        result.update({_[-1]: _ for _ in data if text(_[-4]) == u"accept"})

        # 最后按照过滤
        if decision is not None:
            result = {k: v for k, v in result.items() if v[-4] == decision}
        return result

    def clear(self):
        """
        clear all the records
        """

        query = self.session.query(Model)
        query.delete()
        self.session.commit()

    def count(self):
        query = self.session.query(Model)
        return query.count()

if __name__ == "__main__":
    d = NoticeDao()
    r = d.list_notices()
    r = d.get_notices_for_checking("ip", "192.168.12.117", True, scene_names=["visit", "sdt"])
    r = r[:10]
    for i in r:
        print i
    pass
