#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from threathunter_common.util import millis_now
from .base_dao import BaseDao, BaseDefaultDao
from ..models.default import ConfigDefaultModel as Model
from ..models import ConfigCustModel as CustModel

class ConfigDefaultDao(BaseDefaultDao):

    def list_all_config(self):
        query = self.session.query(Model).order_by(Model.last_modified.desc())
        return [_.get_dict() for _ in query.all()]

    def _get_config_model_by_key(self, key):
        query = self.session.query(Model).filter(Model.configkey == key)
        return query.first()

    def get_config_by_key(self, key):
        m = self._get_config_model_by_key(key)
        if m:
            return m.get_dict()
        else:
            return None

    def add_config(self, key, value):
        """
        add one config
        """
        config_model = self._get_config_model_by_key(key)
        if not config_model:
            config_model = Model(configkey=key, configvalue=value, last_modified=millis_now())
            self.session.add(config_model)
        else:
            config_model.configvalue = value
            config_model.last_modified = millis_now()
            self.session.merge(config_model)
        self.session.commit()

    def remove_config(self, key):
        config_model = self._get_config_model_by_key(key)
        if config_model:
            self.session.delete(config_model)
            self.session.commit()

    def clear(self):
        """
        clear all the config
        """

        query = self.session.query(Model)
        query.delete()
        self.session.commit()

    def count(self):
        query = self.session.query(Model)
        return query.count()

class ConfigCustDao(BaseDao):

    def list_all_config(self):
        """
        list all config, 取定制的和默认的config的合集，定制的覆盖默认的config
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        default_query = ConfigDefaultDao().session.query(Model).order_by(Model.last_modified.desc())
        configs = dict( (_.configkey, _.get_dict()) for _ in default_query.all())
        # key: config obj
        cust_query = self.session.query(CustModel).order_by(CustModel.last_modified.desc())
        for cc in cust_query.all():
            configs[cc.configkey] = cc.get_dict()
        return configs.values()

    def _get_config_model_by_key(self, key):
        """
        只根据key获取config custmize优先default
        @add within v2.0
        """

        query = self.session.query(CustModel).filter(CustModel.configkey == key)
        cust_config =  query.first()
        if not cust_config:
            query = ConfigDefaultDao().session.query(Model).filter(Model.configkey == key)
            return query.first()
        else:
            return cust_config

    def list_all_cust_config(self):
        """
        list all custmize config
        @add within v2.0
        """
        query = self.session.query(CustModel).order_by(CustModel.last_modified.desc())
        return [_.get_dict() for _ in query.all()]

    def _get_cust_config_model_by_key(self, key):
        """
        只根据key获取定制化的config
        @add within v2.0
        """
        query = self.session.query(CustModel).filter(CustModel.configkey == key)
        return query.first()

    def get_config_by_key(self, key):
        """
        @keep 保持接口功能不变 with v1.0
        """
        m = self._get_config_model_by_key(key)
        if m:
            return m.get_dict()
        else:
            return None

    def add_config(self, key, value):
        """
        only add custmize config, just override the default config, not delete key's config entirely.
        @keep 保持接口功能不变,含义变了 with v1.0
        """
        config_model = self._get_cust_config_model_by_key(key)
        if not config_model:
            config_model = CustModel(configkey=key, configvalue=value, last_modified=millis_now())
            self.session.add(config_model)
        else:
            config_model.configvalue = value
            config_model.last_modified = millis_now()
            self.session.merge(config_model)
        self.session.commit()

    def remove_config(self, key):
        """
        only delete custmize config, back to default config if exists(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        config_model = self._get_cust_config_model_by_key(key)
        if config_model:
            self.session.delete(config_model)
            self.session.commit()

        #TODO can't delete

    def clear(self):
        """
        clear all Custmize config, reset to default config(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(CustModel)
        query.delete()
        self.session.commit()

    def count(self):
        query = self.session.query(CustModel)
        return query.count()
