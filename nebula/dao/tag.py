#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .base_dao import BaseDao
from ..models import TagModel as CustModel


class TagDao(BaseDao):

    def list_all_tags(self):
        query = self.session.query(CustModel)
        result = query.all() or []
        result = [_.to_tag() for _ in result]
        return result

    def get_tag(self, tag_id):
        query = self.session.query(CustModel)
        result = query.filter(CustModel.id == tag_id).first()
        if result:
            return result.to_tag()

    def if_tag_exists(self, name):
        query = self.session.query(CustModel)
        result = query.filter(CustModel.name == name).count()
        if result > 0:
            return True
        return False

    def if_tag_exists_nebula(self, name, app):
        query = self.session.query(CustModel)
        result = query.filter(CustModel.name == name,
                              CustModel.app == app).count()
        if result > 0:
            return True
        return False

    def add_tag(self, tag):
        if not self.if_tag_exists(tag['name']):
            new_tag = CustModel.from_tag(tag)
            self.session.add(new_tag)
            self.session.commit()

    def clear(self):
        query = self.session.query(CustModel)
        query.delete()
        self.session.commit()

    def count(self):
        query = self.session.query(CustModel)
        return query.count()
