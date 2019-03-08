#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..models import LogQueryModel
from .base_dao import BaseDao


class LogQueryDao(BaseDao):

    def get_user_logquerys(self, user_id):
        """
        根据用户id来查询日志查询列表
        :param user_id:
        :return:
        """
        query = self.session.query(LogQueryModel)
        query = query.filter(LogQueryModel.user_id == user_id)
        return query.all()

    def update_logquery(self, **kwargs):
        """
        如果参数中不包含id，则新增日志查询，包含id，则修改日志查询
        """
        logquery_id = kwargs.get('id', None)
        logquery = LogQueryModel.from_dict(kwargs)
        if logquery_id is None:
            self.session.add(logquery)
            self.session.commit()
        else:
            query = self.session.query(LogQueryModel)
            old_logquery = query.filter(
                LogQueryModel.id == logquery_id).first()

            # 如果数据库存在日志查询，则修改数据
            if old_logquery:
                logquery.id = logquery_id
                self.session.merge(logquery)
                self.session.commit()
            else:
                return False

        return logquery.id

    def update_logquery_file(self, logquery_id, page=None, total=None, temp_query_file=None):
        """
        根据id更新日志查询page、total、temp_query_file
        :param logquery_id:
        :param page:
        :param total:
        :param temp_query_file:
        :return:
        """
        query = self.session.query(LogQueryModel)
        logquery = query.filter(LogQueryModel.id == logquery_id).first()
        if logquery:
            # 如果存在日志查询才更新状态
            if page:
                logquery.page = page

            if total:
                logquery.total = total

            if temp_query_file:
                logquery.temp_query_file = temp_query_file

            self.session.merge(logquery)
            self.session.commit()

    def delete_logquery(self, query_id):
        """
        删除指定id的日志查询
        :param query_id:
        :return:
        """
        query = self.session.query(LogQueryModel)
        query = query.filter(LogQueryModel.id == query_id)
        query.delete()
        self.session.commit()
