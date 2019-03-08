#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import traceback
from os import path as opath
import json
import logging
import time
import datetime
import csv
import codecs

from threathunter_common.util import json_dumps

import settings
from nebula.dao.user_dao import authenticated
from nebula.dao import cache
from nebula.dao.notice_dao import NoticeDao
from nebula.views.base import BaseHandler
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger('nebula.api.notice_export')


class NoticeExportHandler(BaseHandler):
    REST_URL = '/platform/notices/export'

    @authenticated
    def get(self):
        """
        @API
        summary: 风险名单导出接口
        tags:
          - platform
        parameters:
          - name: key
            in: query
            required: false
            type: string
            description: notice key包含的字符串
          - name: strategy
            in: query
            required: false
            type: string
            description: notice命中的策略，支持多个策略名字
          - name: sceneType
            in: query
            required: false
            type: string
            description: notice命中的场景，支持多个场景
          - name: checkType
            in: query
            required: false
            type: string
            description: notice类型，支持多个类型
          - name: decision
            in: query
            required: false
            type: string
            description: notice操作建议类型，支持多个操作
          - name: fromtime
            in: query
            required: false
            type: integer
            description: notice报警时间应大于等于fromtime
          - name: endtime
            in: query
            required: false
            type: integer
            description: notice报警时间应小于等于endtime
          - name: filter_expire
            in: query
            required: false
            type: boolean
            description: notice是否过期
          - name: test
            in: query
            required: false
            type: boolean
            description: notice是否是测试名单
          - name: tag
            in: query
            required: false
            type: string
            description: filter notice strategy tag
        produces:
          - application/json
        """

        key = self.get_argument('key', default=None)
        fromtime = self.get_argument('fromtime', default=None)
        endtime = self.get_argument('endtime', default=None)
        # 命中策略
        strategies = self.get_arguments('strategy')
        # 命中场景
        scene_types = self.get_arguments('sceneType')
        # notice类型
        check_types = self.get_arguments('checkType')
        # 风险类型
        decisions = self.get_arguments('decision')
        filter_expire = self.get_argument('filter_expire', default='false')
        filter_expire = True if filter_expire == 'true' else False
        test = self.get_argument('test', default=None)
        tags = self.get_arguments('tag')  # 策略风险标签

        # 查询策略权重
        if cache.Strategy_Weigh_Cache is None:
            from nebula.dao.strategy_dao import init_strategy_weigh
            init_strategy_weigh()
        strategy_weigh = cache.Strategy_Weigh_Cache

        tag_strategy = filter(lambda s: list(set(tags) & (
            set(s['tags']))), cache.Strategy_Weigh_Cache.values())
        strategies.extend([s['name'] for s in tag_strategy])

        self.set_header('content-type', 'application/json')
        export_notices = []
        limit = 20000
        try:
            notice_dao = NoticeDao()
            # 查询白名单
            whitelists = dict(notice_dao.get_whitelist_whole())

            # 查询风险名单，得到2万条限制一共有几个文件
            _, page, notices = notice_dao.get_notices(is_checking=False, key=key, fromtime=fromtime,
                                                      endtime=endtime, strategies=strategies,
                                                      scene_types=scene_types, check_types=check_types,
                                                      decisions=decisions, filter_expire=filter_expire,
                                                      test=test, limit=limit)
            export_notices.append(notices)

            # 限制查询文件不超过5个
            if page > 5:
                self.finish(json_dumps(
                    {"status": -1, "msg": "导出条目超过10万条，请更改查询条件"}))
                return

            # 将所有风险名单放入export_notices，统一写入文件
            if page > 1:
                for i in range(2, page + 1):
                    _, _, notices = notice_dao.get_notices(is_checking=False, key=key, fromtime=fromtime,
                                                           endtime=endtime, strategies=strategies,
                                                           scene_types=scene_types, check_types=check_types,
                                                           decisions=decisions, filter_expire=filter_expire,
                                                           test=test, limit=limit, page=i)
                    export_notices.append(notices)
        except Exception as err:
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": "数据获取失败，请联系管理员"}))

        try:
            export_path = settings.NoticeExport_Path
            download_paths = []

            # 删除服务器保留一天前的文件
            del_list = os.listdir(export_path)
            for f in del_list:
                del_path = opath.join(export_path, f)
                if f.startswith('NEBULA风险名单') and opath.isfile(del_path):
                    date = f.split('_')[1]
                    today = datetime.datetime.now().strftime('%Y%m%d')
                    if date != today:
                        os.remove(del_path)

            # 写入csv文件
            headers = ['命中时间', '值类型', '风险值', '风险决策', '策略名称', '风险场景',
                       '子场景', '过期时间', '测试状态', '已设白名单', '风险分值', '省', '市',
                       '关联页面', '风险备注', '风险标签', '触发事件']

            for i in range(0, page):
                notices = export_notices[i]
                file_name = 'NEBULA风险名单_{}_{}.csv'.format(
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), i + 1)
                export_file = unicode(opath.join(export_path, file_name))

                # 写入第一行
                with open(export_file, 'wb') as csvfile:
                    csvfile.write(codecs.BOM_UTF8)
                    writer = csv.writer(
                        csvfile, dialect='excel', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(headers)

                    # 每一个风险名单写入一行
                    for n in notices:
                        # 判断白名单
                        if whitelists.has_key((n.key, n.check_type, n.test)):
                            white_notice = True
                        else:
                            white_notice = False

                        # 查询风险标签
                        if n.strategy_name and strategy_weigh and n.strategy_name in strategy_weigh:
                            tags = ','.join([tag for tag in strategy_weigh[
                                            n.strategy_name]['tags'] if tag])
                        else:
                            tags = ''

                        writer.writerow([
                            time.strftime('%Y/%m/%d %H:%M:%S',
                                          time.localtime(n.timestamp / 1000)),
                            n.check_type,
                            n.key,
                            n.decision,
                            n.strategy_name,
                            n.scene_name,
                            n.checkpoints,
                            time.strftime('%Y/%m/%d %H:%M:%S',
                                          time.localtime(n.expire / 1000)),
                            n.test,
                            white_notice,
                            n.risk_score,
                            n.geo_province.encode('utf-8'),
                            n.geo_city.encode('utf-8'),
                            n.uri_stem.encode('utf-8'),
                            n.remark.encode('utf-8'),
                            tags.encode('utf-8'),
                            json_dumps(n.trigger_event)
                        ])

                download_paths.append(
                    '/platform/notices/export/{}'.format(file_name))

            self.finish(json_dumps(
                {"status": 200, "msg": "ok", "values": download_paths}))

        except :
            logger.error(traceback.format_exc())
            self.finish(json_dumps({"status": -1, "msg": "服务配置错误，请联系管理员"}))
