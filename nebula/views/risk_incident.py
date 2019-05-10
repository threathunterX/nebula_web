#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import json
import json
import logging
from tornado.web import RequestHandler
from enum import Enum
from enum import unique
import requests
import json
import hashlib
import base64
from datetime import datetime
from Crypto.Cipher import AES
from Crypto import Random
from threathunter_common.util import json_dumps, ip_match
from ..dao.config_dao import ConfigCustDao

from nebula.dao.user_dao import authenticated
from .base import BaseHandler
#from .incident_stat import parse_host_url_path, get_latest_incident, get_current_hour_timestamp
#from .data_client import get_global_statistic
from ..dao.riskincident_dao import IncidentDao
from .view_util import mapping_name_to_visual
import settings


hour = 60 * 60 * 1000
logger = logging.getLogger('nebula.api.incident')


class IncidentListHandler(BaseHandler):

    REST_URL = '/platform/risk_incidents'

    @authenticated
    def get(self):
        """
        list all incidents

        @API
        summary: list all incidents
        notes: get details for incidents
        tags:
          - platform
        responses:
          '200':
            description: incidents
            schema:
              $ref: '#/definitions/Incident'
          default:
            description: Unexcepted error
            schema:
              $ref: '#/definitions/Error'
        """

        self.set_header('content-type', 'application/json')

        try:
            incident_list = IncidentDao().get_incident_list()
            self.finish(json_dumps(
                {'status': 0, 'msg': 'ok', 'values': incident_list}))
        except Exception as e:
            logger.error(e)
            self.process_error(400, 'fail to get incidents from database')

    @authenticated
    def post(self):
        """
        add a list of incidents

        @API
        summary: add a list of incidents
        notes: add a list of incidents
        tags:
          - platform
        parameters:
          -
            name: incidents
            in: body
            requires: true
            type: json
            description: the list of the incidents json
        produces:
          - application/json
        """

        self.set_header('content-type', 'application/json')
        incident_list = json.loads(self.request.body)
        interval = 3600 * 1000

        try:
            # 离线计算重新计算时,先删除之前数据库存储的风险事件记录,再存入新增的风险事件
            if incident_list:
                first = incident_list[0]
                start_time = first['start_time'] / interval * interval
                end_time = start_time + interval

                incident_dao = IncidentDao()
                incident_dao.remove_incidents(start_time, end_time)

                for _ in incident_list:
                    incident_dao.add_incident(_)

            self.finish(json_dumps({'status': 0, 'msg': 'ok', 'values': []}))
        except Exception as e:
            logger.error(e)
            self.process_error(400, 'fail to add incidents to database')


class IncidentQueryHandler(BaseHandler):

    REST_URL = '/platform/risks/{id}'

    @authenticated
    def get(self, id):
        """
        get a specific incident detail

        @API
        summary: get a specific incident detail
        notes: get a specific incident detail
        tags:
          - platform
        parameters:
          -
            name: id
            in: path
            required: true
            type: integer
            description: id of the incident
        """

        self.set_header('content-type', 'application/json')
        try:
            incident = IncidentDao().get_incident_by_id(id).to_dict()
            self.finish(json_dumps(
                {'status': 0, 'msg': 'ok', 'values': incident}))
        except Exception as e:
            logger.error(e)
            self.process_error(400, 'fail to get incident from database')

    @authenticated
    def put(self, id):
        """
        update a specific incident detail

        @API
        summary: update a specific incident detail
        notes: update a specific incident detail
        tags:
          - platform
        parameters:
          -
            name: id
            in: path
            required: true
            type: integer
            description: id of the incident
          -
            name: status
            in: body
            required: true
            type: integer
            description: status of the incident
        """

        self.set_header('content-type', 'application/json')
        body = json.loads(self.request.body)
        status = str(body.get('status', 0))

        try:
            IncidentDao().update_status(incident_id=id, status=status)

            self.finish((json_dumps({'status': 0, 'msg': 'ok', 'values': []})))
        except Exception as e:
            logger.error(e)
            self.process_error(400, 'fail to update incident to database')


