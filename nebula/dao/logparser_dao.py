#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..models import LogParserModel
from .base_dao import BaseDao


class LogParserCustDao(BaseDao):

    def upsert_logparser(self, **kwargs):
        """
        如果参数中不包含id，则新增parser，包含id，则修改parser
        """
        parser_id = kwargs.get('id', None)
        logparser = LogParserModel.from_dict(kwargs)
        if parser_id is None:
            self.session.add(logparser)
            self.session.commit()
        else:
            query = self.session.query(LogParserModel)
            old_parser = query.filter(
                LogParserModel.id == parser_id).first()

            # 如果数据库存在logparser，则修改数据
            if old_parser:
                logparser.id = parser_id
                self.session.merge(logparser)
                self.session.commit()
            else:
                return False

        return True

    def get_all_logparsers(self, name=None, host=None, url=None, status=None):
        """
        获得所有的logparser
        :param name: dest名称
        :param host: terms中的host
        :param url: terms中的URL
        :param status: logparser status
        :return:
        """

        query = self.session.query(LogParserModel)

        if name:
            query = query.filter(LogParserModel.dest == name)

        if host:
            query = query.filter(LogParserModel.host == host)

        if url:
            query = query.filter(LogParserModel.url == url)

        if status is not None:
            query = query.filter(LogParserModel.status == status)

        return query.all()

    def delete_logparser(self, parser_id):
        """
        删除指定id的logparser
        :param parser_id:
        :return:
        """
        query = self.session.query(LogParserModel)
        query = query.filter(LogParserModel.id == parser_id)
        query.delete()
        self.session.commit()
