#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from threathunter_common.event import Event
from threathunter_common.util import millis_now, curr_timestamp

import settings
from .base import BaseHandler
from ..services.babel import get_client
from nebula.dao.user_dao import authenticated


logger = logging.getLogger('nebula.api.system')

now = curr_timestamp()
licenseinfo = dict()


def get_licenseinfo():
    global now, licenseinfo

    # 保存查询结果1分钟
    if (curr_timestamp() - now) > 60 or not licenseinfo:
        try:
            client = get_client(settings.LicenseInfo_redis,
                                settings.LicenseInfo_rmq)
            event = Event('nebula_web', 'licenseinfo', '', millis_now(), {})
            bbc, bbc_data = client.send(event, '', True, 10)

            if bbc:
                licenseinfo['expire'] = bbc_data.property_values.get(
                    'days', '')
                licenseinfo['version'] = bbc_data.property_values.get(
                    'info', '')
                now = curr_timestamp()
                return licenseinfo
            else:
                return None
        except Exception as e:
            logger.error(e)
            return None
    else:
        return licenseinfo


class LicenseInfoHandler(BaseHandler):

    REST_URL = '/system/license'

    @authenticated
    def get(self):
        """
        获取nebula证书信息

        @API
        summary: 获取nebula证书信息(new)
        description: nebula证书信息(new)
        tags:
          - system
        responses:
          '200':
            description: 返回一个对象
            schema:
              $ref: '#/definitions/Version'
          default:
            description: Unexcepted error
            schema:
              $ref: '#/definitions/Error'
        """

        license = get_licenseinfo()
        if license:
            return self.finish(license)
        else:
            return self.process_error(500, 'fail to get license config')