#class RisksStatisticsHandler(BaseHandler):
#
#    REST_URL = '/platform/risks/statistics'
#
#    @authenticated
#    def get(self):
#        """
#        get risk incident statistics list
#
#        @API
#        summary: get risk incident statistics list
#        notes: list split every hour
#        tags:
#          - platform
#        parameters:
#          -
#            name: start_time
#            in: query
#            required: true
#            type: integer
#            description: start time of the list
#          -
#            name: end_time
#            in: query
#            required: true
#            type: integer
#            description: start time of the list
#        responses:
#          '200':
#            description: incidents
#            schema:
#              $ref: '#/definitions/RiskStatistics'
#          default:
#            description: Unexcepted error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#
#        self.set_header('content-type', 'application/json')
#        start_time = int(self.get_argument('start_time', 0))
#        end_time = int(self.get_argument('end_time', 0))
#        if not start_time or not end_time:
#            self.process_error(400, 'parameters error')
#
#        try:
#            incident_list = sorted(
#                IncidentDao().get_statistic_data(start_time, end_time))
#        except Exception as e:
#            logger.error(
#                "fail to get incidents statistics from database: %s", e)
#            self.process_error(
#                400, 'fail to get incidents statistics from database')
#
#        try:
#            incident_map = {int(ts): int(count) for ts, count in incident_list}
#            statistics_list = [{ts: incident_map.get(ts, 0)} for ts in range(
#                start_time, end_time, 3600000)]
#            ts = get_current_hour_timestamp()
#            if end_time > ts:
#                count_var = 'total__visit__incident_distinct_ip__1h__slot'
#                ret = get_global_statistic(var_list=[count_var])
#                if ret:
#                    count = ret.get(count_var, 0)
#                    # add the current hour
#                    statistics_list[-1] = {ts: count}
#
#            self.finish(json_dumps(statistics_list))
#        except Exception as e:
#            logger.error(e)
#            self.process_error(400, 'fail to statistic risks')


class RisksHistoryHandler(BaseHandler):

    REST_URL = '/platform/risks/history'

    @authenticated
    def get(self):
        """
        get risk incident history list

        @API
        summary: get risk incident history list
        notes: risk incident list
        tags:
          - platform
        parameters:
          -
            name: start_time
            in: query
            required: true
            type: integer
            description: start time of the list
          -
            name: end_time
            in: query
            required: true
            type: integer
            description: start time of the list
          -
            name: offset
            in: query
            required: true
            type: integer
            description: the page of the list
          -
            name: limit
            in: query
            required: true
            type: integer
            description: the limit of one page
          -
            name: keyword
            in: query
            required: false
            type: string
            description: query key word of the incident
          -
            name: status
            in: query
            required: false
            type: integer
            description: choose the status of the incident
        responses:
          '200':
            description: incidents
            schema:
              $ref: '#/definitions/RiskStatistics'
          default:
            description: Unexcepted error
            schema:
              $ref: '#/definitions/Error'
        """

        self.set_header('content-type', 'application/json')
        start_time = int(self.get_argument('start_time', 0))
        end_time = int(self.get_argument('end_time', 0))
        keyword = self.get_argument('keyword', '')
        offset = int(self.get_argument('offset', 1))
        limit = int(self.get_argument('limit', 10))
        status = str(self.get_argument('status', ''))

        try:
            incident_dao = IncidentDao()
            status_statistic = incident_dao.get_status_statistics(
                start_time, end_time)
            incident_list = incident_dao.get_detail_list(
                start_time, end_time, offset, limit, keyword, status)
        except Exception as e:
            logger.error(e)
            self.process_error(400, 'fail to get incidents from database')
            return
        try:
            risks = dict()
            for _ in incident_list:
                _["strategies"] = mapping_name_to_visual(_["strategies"])
            risks['count'] = sum(status_statistic.values())
            risks['status'] = status_statistic
            risks['items'] = incident_list

            self.finish(json_dumps(risks))
        except Exception as e:
            logger.error(e)
            self.process_error(400, 'fail to statistic risks')


