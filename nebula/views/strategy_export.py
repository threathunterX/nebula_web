#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from os import path as opath
import json
import logging
import datetime
import base64
import hashlib
import tornado
from Crypto.Cipher import DES

from nebula_meta.model.strategy import Strategy

import settings
from nebula.views.base import BaseHandler
from nebula.dao.user_dao import authenticated
from nebula.dao.group_dao import GroupPermissionDao
from nebula.dao.strategy_dao import StrategyCustDao
from nebula_strategy.generator.online_gen import gen_variables_from_strategy

logger = logging.getLogger('nebula.api.strategy_export')

DES_Salt = hashlib.sha1(settings.StrategyExport_Salt).hexdigest()[:8]

sep = '\n'


def encrypt_des(key, text):
    des = DES.new(key, DES.MODE_ECB)
    reminder = len(text) % 8
    # pad 8 bytes
    if reminder == 0:
        text += '\x08' * 8
    else:
        text += chr(8 - reminder) * (8 - reminder)
    return base64.b32encode(des.encrypt(text))


# 策略导入时，对每个策略json字符串进行des解密
def decrypt_des(key, text):
    text = base64.b32decode(text)
    des = DES.new(key, DES.MODE_ECB)
    text = des.decrypt(text)
    pad = ord(text[-1])
    if pad == '\x08':
        return text[:-8]
    return text[:-pad]


class StrategyExportHandler(BaseHandler):
    REST_URL = '/nebula/strategy/export'

    @authenticated
    def post(self):
        """
        策略导出接口

        @API
        summary: 策略导出接口
        notes: 根据策略app和name导出策略
        tags:
          - nebula
        parameters:
          - name: strategies
            in: body
            required: true
            type: json
            description: strategy list
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        try:
            if self.group.is_root():
                return self.process_error(-1, 'root用户组没有权限导出策略')
            elif self.group.is_manager():
                be_block_groups_ids = []
            else:
                view_strategy = GroupPermissionDao().get_group_strategy_block(self.group.id)
                be_block_groups_ids = view_strategy.get('be_blocked', [])

            strategies = json.loads(self.request.body)
            strategies_export = []
            strategy_dao = StrategyCustDao()

            # 根据策略app和name筛选用户组权限
            for s in strategies:
                strategy = strategy_dao.get_strategy_by_app_and_name(s['app'], s[
                                                                     'name'])
                if strategy.group_id in be_block_groups_ids:
                    return self.process_error(-1, '没有权限导出策略')

                strategy.group_id = 0
                strategy_encrypt = encrypt_des(DES_Salt, strategy.get_json())
                strategies_export.append('{}:{}'.format(
                    strategy.name, strategy_encrypt))

            # 删除服务器保留两天前的文件
            export_path = settings.StrategyExport_Path
            del_list = os.listdir(export_path)
            for f in del_list:
                del_path = opath.join(export_path, f)
                if f.startswith('NEBULA策略') and opath.isfile(del_path):
                    date = int(f.split('_')[1])
                    today = int(datetime.datetime.now().strftime('%Y%m%d'))
                    if date - today > 2:
                        os.remove(del_path)

            filename = 'NEBULA策略_{}.txt'.format(
                datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            export_file = opath.join(export_path, filename)
            with open(export_file, 'w') as f:
                f.writelines(sep.join(strategies_export))

            self.finish(json.dumps(
                {"status": 200, "msg": "ok", "download_path": filename}))
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '策略导出失败，请联系管理员')


class StrategyDownloadHandler(BaseHandler):

    REST_URL = '/nebula/strategy/export/{filename}'

    @authenticated
    def get(self, filename):
        """
        策略文件下载接口

        @API
        summary: 根据策略导出的文件名，返回下载文件
        notes: 导出策略文件下载
        tags:
          - nebula
        parameters:
          -
            name: filename
            in: path
            required: true
            type: string
            description: 策略文件名
        """
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition',
                        'attachment; filename=' + filename)

        export_path = settings.StrategyExport_Path
        export_file = opath.join(export_path, filename)
        if opath.isfile(export_file):
            with open(export_file, 'rb') as f:
                data = f.read()
                self.write(data)
            self.finish()
        else:
            raise tornado.web.HTTPError(404)


class StrategyImportHandler(BaseHandler):

    REST_URL = '/nebula/strategy/import'

    @authenticated
    def post(self):
        """
        策略导入接口

        @API
        summary: 根据策略导出的文件，导入生成新策略
        notes: 策略导入
        tags:
          - nebula
        parameters:
          - name: try_import
            in: path
            required: false
            type: boolean
            default: true
            description: 为真时只作尝试，不实际触发
          - name: body
            in: body
            required: true
            type: file
            description: 导出的策略文件内容
        """
        # 判断导入策略是否为尝试导入
        self.set_header('content-type', 'application/json')
        try_import = self.get_argument('try_import', 'true')
        try_import = True if try_import == 'true' else False

        # root用户组不可以创建策略
        # manager用户组、普通用户组可以创建策略
        if self.group.is_root():
            return self.process_error(-1, "root用户组没有权限创建策略")
        elif self.group.is_manager():
            be_block_groups_ids = []
        else:
            view_strategy = GroupPermissionDao().get_group_strategy_block(self.group.id)
            be_block_groups_ids = view_strategy.get('be_blocked', [])

        try:
            # 获取上传文件
            strategy_encrypt = []
            file_metas = self.request.files['file']
            if file_metas:
                meta = file_metas[0]
                strategy_encrypt = meta['body'].strip().split(sep)
        except Exception as e:
            logger.error(e)
            self.process_error(-1, '策略导入失败，请联系管理员')

        import_result = {
            'success_add': [],
            'success_modify': [],
            'fail_permission': [],
            'fail_error': []
        }
        group_id = self.group.id
        strategy_dao = StrategyCustDao()

        for s in strategy_encrypt:
            try:
                if not s:
                    continue
                # 策略字符串进行解密
                strategy_name, encrypt_str = s.split(':')
                decrypt_str = decrypt_des(DES_Salt, encrypt_str)
                new_strategy = Strategy.from_dict(json.loads(decrypt_str))
                # do checking
                gen_variables_from_strategy(new_strategy, effective_check=False)
            except Exception as e:
                logger.error(e)
                return self.process_error(-1, '导入的规则内容有误({})，请重新检查并更正后进行导入'.format(str(e)))

            try:
                # 判断策略是否存在，及是否有权限新增、修改
                existing_strategy = strategy_dao.get_strategy_by_app_and_name(
                    new_strategy.app, new_strategy.name)

                if existing_strategy:
                    if existing_strategy.group_id in be_block_groups_ids:
                        import_result['fail_permission'].append(strategy_name)
                    else:
                        new_strategy.group_id = existing_strategy.group_id
                        new_strategy.score = existing_strategy.score
                        new_strategy.status = 'inedit'
                        import_result['success_modify'].append(strategy_name)
                else:
                    new_strategy.group_id = group_id
                    new_strategy.score = 0
                    new_strategy.status = 'inedit'
                    import_result['success_add'].append(strategy_name)

                if not try_import:
                    strategy_dao.add_strategy(new_strategy)

            except Exception as e:
                logger.error(e)
                import_result['fail_error'].append(strategy_name)

        for status in import_result:
            import_result[status] = list(set(import_result[status]))

        self.finish(json.dumps(
            {"status": 200, "msg": "ok", "values": import_result}))
