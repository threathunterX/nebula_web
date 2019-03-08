#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import or_

from nebula_meta.util import unicode_string
from threathunter_common.util import millis_now

from .base_dao import BaseDataDao
from ..models.data import RiskIncidentModel

week = 7 * 24 * 60 * 60 * 1000


class IncidentDao(BaseDataDao):

    def _get_incident_list_inside_time(self, start_time, end_time):
        query = self.session.query(RiskIncidentModel)
        return query.filter(RiskIncidentModel.start_time >= start_time,
                            RiskIncidentModel.start_time <= end_time)

    def get_incident_by_id(self, incident_id):
        query = self.session.query(RiskIncidentModel)
        return query.filter(RiskIncidentModel.id == incident_id).first()

    def get_incident_list(self):
        """
        返回所有风险事件信息
        """
        query = self.session.query(RiskIncidentModel)
        return [_.to_dict() for _ in query.all()]

#    def get_statistic_data(self, start_time, end_time):
#        """
#        返回指定时间内所有小时的incident数目
#        :param start_time: 开始时间
#        :param end_time: 结束时间
#        :return: timestamp list
#        """
#        # 根据相同小时时间戳进行group by，统计时间戳和数量
#        query_string = 'SELECT unix_timestamp(from_unixtime(start_time/1000,"%Y:%m:%d %H:00:00"))*1000, count(*) FROM risk_incident WHERE start_time >= {} AND start_time <= {} GROUP BY from_unixtime(start_time/1000, "%Y:%m:%d %H")'
#        return self.session.execute(query_string.format(start_time, end_time)).fetchall()

    def add_incident(self, incident):
        """
        新增incident
        """
        incident = RiskIncidentModel.from_dict(incident)
        self.session.add(incident)
        self.session.commit()

    def update_status(self, incident_id, status):
        incident = self.get_incident_by_id(incident_id)
        if incident and status:
            incident.status = int(status)
            self.session.merge(incident)
            self.session.commit()

    def get_status_statistics(self, start_time, end_time):
        """
        统计风险事件状态
        状态0为未处理，状态1为风险事件，状态2为误报事件
        状态3为未处理事件超过一周既状态0的时间戳为一周前
        """
        query = self._get_incident_list_inside_time(start_time, end_time)
        status_statistics = {i: 0 for i in range(0, 4)}
        for incident in query.all():
            if incident.status == 0 and incident.start_time + week < millis_now():
                status_statistics[3] += 1
            else:
                status_statistics[incident.status] += 1

        return status_statistics

    def get_detail_list(self, start_time, end_time, offset, limit, keyword=None, status=''):
        """
        返回指定时间内所有incident的详细信息list
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param offset: 页数
        :param limit: 页大小
        :param keyword: 关键字
        :param status: 风险事件状态
        :return: incident detail list
        """
        query = self._get_incident_list_inside_time(start_time, end_time)
        query = query.order_by(RiskIncidentModel.risk_score.desc())

        if keyword:
            keyword = unicode_string('%{}%'.format(keyword.encode('utf-8')))
            query = query.filter(or_(RiskIncidentModel.ip.like(keyword),
                                     RiskIncidentModel.uri_stems.like(keyword)))

        # 状态0为未处理，状态1为风险事件，状态2为误报事件
        # 状态3为未处理事件超过一周既状态0的时间戳为一周前
        if status:
            status = int(status)
            if status == 3:
                query = query.filter(RiskIncidentModel.status == 0,
                                     RiskIncidentModel.start_time + week < millis_now())
            elif status == 0:
                query = query.filter(RiskIncidentModel.status == 0,
                                     RiskIncidentModel.start_time + week >= millis_now())
            else:
                query = query.filter(RiskIncidentModel.status == status)

        query = query.slice((offset - 1) * limit, offset * limit)

        incident_list = [incident.to_dict() for incident in query.all()]

        # 状态为3时，返回数据incident数据状态从0改为3
        if status == 3:
            for _ in incident_list:
                _['status'] == 3

        return incident_list

    def remove_incidents(self, start_time, end_time):
        """
        删除指定时间内的风险事件
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return:
        """
        query = self._get_incident_list_inside_time(
            start_time=start_time, end_time=end_time)
        query.delete()
        self.session.commit()
