#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from threathunter_common.util import millis_now
from .base_dao import BaseDao, BaseDefaultDao
from ..models import EventModelCust
from ..models.default import EventModelDefault

from nebula_meta.event_model import sort_event_models


def fix_global_event_registry():
    """
    变量修改时，修改内存里全局的schema配置
    :return:
    """
    from nebula_meta.event_model import update_events_to_registry
    update_events_to_registry(EventModelCustDao().list_all_models())


class EventModelDefaultDao(BaseDefaultDao):
    """
    Default event model dao
    """

    def list_all_models(self):
        """
        get all event models
        """

        query = self.session.query(EventModelDefault)
        result = [EventModelDefault.to_eventmodel(_) for _ in query.all()]
        sort_event_models(result)
        return result

    def list_model_by_app(self, app):
        return filter(lambda model: model.app == app or model.app == "__all__", self.list_all_models())

    def list_model_by_type(self, type):
        return filter(lambda model: model.type == type, self.list_all_models())

    def _get_db_model_by_app_name(self, app, name):
        """
        get one db record by app and name
        """

        query = self.session.query(EventModelDefault)
        return query.filter(EventModelDefault.app == app, EventModelDefault.name == name).first()

    def add_model(self, model):
        """
        add one event model
        """

        new = EventModelDefault.from_eventmodel(model)
        new.last_modified = millis_now()
        existing = self._get_db_model_by_app_name(model.app, model.name)
        if existing:
            # update
            new.id = existing.id
            self.session.merge(new)
        else:
            # insert
            self.session.add(new)
        self.session.commit()
        fix_global_event_registry()

    def get_model_by_app_name(self, app, name):
        existing = self._get_db_model_by_app_name(app, name)
        if existing:
            return existing.to_eventmodel()

    def delete_model_by_app_name(self, app, name):
        existing = self._get_db_model_by_app_name(app, name)
        if existing:
            self.session.delete(existing)
            self.session.commit()
            fix_global_event_registry()

    def delete_model_list_by_app_type(self, app, type):
        query = self.session.query(EventModelDefault)
        if not app and not type:
            query.filter().delete()
        elif not app:
            query.filter(type == EventModelDefault.type).delete()
        elif not type:
            query.filter(app == EventModelDefault.app).delete()
        else:
            query.filter(type == EventModelDefault.type, app == EventModelDefault.app).delete()
        self.session.commit()
        fix_global_event_registry()

    def delete_model_by_instance(self, event_model):
        self.delete_model_by_app_name(event_model.app, event_model.name)
        fix_global_event_registry()

    def clear(self):
        """
        clear all the records
        """

        query = self.session.query(EventModelDefault)
        query.delete()
        self.session.commit()
        fix_global_event_registry()

    def count(self):
        query = self.session.query(EventModelDefault)
        return query.count()


class EventModelCustDao(BaseDao):
    def list_all_models(self):
        """
        get all event model
        @keep 保持接口功能不变，含义变了 with v1.0
        """

        # cust 优先级更高
        default_query = EventModelDefaultDao().session.query(EventModelDefault)
        events = dict( ( (_.app, _.name), _.to_eventmodel()) for _ in default_query.all())
        # key: event obj
        cust_query = self.session.query(EventModelCust)
        for cq in cust_query.all():
            events[(cq.app, cq.name)] = cq.to_eventmodel()
        result = events.values()
        sort_event_models(result)
        return result

    def list_model_by_app(self, app):
        """
        依赖于list_all_model
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        return filter(lambda model: model.app == app or model.app == "__all__", self.list_all_models())

    def list_model_by_type(self, type):
        """
        依赖于list_all_model
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        return filter(lambda model: model.type == type, self.list_all_models())

    def _get_db_model_by_app_name(self, app, name):
        """
        只根据key获取event custmize优先default
        @add within v2.0
        """
        query = self.session.query(EventModelCust).filter(EventModelCust.app == app, EventModelCust.name == name)
        cust_event = query.first()
        if not cust_event:
            query = EventModelDefaultDao().session.query(EventModelDefault).filter(EventModelDefault.app == app,
                                                                                   EventModelDefault.name == name)
            return query.first()
        else:
            return cust_event

    def _get_cust_model_by_app_name(self, app, name):
        """
        只根据key获取定制化的event
        @add within v2.0
        """
        query = self.session.query(EventModelCust)
        return query.filter(EventModelCust.app == app, EventModelCust.name == name).first()

    def add_model(self, model):
        """
        only add custmize event, just override the default event, not delete key's event entirely.
        @keep 保持接口功能不变,含义变了 with v1.0
        """

        new = EventModelCust.from_eventmodel(model)
        new.last_modified = millis_now()
        existing = self._get_cust_model_by_app_name(model.app, model.name)
        if existing:
            # update
            new.id = existing.id
            self.session.merge(new)
        else:
            # insert
            self.session.add(new)
        self.session.commit()
        fix_global_event_registry()

    def get_model_by_app_name(self, app, name):
        """
        对外接口只根据key获取event custmize优先default
        @add within v2.0
        """
        existing = self._get_db_model_by_app_name(app, name)
        if existing:
            return existing.to_eventmodel()

    def delete_model_by_app_name(self, app, name):
        """
        only delete custmize event model, back to default event if exists(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        existing = self._get_cust_model_by_app_name(app, name)
        if existing:
            self.session.delete(existing)
            self.session.commit()
            fix_global_event_registry()

    def delete_model_list_by_app_type(self, app, type):
        """
        only delete custmize event model, back to default event if exists(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(EventModelCust)
        if not app and not type:
            query.filter().delete()
        elif not app:
            query.filter(type == EventModelCust.type).delete()
        elif not type:
            query.filter(app == EventModelCust.app).delete()
        else:
            query.filter(type == EventModelCust.type, app == EventModelCust.app).delete()
        self.session.commit()
        fix_global_event_registry()

    def delete_model_by_instance(self, model):
        self.delete_model_by_app_name(model.app, model.name)
        fix_global_event_registry()

    def clear(self):
        """
        clear all Custmize event model, reset to default event(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(EventModelCust)
        query.delete()
        self.session.commit()
        fix_global_event_registry()

    def count(self):
        """
        只获取custmize 的event个数
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(EventModelCust)
        return query.count()
