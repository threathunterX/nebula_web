#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json

from ..models import PermissionModel as Model
from ..models import GroupPermissionModel
from .base_dao import BaseDao


class PermissionDao(BaseDao):

    def add_permission(self, permission):
        # 如果存在相同app codename，则修改permission，否则新增permission
        new = Model.from_dict(permission)
        exiting = self.get_permission_by_app_and_codename(
            new.app, new.codename)
        if exiting:
            new.id = exiting.id
            self.session.merge(new)
            self.session.commit()
        else:
            self.session.add(new)
            self.session.commit()

    def get_permission_list(self):
        query = self.session.query(Model)
        return [_.to_dict() for _ in query.all()]

    def delete_permission_list(self):
        query = self.session.query(Model)
        query.delete()
        self.session.commit()

    def get_permission_by_app_and_codename(self, app, codename):
        query = self.session.query(Model)
        permission = query.filter(
            Model.app == app, Model.codename == codename).first()
        return permission

    def delete_permission_by_app_and_codename(self, app, codename):
        permission = self.get_permission_by_app_and_codename(app, codename)
        if permission:
            self.session.delete(permission)
            self.session.commit()

    def count(self):
        query = self.session.query(Model)
        return query.count()


class GroupPermissionDao(BaseDao):

    def add_group_permission(self, group_id, codename, app='nebula', extra_settings=''):
        # 根据app codename查询permission，再增加用户组权限
        permission = PermissionDao().get_permission_by_app_and_codename(app, codename)

        if permission:
            group_permission = GroupPermissionModel.from_dict(dict(
                group_id=group_id,
                permission_id=permission.id,
                extra_settings=extra_settings
            ))
            self.session.add(group_permission)
            self.session.commit()

    def update_group_permission(self, group_id, codename, app='nebula', extra_settings=''):
        # 根据app codename查询permission，再修改用户组权限
        permission = PermissionDao().get_permission_by_app_and_codename(app, codename)

        if permission:
            group_permission = GroupPermissionModel.from_dict(dict(
                group_id=group_id,
                permission_id=permission.id,
                extra_settings=extra_settings
            ))

            query = self.session.query(GroupPermissionModel)
            existing = query.filter(GroupPermissionModel.group_id == group_id,
                                    GroupPermissionModel.permission_id == permission.id).first()
            if existing:
                group_permission.id = existing.id
                self.session.merge(group_permission)
                self.session.commit()
            else:
                self.session.add(group_permission)
                self.session.commit()

    def get_group_permission(self, group_id, codename, app='nebula'):
        # 根据app codename查询permission，再查询group_permission
        permission = PermissionDao().get_permission_by_app_and_codename(app, codename)

        if permission:
            query = self.session.query(GroupPermissionModel)
            group_permission = query.filter(
                GroupPermissionModel.group_id == group_id, GroupPermissionModel.permission_id == permission.id).first()
            return group_permission

    def add_group_strategy_block(self, be_blocked_id, blocked_id):
        # 保存策略查看黑名单，be_blocked_id为被禁止查看的用户组id，block_id为禁止其他用户组查看本组策略的用户组id
        group_permission = self.get_group_permission(
            be_blocked_id, 'view_strategy')

        if group_permission:
            extra_settings = json.loads(group_permission.extra_settings)
            be_blocked_settings = extra_settings.get('be_blocked', [])

            if blocked_id not in be_blocked_settings:
                be_blocked_settings.append(blocked_id)
                extra_settings['be_blocked'] = be_blocked_settings
                self.update_group_permission(
                    be_blocked_id, 'view_strategy', extra_settings=json.dumps(extra_settings))
        else:
            extra_settings = {'be_blocked': [blocked_id]}
            self.add_group_permission(
                be_blocked_id, 'view_strategy', extra_settings=json.dumps(extra_settings))

    def delete_group_strategy_block(self, be_blocked_id, blocked_id):
        # 删除策略查看黑名单，be_blocked_id为被禁止查看的用户组id，block_id为禁止其他用户组查看本组策略的用户组id

        group_permission = self.get_group_permission(
            be_blocked_id, 'view_strategy')

        if group_permission:
            extra_settings = json.loads(group_permission.extra_settings)
            be_blocked_settings = extra_settings.get('be_blocked', [])

            if blocked_id in be_blocked_settings:
                be_blocked_settings.remove(blocked_id)
                extra_settings['be_blocked'] = be_blocked_settings
                self.update_group_permission(
                    be_blocked_id, 'view_strategy', extra_settings=json.dumps(extra_settings))

    def get_group_strategy_block(self, group_id):
        # 本组策略查看黑名单
        view_strategy = self.get_group_extra_settings(
            group_id, 'view_strategy', app='nebula')
        return json.loads(view_strategy) if view_strategy else {}

    def get_group_extra_settings(self, group_id, codename, app='nebula'):
        permission = PermissionDao().get_permission_by_app_and_codename(app, codename)

        if permission:
            query = self.session.query(GroupPermissionModel)
            group_permission = query.filter(
                GroupPermissionModel.group_id == group_id, GroupPermissionModel.permission_id == permission.id).first()

            if group_permission:
                return group_permission.extra_settings
