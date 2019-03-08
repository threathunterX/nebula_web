#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from threathunter_common.util import millis_now
from nebula_meta.variable_model import sort_variable_models
from .base_dao import BaseDao, BaseDefaultDao
from ..models.default import VariableModelDefault
from ..models import VariableModelCust


def fix_global_variable_registry():
    """
    变量修改时，修改内存里全局的schema配置
    :param self:
    :return:
    """
    from nebula_meta.variable_model import update_variables_to_registry
    update_variables_to_registry(VariableModelCustDao().list_all_models())


class VariableModelDefaultDao(BaseDefaultDao):

    def list_all_models(self):
        """
        get all variable models
        """

        query = self.session.query(VariableModelDefault)
        result = [_.to_variablemodel() for _ in query.all()]
        sort_variable_models(result)
        return result

    def list_model_by_app(self, app):
        return filter(lambda model: model.app == app or model.app == "__all__", self.list_all_models())

    def list_model_by_type(self, type):
        return filter(lambda model: model.type == type, self.list_all_models())

    def _get_db_model_by_app_name(self, app, name):
        """
        get one db record by app and name
        """

        query = self.session.query(VariableModelDefault)
        return query.filter(VariableModelDefault.app == app, VariableModelDefault.name == name).first()

    def add_model(self, model):
        """
        add one variable model
        """

        new = VariableModelDefault.from_variablemodel(model)
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
        fix_global_variable_registry()

    def get_model_by_app_name(self, app, name):
        existing = self._get_db_model_by_app_name(app, name)
        if existing:
            return existing.to_variablemodel()

    def delete_model_by_app_name(self, app, name):
        existing = self._get_db_model_by_app_name(app, name)
        if existing:
            self.session.delete(existing)
            self.session.commit()
            fix_global_variable_registry()

    def delete_model_list_by_app_type_module(self, app, type, module=None):
        query = self.session.query(VariableModelDefault)
        if app:
            query = query.filter(app == VariableModelDefault.app)
        if type:
            query = query.filter(type == VariableModelDefault.type)
        if module:
            query = query.filter(VariableModelDefault.module == module)
        query.delete()
        self.session.commit()
        fix_global_variable_registry()

    def clear(self):
        """
        clear all the records
        """

        query = self.session.query(VariableModelDefault)
        query.delete()
        self.session.commit()
        fix_global_variable_registry()

    def count(self):
        query = self.session.query(VariableModelDefault)
        return query.count()


class VariableModelCustDao(BaseDao):

    def list_all_models(self):
        """
        list all variable models, 取定制的和默认的variable model的合集，定制的覆盖默认的variable model
        @keep 保持接口功能不变，含义变了 with v1.0
        """

        default_query = VariableModelDefaultDao().session.query(VariableModelDefault)
        variables = dict( ( (_.app, _.name), _.to_variablemodel()) for _ in default_query.all())
        # key: variable obj
        cust_query = self.session.query(VariableModelCust)
        for cq in cust_query.all():
            variables[(cq.app, cq.name)] = cq.to_variablemodel()
        result = variables.values()
        sort_variable_models(result)
        return result

    def list_model_by_app(self, app):
        """
        依赖于list_all_models
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        return filter(lambda model: model.app == app or model.app == "__all__", self.list_all_models())

    def list_model_by_type(self, type):
        """
        依赖于list_all_models
        @keep 保持接口功能不变，含义变了 with v1.0
        """
        return filter(lambda model: model.type == type, self.list_all_models())

    def _get_db_model_by_app_name(self, app, name):
        """
        只根据key获取variable custmize优先default
        @add within v2.0
        """
        query = self.session.query(VariableModelCust).filter(VariableModelCust.app == app,
                                                             VariableModelCust.name == name)
        cust_variable = query.first()
        if not cust_variable:
            query = VariableModelDefaultDao().session.query(VariableModelDefault).filter(
                VariableModelDefault.app == app, VariableModelDefault.name == name)
            return query.first()
        else:
            return cust_variable
        
    def _get_cust_db_model_by_app_name(self, app, name):
        """
        只根据key获取定制化的variable
        @add within v2.0
        """
        query = self.session.query(VariableModelCust)
        return query.filter(VariableModelCust.app == app, VariableModelCust.name == name).first()

    def add_model(self, model):
        """
        only add custmize variable, just override the default variable, not delete key's variable entirely.
        @keep 保持接口功能不变,含义变了 with v1.0
        """

        new = VariableModelCust.from_variablemodel(model)
        new.last_modified = millis_now()
        existing = self._get_cust_db_model_by_app_name(model.app, model.name)
        if existing:
            # update
            new.id = existing.id
            self.session.merge(new)
        else:
            # insert
            self.session.add(new)
        self.session.commit()
        fix_global_variable_registry()

    def get_model_by_app_name(self, app, name):
        """
        对外接口只根据key获取variable custmize优先default
        @add within v2.0
        """
        existing = self._get_db_model_by_app_name(app, name)
        if existing:
            return existing.to_variablemodel()

    def delete_model_by_app_name(self, app, name):
        """
        only delete custmize variable model, back to default variable if exists(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        existing = self._get_cust_db_model_by_app_name(app, name)
        if existing:
            self.session.delete(existing)
            self.session.commit()
            fix_global_variable_registry()

    def delete_model_list_by_app_type_module(self, app, type, module=None):
        """
        only delete custmize variable model, back to default variable if exists(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(VariableModelCust)
        if app:
            query = query.filter(app == VariableModelCust.app)
        if type:
            query = query.filter(type == VariableModelCust.type)
        if module:
            query = query.filter(VariableModelCust.module == module)
        query.delete()
        self.session.commit()
        fix_global_variable_registry()

    def clear(self):
        """
        clear all Custmize variable model, reset to default variable(different with b4)
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(VariableModelCust)
        query.delete()
        self.session.commit()
        fix_global_variable_registry()

    def count(self):
        """
        只获取custmize 的variable个数
        @change 保持接口功能结果可能变了,含义也变了 with v1.0
        """
        query = self.session.query(VariableModelCust)
        return query.count()

