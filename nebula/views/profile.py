#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json

from threathunter_common.event import Event
from threathunter_common.util import millis_now

from nebula.dao.user_dao import authenticated
from ..services.babel import get_profile_query_client, get_profile_account_risk_client, get_profile_page_risk_client
from .base import BaseHandler
from .incident_stat import find_ip_geo


logger = logging.getLogger('nebula.api.profile')


ip_location_variable = 'user__account__ip_last10_login_timestamp__profile'
alarm_increment_variable = 'user__visit__alarm_increment_times__profile'
hour_merge_variable = 'user__visit__hour_merge__profile'


def get_profile(key, key_type, variables):
    # 初始化profilequery RPC client
    property_values = {
        'profile_key_value': key,
        'profile_key_type': key_type,
        'variables': variables
    }
    client = get_profile_query_client()
    event = Event('nebula_web', 'profile_query', '',
                  millis_now(), property_values)

    # client发送event，如果RPC正常返回，则返回RPC server返回数据
    bbc, bbc_data = client.send(event, '', True, 10)
    profile_values = bbc_data.property_values if bbc else False
    return profile_values


def get_account_risk(current_day, start_day, end_day):
    # 查询profile账号安全场景
    property_values = {
        'current_day': current_day,
        'start_day': start_day,
        'end_day': end_day
    }
    client = get_profile_account_risk_client()
    event = Event('nebula_web', 'profile_account_risk',
                  '', millis_now(), property_values)

    # client发送event，如果RPC正常返回，则返回RPC server返回数据
    bbc, bbc_data = client.send(event, '', True, 10)
    property_values = bbc_data.property_values if bbc else False
    return property_values


def get_page_risk(current_day, pages):
    # 查询profile账号来源分析
    property_values = {
        'current_day': current_day,
        'pages': pages
    }
    client = get_profile_page_risk_client()
    event = Event('nebula_web', 'profile_page_risk',
                  '', millis_now(), property_values)

    # client发送event，如果RPC正常返回，则返回RPC server返回数据
    bbc, bbc_data = client.send(event, '', True, 10)
    property_values = bbc_data.property_values if bbc else False
    return property_values


