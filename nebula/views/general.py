#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json

from tornado.web import StaticFileHandler, RequestHandler

import settings

from nebula.dao.user_dao import authenticated
from threathunter_common.geo.geoutil import get_cities_in_china, get_provinces_in_china
from .base import BaseHandler

class CustomizedFileHandler(StaticFileHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        
class IndexHandler(BaseHandler):
    @authenticated
    def get(self):
        self.base_render("index.html")

class LoginHandler(BaseHandler):
    def get(self):
        self.base_render("index.html")

class ProjectHandler(BaseHandler):
    @authenticated
    def get(self):
        self.base_render("project.html")

class SwaggerUIHandler(RequestHandler):
    def initialize(self, assets_path, **kwds):
        self.assets_path = assets_path

    def get_template_path(self):
        return self.assets_path

    def get(self):
        self.render('index.html')

class WebConfigHandler(BaseHandler):
    REST_URL = '/nebula/web/config'
    def get(self):
        self.write(json.dumps(dict( (k, v) for k,v in settings._config.config_data.iteritems()
                                    if k[0].isupper() and not isinstance(v, set))))

class AllCityHandler(BaseHandler):
    @authenticated
    def get(self):
        """
        获取中国所有城市的接口
        """
        self.write(json.dumps(dict(status=0,msg='',values=list(set(get_cities_in_china())))))
        
class AllProvinceHandler(BaseHandler):
    @authenticated
    def get(self):
        """
        获取中国所有省份的接口
        
        关于没有指定省份所有城市的接口说明:
        省、市只能选一个没有相关性，且市里面有搜索.
        """
        self.write(json.dumps(dict(status=0,msg='',values=list(set(get_provinces_in_china())))))
        
class APIVersionHandler(BaseHandler):
    
    def get(self, ):
        """
        返回api的版本 ex. 1.3.0
        @todo add to api doc
        """
        self.finish(settings.API_VERSION)

class GeoStatsHandler(BaseHandler):

    REST_URL = '/platform/geoinfo'

    def get(self, ):
        """
        Get the geo information of one ip

        @API
        summary: ip geo information
        notes: Get the geo information of one ip
        tags:
          - platform
        parameters:
          -
            name: ip
            in: query
            required: false
            type: string
            description: ip address
          -
            name: mobile
            in: query
            required: false
            type: string
            description: mobile phone number
        produces:
          - application/json
        """
        from threathunter_common.geo.geoutil import get_ip_location
        from threathunter_common.util import utf8
        from threathunter_common.geo.phonelocator import get_geo
        import ipaddr
        ip = self.get_argument('ip', "")
        mobile = self.get_argument('mobile', "")

        result = "未知"
        try:
            if ip:
                ip_addr = ipaddr.IPAddress(ip)
                if ip_addr.is_loopback or ip_addr.is_private:
                    result = "内网地址"
                else:
                    result = get_ip_location(ip)
            elif mobile:
                result = get_geo(mobile)
        except Exception as ignore:
            pass

        result = utf8(result)
        self.finish(json.dumps({"address": result}))