#class RisksRealtimeHandler(BaseHandler):
#    REST_URL = '/platform/risks/realtime'
#
#    @authenticated
#    def get(self):
#        """
#        get risk incident realtime list
#
#        @API
#        summary: get risk incident realtime list
#        notes: risk incident list
#        tags:
#          - platform
#        parameters:
#          -
#            name: offset
#            in: query
#            required: false
#            type: integer
#            description: the page of the list
#          -
#            name: limit
#            in: query
#            required: false
#            type: integer
#            description: the limit of one page
#          -
#            name: keyword
#            in: query
#            required: false
#            type: string
#            description: query key word of the incident
#        responses:
#          '200':
#            description: incidents
#            schema:
#              $ref: '#/definitions/RiskStatistics'
#          default:
#            description: Unexcepted error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#
#        self.set_header('content-type', 'application/json')
#        keyword = self.get_argument('keyword', '')
#        offset = int(self.get_argument('offset', 0))
#        limit = int(self.get_argument('limit', 20))
#        blank_return = dict(count=0, items=[], status={i: 0 for i in range(0, 4)})
#        if not settings.Enable_Online:
#            self.finish(json_dumps(blank_return))
#            return
#
#        incident_statistics = get_realtime_incident(offset, limit, keyword)
#        if not incident_statistics:
#            incident_statistics = dict(count=0, items=[])
#
#        try:
#            incident_statistics['status'] = {i: 0 for i in range(0, 4)}
#
#            self.finish(json_dumps(incident_statistics))
#        except Exception as e:
#            logger.error(e)
#            self.process_error(400, 'fail to statistic risks')
#
#
#def parse_host_url_path(url):
#    if url.find('/') == -1:
#        # ex. 183.131.68.9:8080, auth.maplestory.nexon.com:443
#        host = url
#        url_path = ''
#    else:
#        if url.startswith('http') or url.startswith('https'):
#            # 有协议的, 需要扩充
#            segs = url.split('/',3)
#            host = '/'.join(segs[:3])
#            url_path = segs[-1]
#        else:
#            host, url_path = url.split('/',1)
#    return host, url_path
#
#def get_realtime_incident(page, count, keyword):
#    try:
#        key_variable = 'ip__visit__incident_score__1h__slot'
#        var_list = [
#            'ip__visit__incident_score__1h__slot',
#            'ip__visit__incident_min_timestamp__1h__slot',
#            'ip__visit__user_incident_count__1h__slot',
#            'ip__visit__page_incident_count__1h__slot',
#            'ip__visit__tag_incident_count__1h__slot',
#            'ip__visit__scene_incident_count_strategy__1h__slot',
#            'ip__visit__incident_max_rate__1h__slot',
#            'ip__visit__did_incident_count__1h__slot'
#        ]
#        incident_statistics = dict(count=0, items=[])
#        incident_list = list()
#
#        property_values = get_latest_incident(
#            var_list, key=keyword, key_variable=key_variable, count=count, page=page)
#
#        if property_values:
#            result = property_values.get('result', {})
#            incident_statistics['count'] = property_values.get('total', 0)
#
#            for key, variables in result.items():
#                if not ip_match(key):
#                    continue
#
#                incident = dict()
#                incident['ip'] = key
#                incident['associated_events'] = list()
#                incident['start_time'] = variables.get(
#                    'ip__visit__incident_min_timestamp__1h__slot', 0)
#                incident['strategies'] = mapping_name_to_visual(
#                    variables.get("ip__visit__scene_incident_count_strategy__1h__slot", {}))
#                incident['hit_tags'] = variables.get(
#                    'ip__visit__tag_incident_count__1h__slot', {})
#                incident['risk_score'] = variables.get(
#                    'ip__visit__incident_score__1h__slot', 0)
#                incident['uri_stems'] = variables.get(
#                    'ip__visit__page_incident_count__1h__slot', {})
#                incident['hosts'] = dict()
#                for uri, count in incident['uri_stems'].items():
#                    host, _ = parse_host_url_path(uri)
#                    if incident['hosts'].get(host, None):
#                        incident['hosts'][host] += count
#                    else:
#                        incident['hosts'][host] = count
#                incident['most_visited'] = sorted(incident['uri_stems'].items(), lambda x, y: cmp(
#                    x[1], y[1]), reverse=True)[0][0] if incident['uri_stems'] else ''
#                incident['peak'] = round(variables.get(
#                    'ip__visit__incident_max_rate__1h__slot', 0) or 0, 2)
#                incident['dids'] = variables.get(
#                    'ip__visit__did_incident_count__1h__slot', {})
#                incident['associated_users'] = variables.get(
#                    'ip__visit__user_incident_count__1h__slot', {})
#                incident['users_count'] = len(incident['associated_users'])
#                incident['associated_orders'] = dict()
#                incident['status'] = ''
#
#                incident_list.append(incident)
#
#            incident_list.sort(key=lambda v: v['risk_score'], reverse=True)
#            incident_statistics['items'] = incident_list
#
#        return incident_statistics
#    except Exception as e:
#        logger.error(e)
#        return incident_statistics


