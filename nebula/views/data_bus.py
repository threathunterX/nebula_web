## -*- coding: utf-8 -*-
#from __future__ import absolute_import
#import logging
#import traceback
#from datetime import datetime
#from collections import OrderedDict
#
#from tornado.escape import json_encode as origin_json_encode
#from tornado.web import RequestHandler
#
#from threathunter_common.metrics.metricsagent import MetricsAgent
#from threathunter_common.util import json_dumps, millis_now
#from nebula_utils.persist_compute.cache import get_statistic, get_all_statistic, ContinuousDB
#from nebula.views.base import BaseHandler
#from nebula.views.cache import CacheMixin, cache, API_Cache
#from nebula.views import data_client
#from common.utils import get_hour_strs, get_hour_strs_fromtimestamp
#from nebula.dao.user_dao import authenticated
#
#DEBUG_PREFIX = '==============='
#
#logger = logging.getLogger('nebula.api.data_bus')
#
#def json_encode(obj):
#    """
#    只针对标准返回json报文中values字段中的一层的字典, 如果值是set对象，类型转换成list. 然后再使用tornado.escape.json_encode
#    ex.
#    obj: {'status':0, 'values':{variable1:set(), variable2:list(), variable3:4, variable4:"a"}}
#    先转换成:
#    obj: {'status':0, 'values':{variable1:list(), variable2:list(), variable3:4, variable4:"a"}}
#    再json_encode
#    """
#    if not isinstance(obj, dict) or not obj.has_key("values"):
#        return origin_json_encode(obj)
#    
#    value_obj = obj['values']
#    if value_obj:
#        for k,v in value_obj.iteritems():
#            if isinstance(v, set):
#                value_obj[k] = list(v)
#            
#    return origin_json_encode(obj)
#
#
#class CleanCacheHandler(BaseHandler):
#    REST_URL = '/platform/stats/clean_cache'
#
#    @authenticated
#    def get(self):
#        """
#        为定时脚本提供刷新统计数据缓存的API接口
#        ex. /platform/stats/clean_cache?url=/platform/stats/offline_serial&method=GET
#        """
#        url = self.get_argument('url', default='')
#        method = self.get_argument('method', default='')
#        if not url:
#            self.finish(json_encode(dict(status=-1, error=u"清空API缓存url参数为必须")))
#            return
#        
#        if method:
#            prefix = '%s:%s' % (url, method)
#        else:
#            prefix = '%s:' % url
#            
#        for k in API_Cache:
#            if k.startswith(prefix):
#                del API_Cache[k]
#
#        self.finish(json_encode(dict(status=0)))
#
#
#class OnlineDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/online'
#
#    def get(self):
#        """
#        从实时获取数据的api接口
#
#        @API
#        summary: 从online获取当前5分钟数据
#        notes: 从online获取当前5分钟数据
#        tags:
#          - platform
#        parameters:
#          - name: key
#            in: query
#            required: false
#            type: string
#            description: 变量值
#          - name: key_type
#            in: query
#            required: true
#            type: string
#            description: 维度
#          - name: var_list
#            in: query
#            required: true
#            type: string
#            description: 变量列表
#        """
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        var_list = self.get_arguments('var_list')
#        try:
#            ret_stats = data_client.get_realtime_statistic(key, key_type, var_list)
#            if ret_stats:
#                self.finish(json_encode(dict(status=0, values=ret_stats)))
#            else:
#                self.finish(json_encode(dict(status=0, values=ret_stats, msg=u"realtime数据返回为空")))
#        except Exception as e:
#            logger.error(e)
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#
#
#class SlotDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/slot'
#
#    def get(self):
#        """
#        从slot获取数据的api接口
#        @todo key_type not none
#
#        @API
#        summary: 从slot获取当前小时数据
#        notes: 从slot获取当前小时数据
#        tags:
#          - platform
#        parameters:
#          - name: key
#            in: query
#            required: false
#            type: string
#            description: 变量值
#          - name: key_type
#            in: query
#            required: true
#            type: string
#            description: 维度
#          - name: var_list
#            in: query
#            required: true
#            type: string
#            description: 变量列表
#        """
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        var_list = self.get_arguments('var_list')
#        scenes = ['VISITOR', 'ACCOUNT', 'ORDER', 'TRANSACTION', 'MARKETING', 'OTHER']
#        subkeys = dict( (_,scenes) for _ in var_list if 'scene' in _)
#        logger.debug(DEBUG_PREFIX+u"input args: key %s, key_type %s, var_list %s, ", key, key_type, var_list)
#        try:
#            if key_type == 'total':
#                ret_stats = data_client.get_global_statistic(var_list, subkeys=subkeys)
#            else:
#                ret_stats = data_client.get_latest_statistic(key, key_type, var_list, subkeys=subkeys)
#
#            if ret_stats:
#                self.finish(json_encode(dict(status=0, values=ret_stats)))
#            else:
#                self.finish(json_encode(dict(status=0, values=ret_stats, msg=u"slot数据返回为空")))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#
#
#class SlotBaseLineDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/slot_baseline'
#
#    def get(self):
#        """
#        从slot两次查找数据的api接口
#        key_type:ip
#        key_var:ip__visit__dynamic_count__1h__slot
#        var_list:ip__visit__geo_dynamic_count__1h__slot
#        merge_list:ip__visit__geo_dynamic_count__1h__slot
#        @todo key_type not none
#        """
#        var_list = self.get_arguments('var_list')
#        merge_list = self.get_arguments('merge_list')
#        key_type = self.get_argument('key_type', default='') # 预留, 现在java是没管变量的维度的, 如果key_variable查出来的key不是var_list中的key_type的时候，还是会正常返回, 多半会返回空, 少数情况不同维度key相同的情况会返回异常数据
#        key_var = self.get_argument('key_var', default='')
#        # 其实slot并不支持key_var, list类型, 这点和offline baseline不同，支持多个key_var去获取key @issue
#
#        if len(var_list) < 1:
#            self.finish(json_encode(dict(status=-1, error=u"两次连续的查询的变量列表不能为空")))
#            return
#        
#        try:
#            ret_stats = data_client.get_latest_baseline_statistic(key_var, var_list, merge_list)
#            if ret_stats:
#                self.finish(json_encode(dict(status=0, values=ret_stats)))
#            else:
#                self.finish(json_encode(dict(status=0, values=ret_stats, msg=u"slot数据返回为空")))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#        
#class OfflineDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/offline'
#    
#    def get(self):
#        """
#        从离线每小时获取数据
#        @todo key_type not none
#        """
#        from_time = self.get_argument('from_time', default='')
#        end_time = self.get_argument('end_time', default='')
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        var_list = self.get_arguments('var_list')
#        
#        from_time = int(from_time) / 1000.0
#        end_time = int(end_time) / 1000.0
#        
#        #@todo 参数检查
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s", datetime.fromtimestamp(from_time))
#        
#        logger.debug(DEBUG_PREFIX + '查询的参数key:%s, key_type:%s, from_time:%s, end_time:% var_list:%s', str(key), str(key_type), from_time, end_time, var_list)
#        
#        try:
#            if not key:
#                key = "__GLOBAL__"
#            if key_type == "total":
#                key_type = "global"
#            ret_stats = data_client.get_offline_key_stat(key, key_type, from_time, var_list)
#            if ret_stats:
#                self.finish(json_encode(dict(status=0, values=ret_stats)))
#            else:
#                self.finish(json_encode(dict(status=0, values=ret_stats, msg=u"offline数据返回为空")))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#
#class OfflineBaseLineDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/offline_baseline'
#    
#    def get(self):
#        """
#        从离线每小时获取数据
#        对一个全局的榜单key_var拿出所有的key, 然后逐个key查询var_list, 如果其中有variable在merge_list当中，将会合并成一个总的统计字典(根据变量名放到merges字段中去), 必须知道拿出的key的key_type才能继续下一步查询
#        
#        """
#        from_time = self.get_argument('from_time', default='')
#        end_time = self.get_argument('end_time', default='')
#        key_type = self.get_argument('key_type', default='')
#        key_var = self.get_arguments('key_var')
#        var_list = self.get_arguments('var_list')
#        merge_list = set(self.get_arguments('merge_list'))
#
#        if len(var_list) < 1 or not key_type:
#            self.finish(json_encode(dict(status=-1, error=u"两次连续的查询的变量列表var_list为空 或者查询的全局统计信息的key_type未知")))
#            return
#        
#        from_time = int(from_time) / 1000.0
#        end_time = int(end_time) / 1000.0
#        
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s", datetime.fromtimestamp(from_time))
#        
#        logger.debug(DEBUG_PREFIX + u'查询的参数from_time:%s, end_time:%s, var_list:%s, key_var:%s, merge_list:%s, key_type:%s', from_time, end_time, var_list, key_var, merge_list, key_type)
#        
#        try:
#            ret_stats = data_client.get_offline_baseline(key_var, key_type, var_list, merge_list, int(from_time*1000))
#            if ret_stats:
#                self.finish(json_encode(dict(status=0, values=ret_stats)))
#            else:
#                self.finish(json_encode(dict(status=0, values=ret_stats, msg=u"offline数据返回为空")))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#
#class ProfileDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/profile'
#    
#    def get(self):
#        """
#        从profile获取数据
#        
#        """
#        #@to move here
#
#class OfflineSerialDataHandler(CacheMixin, RequestHandler):
#    REST_URL = '/platform/stats/offline_serial'
#    
#    @cache
#    def get(self):
#        """
#        从Aerospike获取一些连续小时的统计数据
#
#        @API
#        summary: 从Aerospike获取一些连续小时的统计数据
#        notes: 从Aerospike获取一些连续小时的统计数据
#        tags:
#          - platform
#        parameters:
#          -
#            name: from_time
#            in: query
#            required: true
#            type: integer
#            description: 起始时间
#          -
#            name: end_time
#            in: query
#            required: true
#            type: integer
#            description: 结束时间
#          -
#            name: key_type
#            in: query
#            required: true
#            type: string
#            description: 维度
#          -
#            name: key
#            in: query
#            required: false
#            type: string
#            description: 变量值
#          -
#            name: var_list
#            in: query
#            required: false
#            type: string
#            description: 变量名列表
#        """
#        from_time = int(self.get_argument('from_time', 0))
#        end_time = int(self.get_argument('end_time', 0))
#        key = self.get_argument('key', '')
#        key_type = self.get_argument('key_type', '')
#        var_list = self.get_arguments('var_list')
#        
#        if not (from_time and end_time and key_type):
#            self.finish(json_encode(dict(status=-1, msg=u"参数错误，没有查询时间范围, 或者没有指定维度")))
#            return
#
#        ts = int(from_time) / 1000.0
#        end_ts = int(end_time) / 1000.0
#        now = millis_now()
#        now_in_hour_start = now / 1000 / 3600 * 3600
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(ts), datetime.fromtimestamp(end_ts))
#
#        if key_type == "total":
#            key_type = "global"
#        if not key:
#            # 默认取全局的数据时 key_type = 'total'
#            key = '__GLOBAL__'
#
#        try:
#            if end_ts >= now_in_hour_start:
#                timestamps = get_hour_strs_fromtimestamp(ts, now_in_hour_start-1)
#            else:
#                timestamps = get_hour_strs_fromtimestamp(ts, end_ts)
#    
#            timestamps = map(lambda x: str(x), timestamps)
#            #logger.debug(DEBUG_PREFIX+u"查询的时间戳: %s", timestamps)
#            records = None
#            if timestamps:
#                records = data_client.get_offline_continuous(key, key_type, timestamps, var_list)
#            if not records:
#                records = dict()
#            
#            logger.debug(DEBUG_PREFIX+u"查询的key: %s, key_type:%s, 返回的查询结果是:%s", key, key_type, records)
#            ret_stats = dict( (int(float(ts)*1000), v)  for ts,v in records.iteritems())
#            if ret_stats:
#                self.finish(json_encode(dict(status=0, values=ret_stats)))
#            else:
#                self.finish(json_encode(dict(status=0, values=ret_stats, msg=u"offline数据返回为空")))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#        
#
#class MetricsDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/metrics'
#    
#    def get(self):
#        """
#        从metrics监控系统获取统计数据
#        
#        values: { timepoint1: {tag1:count, tag2:count}, timepoint2:{tag1:count, tag2:count}}
#        """
#        from_time = int(self.get_argument('from_time', 0))
#        end_time = int(self.get_argument('end_time', 0))
#        group_tags = self.get_arguments('group_tag')
#        filter_tags = self.get_arguments('filter_tag')
#        db = self.get_argument('db', 'default')
#        metrics_name = self.get_argument('metrics_name', None)
#        interval = self.get_argument('interval', 0)
#        aggregation = self.get_argument('aggregation', 'sum')
#        
#        if not metrics_name:
#            self.finish(json_encode(dict(status=-1, msg=u"参数错误，查询的metrics_name为空")))
#            return
#            
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(from_time/1000.0), datetime.fromtimestamp(end_time/1000.0))
#        logger.debug(DEBUG_PREFIX+u"查询的db: %s, metrics_name:%s, aggregation:%s, from_time:%s, end_time:%s, group_tags:%s, filter_tags:%s, interval:%s", db, metrics_name, aggregation, from_time, end_time, group_tags, filter_tags, interval)
#        try:
#            ret_stats = MetricsAgent.get_instance().query(db, metrics_name, aggregation, from_time, end_time, interval, filter_tags, group_tags)
#            self.finish(json_encode(dict(status=0, values=ret_stats)))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#        
#        
#
#class NoticeDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/notice'
#    
#    def get(self):
#        """
#        从风险名单服务获取数据
#        
#        """
#        #@todo
#
#class RiskIncidentDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/risk_incident'
#    
#    def get(self):
#        """
#        从风险事件获取数据
#        
#        """
#        #@todo
#
#class GEODataHandler(BaseHandler):
#    REST_URL = '/platform/stats/geo'
#
#    def get(self):
#        """
#        ip,mobile地理信息的数据源
#        
#        """
#        ips = self.get_arguments('ip')
#        mobiles = self.get_arguments('mobile')
#            
#        try:
#            ret_stats = dict()
#            ip_dict = ret_stats['ip'] = dict()
#            mobile_dict = ret_stats['mobile'] = dict()
#            for ip in ips:
#                ip_dict[ip] = data_client.find_ip_geo(ip)
#            for mobile in mobiles:
#                mobile_dict[ip] = data_client.find_mobile_geo(mobile)
#            self.finish(json_encode(dict(status=0, values=ret_stats)))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json_encode(dict(status=-1, error=e.message)))
#
#
#class ThreatMapDataHandler(BaseHandler):
#    REST_URL = '/platform/stats/threat_map'
#
#    @authenticated
#    def get(self):
#        """
#        导弹图接口，查询开始时间和结束时间之间的1000次风险事件访问数据
#
#        @API
#        summary: threat map
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 开始时间
#            required: true
#            type: timestamp
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: timestamp
#          - name: limit
#            in: query
#            description: 攻击事件个数，默认为1000
#            required: false
#            type: number
#            default: 1000
#        """
#        self.set_header('content-type', 'application/json')
#
#        try:
#            from_time = int(self.get_argument('from_time', 0))
#            end_time = int(self.get_argument('end_time', 0))
#            limit = int(self.get_argument('limit', 1000))
#
#            # 开始时间和结束时间不能为空
#            if from_time and end_time:
#                res, result = data_client.get_threat_map(from_time, end_time, limit)
#
#                # RPC正常返回为攻击城市信息列表，超时返回为False，
#                if res:
#                    self.flush()
#                    self.finish(json_dumps({"status": 200, "values": result}))
#                else:
#                    self.process_error(500, result)
#            else:
#                self.process_error(400, '开始时间和结束时间不能为空')
#        except Exception as e:
#            logger.error(e)
#            self.process_error(500, '导弹图查询失败')