class ProfileHandler(BaseHandler):
    REST_URL = '/platform/stats/profile'

    @authenticated
    def post(self):
        """
        获取id获取档案变量列表类型和值，封装Java RPC client

        @API
        summary: 档案
        notes: 档案变量类型和值
        tags:
          - platform
        parameters:
          -
            name: profile
            in: body
            required: true
            type: json
            description: 档案id和变量列表
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        profile = json.loads(self.request.body)
        key = profile.get('key', None)
        key_type = profile.get('key_type', None)
        variables = profile.get('variables', None)

        if not(key and key_type and variables):
            self.process_error(400, '档案id、类型及查询信息不能为空')

        if not(key_type in['user', 'ip', 'did', 'page'] and isinstance(variables, list)):
            self.process_error(400, '档案类型必须为user/ip/did/page且查询信息类型为列表')

        try:
            profile_values = get_profile(key, key_type, variables)
            # RPC返回超时，profile_values为False，正确返回时，判断status是否为200
            if profile_values is False:
                self.process_error(500, '服务器处理超时')
            else:
                status = profile_values.get('status', 500)
                if status == 200:
                    # 返回profile_values格式，例：
                    # {"status":200,"content":{"user__visit__alarm_increment_times__profile":{"type":"long","value":10}}}
                    # 只取变量的值，不需要其他type等信息
                    content = profile_values.get('content', {})
                    profile_variables = {key: values[
                        'value'] for key, values in content.items() if 'value' in values}

                    # ip_location_variable变量需要添加IP的location信息,按照timestamp大小排序
                    if ip_location_variable in profile_variables:
                        ip_location_dict = profile_variables.get(
                            ip_location_variable, {})
                        sort_timestamp_ip = sorted(ip_location_dict.items(
                        ), lambda x, y: cmp(x[1], y[1]), reverse=True)
                        ip_location_list = []
                        for ip, ts in sort_timestamp_ip:
                            country, province, city = find_ip_geo(ip)
                            ip_location_list.append({'ip': ip,
                                                     'timestamp': ts, 'location': city})
                        profile_variables[
                            ip_location_variable] = ip_location_list

                    # alarm_increment_variable变量需要加上默认值0
                    if alarm_increment_variable not in profile_variables:
                        profile_variables[alarm_increment_variable] = 0

                    # hour_merge_variable变量需要每个小时的数据，默认值为0
                    hour_merge_value = profile_variables.get(
                        hour_merge_variable, {})
                    profile_variables[hour_merge_variable] = [
                        hour_merge_value.get(format(i, '02d'), 0) for i in range(1, 25)]

                    self.finish(json.dumps(
                        {'status': status, 'msg': 'ok', 'values': profile_variables}))
                else:
                    self.finish(json.dumps(
                        {'status': status, 'msg': profile_values.get('msg', '服务器处理异常')}))
        except Exception as e:
            logger.error(e)
            self.process_error(500, '档案查询失败')


class ProfileAccountRiskHandler(BaseHandler):
    REST_URL = '/platform/stats/account_risk'

    @authenticated
    def get(self):
        """
        查询账户安全报表，一周趋势、今日统计接口

        @API
        summary: 查询一周趋势、今日统计
        tags:
          - platform
        parameters:
          - name: current_day
            in: query
            required: true
            type: timestamp
            description: 查询今日统计的日期时间戳
          - name: start_day
            in: query
            required: true
            type: timestamp
            description: 一周趋势统计开始日期时间戳
          - name: end_day
            in: query
            required: true
            type: timestamp
            description: 一周趋势统计开始日期时间戳
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        current_day = int(self.get_argument('current_day', 0))
        start_day = int(self.get_argument('start_day', 0))
        end_day = int(self.get_argument('end_day'), 0)

        try:
            if not (current_day and start_day and end_day):
                self.process_error(400, '一周趋势、今日统计时间不能为空')

            property_values = get_account_risk(current_day, start_day, end_day)
            if property_values is False:
                self.process_error(500, '服务器处理超时')
            else:
                status = property_values.get('status', 0)
                if status == 400:
                    self.process_error(400, property_values.get(
                        'msg', '一周趋势、今日统计时间不能为空'))
                else:
                    trend_day = property_values.get('trend_day', {})
                    trend_week = property_values.get('trend_week', {})
                    self.finish(json.dumps(
                        {'status': 200, 'msg': 'ok', 'values': {'trend_day': trend_day, 'trend_week': trend_week}}))
        except Exception as e:
            logger.error(e)
            self.process_error(500, '账号安全报表查询失败')


class ProfilePageRiskHandler(BaseHandler):
    REST_URL = '/platform/stats/page_risk'

    @authenticated
    def post(self):
        """
        账号来源分析接口

        @API
        summary: 账号来源分析，登录、注册page详情
        tags:
          - platform
        parameters:
          - name: body
            in: body
            required: true
            type: json
            description: 账号来源分析参数
        produces:
          - application/json
        """
        self.set_header('content-type', 'application/json')
        body = json.loads(self.request.body)
        current_day = int(body.get('current_day', 0))
        pages = body.get('pages', [])

        try:
            if not (current_day and pages):
                self.process_error(400, '账号来源分析参数不能为空')

            property_values = get_page_risk(current_day, pages)
            if property_values is False:
                self.process_error(500, '服务器处理超时')
            else:
                status = property_values.get('status', 0)
                if status == 400:
                    self.process_error(
                        400, property_values.get('msg', '账号来源分析参数不能为空'))
                else:
                    page_values = {page: property_values.get(page, {}) for page in pages}
                    self.finish(json.dumps(
                        {'status': 200, 'msg': 'ok', 'values': page_values}))
        except Exception as e:
            logger.error(e)
            self.process_error(500, '账号来源分析查询失败')