def AesEncryptSeg(ip, SNKEY):
    remainder = len(ip) % 16
    if remainder:
        padded_value = ip + '\0' * (16 - remainder)
    else:
        padded_value = ip
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(SNKEY, AES.MODE_CFB, iv, segment_size=128)
    value = cipher.encrypt(padded_value)[:len(ip)]
    ciphertext = iv + value
    return base64.encodestring(ciphertext).strip()


def AesDecryptSeg(ip, SNKEY):
    data = base64.decodestring(ip)
    cihpertxt = data[AES.block_size:]
    remainder = len(cihpertxt) % 16
    if remainder:
        padded_value = cihpertxt + '\0' * (16 - remainder)
    else:
        padded_value = cihpertxt
    cryptor = AES.new(SNKEY, AES.MODE_CFB, data[0:AES.block_size], segment_size=128)
    plain_text = cryptor.decrypt(padded_value)
    return plain_text[0:len(cihpertxt)]


def request_check_ip(ip_list, SNUSER, SNKEY):
    ips = []
    for ip in ip_list:
        u = {}
        u["ip"] = ip
        ips.append(u)
    ips = json.dumps(ips)
    aes_ips_str = AesEncryptSeg(ips, SNKEY)
    payload = {
        "snuser": SNUSER,
        "data": aes_ips_str,
    }
    SRV_URL = "https://api.threathunter.cn/zhbpro/"
    POST_URL = SRV_URL + "blackip_check"
    r = requests.post(POST_URL, data=json.dumps(payload))
    r_json = r.json()
    status_code = r_json['status']
    if status_code == 200:
        data = AesDecryptSeg(r_json["data"], SNKEY)
    else:
        data = ''
    errmsg = r_json['errmsg']
    return (status_code, data, errmsg)


def request_check_phone(phones, SNUSER, SNKEY):
    users = []
    for user in phones:
        u = {}
        usha1 = hashlib.sha1(user).hexdigest()
        u["user"] = usha1
        users.append(u)
    pstr = json.dumps(users)
    cstr = AesEncryptSeg(pstr, SNKEY)
    payload = {
        "snuser": SNUSER,
        "data": cstr
    }
    SRV_URL = "https://api.threathunter.cn/zhbpro/"
    POST_URL = SRV_URL + "phone_no_check"
    r = requests.post(POST_URL, data=json.dumps(payload))
    r_json = r.json()
    status_code = r_json.get('status')
    if status_code == 200:
        data = AesDecryptSeg(r_json.get('data'), SNKEY)
    else:
        data = ''
    msg = r_json.get('errmsg')
    return (status_code, data, msg)


def config_from_database():
    config = ConfigCustDao().list_all_config()
    logger.error('SNUSER result {}'.format(config))
    SNUSER = ''
    SNKEY = ''
    for v in config:
        key = v.get('key')
        if key == 'SNUSER':
            SNUSER = v.get('value')
        elif key == 'SNKEY':
            SNKEY = v.get('value')
        else:
            pass
    return (SNUSER, SNKEY)

class BlackHandler(RequestHandler):
    @authenticated
    def get(self):
        """
        :argument
        type: black_ip / phone_number
        ip: black_ip
        phone_number: phone_number
        :return:
        status_code: status code
        status_message: status message
        result: result
        """
        result = dict(
            status_code=500,
            status_message='program error',
            result=[],
        )
        (SNUSER, SNKEY) = config_from_database()
        if SNUSER == '' or SNKEY == '':
            result['status_message'] = 'configuration is None'
            result['status_code'] = 412
            self.write(json.dumps(result))
        else:
            _type = self.get_argument("type", "")
            if _type == 'black_ip':
                ip = self.get_argument("ip", "")
                if ip != '':
                    ips = [ip]
                    status_code, data, msg= request_check_ip(ips, SNUSER, SNKEY)
                else:
                    status_code = 412
                    msg = 'Precondition Failed'
                    data = []
            elif _type == 'phone_number':
                phone_number = self.get_argument("phone_number", "")
                if phone_number != '':
                    phones = [str(phone_number)]
                    status_code, data, msg = request_check_phone(phones, SNUSER, SNKEY)
                else:
                    status_code = 412
                    msg = 'Precondition Failed'
                    data = []
            else:
                status_code = 412
                msg = 'Precondition Failed'
                data = []
            result['status_code'] = status_code
            result['result'] = data
            result['status_message'] = msg

            self.write(json.dumps(result))
