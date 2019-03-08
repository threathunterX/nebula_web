#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json

from threathunter_common.util import millis_now

from nebula.dao.base_dao import BaseDao
from nebula.dao.permission_dao import GroupPermissionDao
from nebula.models import GroupModel as Model
from nebula.models import UserGroupModel
from nebula.models import UserModel


class GroupDao(BaseDao):

    def _get_creator_name(self, creator):
        query = self.session.query(UserModel)
        user = query.filter(UserModel.id == creator).first()
        return user.name

    def get_group_detail_list(self):
        """
        返回用户管理所有用户组信息
        """
        query = self.session.query(Model)
        return [self.get_group_detail_by_id(_.id) for _ in query.all()]

    def get_group_by_id(self, group_id):
        query = self.session.query(Model)
        return query.filter(Model.id == group_id).first()

    def get_group_detail_by_id(self, group_id):
        """
        返回用户组的详细信息
        """
        group = self.get_group_by_id(group_id)
        query = self.session.query(UserModel)
        user = query.filter(UserModel.id == group.creator).first()

        detail = group.to_dict()
        detail['creator'] = user.name
        detail['users_count'] = UserGroupDao().get_users_count(group_id)

        grouppermission_dao = GroupPermissionDao()

        privileges = grouppermission_dao.get_group_extra_settings(
            group_id, app='nebula', codename='view_privileges')
        detail['privileges'] = json.loads(privileges) if privileges else []

        view_strategy = grouppermission_dao.get_group_extra_settings(
            group_id, app='nebula', codename='view_strategy')
        view_strategy = json.loads(view_strategy) if view_strategy else {}
        detail['blocked'] = view_strategy.get('blocked', [])

        return detail

    def add_group(self, group):
        # 新建用户组时，保存可查看页面列表和禁止查看本组策略的用户组列表
        privileges = group.get('privileges', [])
        blocked = group.get('blocked', [])

        group = Model.from_dict(group)
        self.session.add(group)
        self.session.commit()

        group_permissiondao = GroupPermissionDao()
        # 保存用户组可查看页面
        group_permissiondao.add_group_permission(
            group.id, codename='view_privileges', extra_settings=json.dumps(privileges))

        # 保存禁止的用户组，和被禁止用户组增加新的用户组id
        view_strategy = {'blocked': blocked}
        group_permissiondao.add_group_permission(
            group.id, codename='view_strategy', extra_settings=json.dumps(view_strategy))
        for be_blocked_id in blocked:
            group_permissiondao.add_group_strategy_block(
                be_blocked_id, group.id)

    def update_group(self, group_id, group):
        # 修改用户组时，保存可查看页面列表和禁止查看本组策略的用户组列表
        privileges = group.get('privileges', [])
        blocked = group.get('blocked', [])

        query = self.session.query(Model)
        existing = query.filter(Model.id == group_id).first()

        if existing:
            group['creator'] = existing.creator
            group['create_time'] = existing.create_time
            group = Model.from_dict(group)
            group.id = existing.id
            self.session.merge(group)
            self.session.commit()

            group_permissiondao = GroupPermissionDao()

            # 保存用户组查看页面权限
            group_permissiondao.update_group_permission(
                group.id, codename='view_privileges', extra_settings=json.dumps(privileges))

            # 保存用户组禁止查看本组策略的其他用户组
            extra_settings = group_permissiondao.get_group_extra_settings(
                group.id, codename='view_strategy')

            if extra_settings:
                extra_settings = json.loads(extra_settings)
                old_blocked = extra_settings.get('blocked', [])

                for old_blocked_group in list(set(old_blocked) - set(blocked)):
                    group_permissiondao.delete_group_strategy_block(
                        old_blocked_group, group.id)

                for new_blocked_group in list(set(blocked) - set(old_blocked)):
                    group_permissiondao.add_group_strategy_block(
                        new_blocked_group, group.id)

                extra_settings['blocked'] = blocked
                group_permissiondao.update_group_permission(
                    group.id, 'view_strategy', extra_settings=json.dumps(extra_settings))

            else:
                view_strategy = {'blocked': blocked}
                group_permissiondao.add_group_permission(
                    group.id, codename='view_strategy', extra_settings=json.dumps(view_strategy))
                for be_blocked_id in blocked:
                    group_permissiondao.add_group_strategy_block(
                        be_blocked_id, group.id)

    def get_manage_groups(self, group_id):
        # 根据用户组id查询可以查看的所有用户组id
        group = self.get_group_by_id(group_id)

        if group.is_root():
            return [1, 2]
        elif group.is_manager():
            groups = self.session.query(Model).filter(
                Model.id.notin_([1, 2])).all()
            return [_.id for _ in groups] if groups else []
        else:
            return []

    def get_group_strategy_access(self):
        query = self.session.query(Model).filter(Model.id.notin_([1, 2]))
        return [{'id': _.id, 'name': _.name} for _ in query.all()]


class UserGroupDao(BaseDao):

    def _get_user_group(self, user_id, group_id):
        """
        查询用户是否存在用户组
        """
        query = self.session.query(UserGroupModel)
        return query.filter(UserGroupModel.user_id == user_id, UserGroupModel.group_id == group_id).first()

    def add_user_group(self, user_group):
        new = UserGroupModel.from_dict(user_group)
        exiting = self._get_user_group(new.user_id, new.group_id)
        if not exiting:
            self.session.add(new)
            self.session.commit()

    def get_group_by_user(self, user_id):
        query = self.session.query(UserGroupModel)
        user_group = query.filter(UserGroupModel.user_id == user_id).first()
        group = GroupDao().get_group_detail_by_id(user_group.group_id)
        return group

    def get_users_count(self, group_id):
        """
        返回用户组所有用户总数
        """
        query = self.session.query(UserGroupModel)
        return query.filter(UserGroupModel.group_id == group_id).count()

    def update_group_id(self, user_id, group_id):
        query = self.session.query(UserGroupModel)
        user_group = query.filter(UserGroupModel.user_id == user_id).first()
        user_group.group_id = group_id
        user_group.last_modified = millis_now()
        self.session.merge(user_group)
        self.session.commit()
