## -*- coding: utf-8 -*-
#from __future__ import absolute_import
#import hashlib, time, logging, os, traceback, sys
#import socket
#import simplejson as json
#from datetime import datetime, timedelta
#from threathunter_common.event import Event
#from os import path as opath
##from threading import Lock
#
#from ..dao.notice_dao import NoticeDao
#from ..dao.logquery_dao import LogQueryDao
#from nebula.views.base import BaseHandler
#from nebula.views import data_client
#import settings
#from common.utils import get_hour_strs, get_hour_strs_fromtimestamp
#from nebula.dao.user_dao import authenticated
#from common import utils
#from nebula.dao import cache
#
#from threathunter_common.metrics.metricsagent import MetricsAgent
#from threathunter_common.util import json_dumps, millis_now, curr_timestamp, ip_match
#from nebula_utils.persist_utils.event_schema import Event_Schema
#from nebula_utils import persist_utils
#from nebula_utils.persist_compute.cache import get_statistic, get_all_statistic, ContinuousDB
#from tornado.locks import Lock
#from tornado.gen import coroutine
#from tornado import gen
#from tornado.concurrent import run_on_executor
#from nebula_utils.persist_utils.bson.objectid import ObjectId
#
#logger = logging.getLogger('nebula.api.incident')
#
#DEBUG_PREFIX = '==============='
#Related_Users_Text = "关联用户"
#Browser_Types_Text = "浏览器类型"
#Click_Interval_Text = "点击时间间隔小于1s"
#Signup_Text = "次注册行为"
#Signin_Text = "次登录行为"
#Strategy_Trigger_Text = "类规则触发"
#Related_Device_Text = "关联设备"
#Related_IP_Text = "关联IP"
#DIM_LIST = ['ip', 'user', 'page', 'did']
#
#db_lock = Lock()
#query_lock = Lock()
#
#def get_hour_start(point=None):
#    """
#    获取point时间戳所在的小时的开始的时间戳, 默认获取当前时间所在小时的开始时的时间戳
#    """
#    if point is None:
#        p = time.time()
#    else:
#        p = point
#
#    return ((int(p) / 3600) * 3600) * 1.0
#
#
#class PersistBeginTimeHandler(BaseHandler):
#    REST_URL = '/platform/behavior/start_time'
#    def get(self):
#        """
#        @API
#        summary: 获得最早的持久化数据时间段
#        description: 获得最早可用的持久化数据的时间段
#        tags:
#          - platform
#        responses:
#          '200':
#            description: 返回时间段
#            schema:
#              $ref: '#/definitions/time_frame'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        dirs = os.listdir(settings.Persist_Path)
#        if not dirs:
#            # 0 代表还没有持久化数据文件夹产生
#            dirs = [0]
#        else:
#            dirs.sort()
#            for d in dirs:
#                if opath.exists(opath.join(settings.Persist_Path, d, 'data')):
#                    self.finish(json_dumps({'time_frame':get_ts_from_hour(d)}))
#                    return
#        self.finish(json_dumps({'time_frame':0}))
##        self.finish(json_dumps({'time_frame':int(dirs[0])}))
#
#class IncidentStatsHandler(BaseHandler):
#    REST_URL = '/platform/behavior/statistics'
#
#    def get(self):
#        """
#        获取事件统计的7处统计: 上面5个统计， 和用户和url的访问top
#        @API
#        summary: '获取三个接口数据 '
#        description: '/platform/behavior/variables,/platform/behavior/top/visits,/platform/behavior/top/related_users'
#        tags:
#          - platform
#        parameters:
#          - name: fromtime
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#            format: int64
#          - name: endtime
#            in: query
#            description: 截止时间
#            required: true
#            type: integer
#            format: int64
#          - name: key
#            in: query
#            description: 名单，可以为IP等
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回三个接口数据集合
#            schema:
#              $ref: '#/definitions/behaviorStatistics'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        fromtime = self.get_argument('fromtime', default='')
#        endtime = self.get_argument('endtime', default='')
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        var_list = self.get_arguments('vars')
#        vaild_key_type = ('ip', 'user', 'page', 'did')
#
#        if not var_list:
#            # @未来 之后有日志配置了之后， 应该是前端传进来, 前端是从计算变量配置放入特定的配置里面，然后传进来
#            # 变量名统一用key_type 而非字段名
#            if key_type == 'ip':
#                var_list = [
#                    "ip__visit__page_dynamic_count__1h__slot",'ip__visit__ua_dynamic_count__1h__slot',
#                    "ip__visit__did_dynamic_count__1h__slot" ,"ip__visit__user_dynamic_count__1h__slot" ]
#            elif key_type == 'user':
#                var_list = [
#                    "user__visit__page_dynamic_count__1h__slot", 'user__visit__ua_dynamic_count__1h__slot',
#                    "user__visit__did_dynamic_count__1h__slot", "user__visit__ip_dynamic_count__1h__slot"]
#            elif key_type == 'did':
#                var_list = [
#                    "did__visit__page_dynamic_count__1h__slot", 'did__visit__ua_dynamic_count__1h__slot',
#                    "did__visit__ip_dynamic_count__1h__slot", "did__visit__user_dynamic_count__1h__slot"]
#
#        fromtime = int(fromtime) / 1000.0
#        endtime = int(endtime) / 1000.0
#
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(fromtime), datetime.fromtimestamp(endtime))
#
#        def get_statistic_tops(src_dict, ):
#            """
#            根据返回的变量们的数据来组织返回的榜单的类型
#            """
#
#            #  ipc @todo 想想覆盖了么
#            top_key_list = {
#                'user_top': ['ip__visit__user_dynamic_count__1h__slot','did__visit__user_dynamic_count__1h__slot',
#                             'page__visit__user_dynamic_count__1h__slot'],
#                'url_top': ['ip__visit__page_dynamic_count__1h__slot','did__visit__page_dynamic_count__1h__slot',
#                            'user__visit__page_dynamic_count__1h__slot'],
#                'device_top': ['ip__visit__did_dynamic_count__1h__slot','user__visit__did_dynamic_count__1h__slot',
#                               'page__visit__did_dynamic_count__1h__slot'],
#                'ip_top': ['did__visit__ip_dynamic_count__1h__slot' ,
#                           'page__visit__ip_dynamic_count__1h__slot','user__visit__ip_dynamic_count__1h__slot'],
#                'ua_top': ['user__visit__ua_dynamic_count__1h__slot', 'did__visit__ua_dynamic_count__1h__slot',
#                           'ip__visit__ua_dynamic_count__1h__slot']
#                }
#            for top_name, top_key_var_list in top_key_list.iteritems():
#                for top_key in top_key_var_list:
#                    if src_dict.has_key(top_key):
#                        tmp = src_dict.pop(top_key, dict())
#                        # 生成host_top
#                        if top_name == 'url_top':
#                            host_top = dict()
#                            for k,v in tmp.iteritems():
#                                host, url_path = parse_host_url_path(k)
#                                if not host_top.has_key(host):
#                                    host_top[host] = v
#                                else:
#                                    host_top[host] = host_top[host] + v
#                            host_list = [ dict(item=k, count=v) for k,v in host_top.iteritems()]
#                            host_list.sort(key=lambda x:x['count'],reverse=True)
#                            src_dict['host_top'] = host_list
#                        tmp_list = [ dict(item=k, count=v) for k,v in tmp.iteritems()]
#                        tmp_list.sort(key=lambda x:x['count'],reverse=True)
#                        src_dict[top_name] = tmp_list[:20]
#
#        # 当前小时通过rpc去获取
#        now_in_hour_start = get_hour_start()
#        if fromtime == now_in_hour_start:
#            logger.debug(DEBUG_PREFIX+"在当前小时去获取...")
#            stats = get_latest_statistic(key, key_type, var_list)
#            get_statistic_tops(stats)
#            self.finish(json.dumps(stats))
#            return
#        # 当前小时之前去离线获取
##        logger.debug(DEBUG_PREFIX + "api : %s 从之前小时获取...", self.REST_URL)
#        try:
#            db_lock.acquire()
#            # variables:[user_count, ua_count, login_count, regist_count, http_count], user_top:[dict(item=k,count=v), ], url_top:[dict(item=k,count=v), ]
#
##            logger.debug(DEBUG_PREFIX + '查询的参数key:%s, key_type:%s, fromtime:%s, endtime:%s, var_list:%s', str(key), str(key_type), fromtime, endtime, var_list)
#            ret = get_statistic(key, key_type, fromtime, endtime, var_list)
##            logger.debug(DEBUG_PREFIX+'查询到的返回结果是: %s', ret)
#            if ret is None:
#                self.finish(json.dumps({"user_top":[], 'url_top':[], 'host_top':[],'ip_top':[], 'ua_top':[]}))
#
#            else:
#                get_statistic_tops(ret)
#                logger.debug(DEBUG_PREFIX+'整理返回内容的榜单之后是: %s', ret)
#                self.finish(json.dumps(ret))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"user_top":[], 'url_top':[], 'host_top':[],'ip_top':[], 'ua_top':[]}))
#        finally:
#            db_lock.release()
#
#def filter_records(records, filter_cols, query):
#    # 过滤日志列表中任意filter_cols里面的属性包含query，并返回包含query的日志们
##    logger.debug(DEBUG_PREFIX, u"query: %s, records size: %s, filter_cols: %s", query, len(records), str(filter_cols))
#    if not query:
#        return records
##    print >>sys.stderr, type(records), type(filter_cols), type(query)
##    print 'query is ', query
#    res = []
#    for r in records:
##        print 'filter', r.get('uri_stem')
#        for col in filter_cols:
#            v = r.get(col, "")
#            if not v:
#                continue
##            print 'filter' , r, type(r), v, type(v), col, v.find(query)
#            if v.find(query) != -1:
##                logger.debug(DEBUG_PREFIX, u"hit, col:%s, v:%s,", col, v)
#                res.append(r)
#                break
#    return res
##    return filter(lambda x: any(getattr(x, col, "").find(query) >= 0 \
##                                 for col in filter_cols) , records)
#
#
#class VisitStreamHandler(BaseHandler):
#    REST_URL = '/platform/behavior/visit_stream'
#    
#    def get(self):
#        """
#        获取一个小时内一段时间范围内每条记录的 user, 时间戳, 是否有报警
#        Return:
#        values: [{"ip":"10.4.36.154","did":"07900fe9a2926b684e98df9bc67a30bd06fd9c9c1e73f388b10e2696","user":"mmq0902",
#        "page":"bbb4.hyslt.com/api.php","sid":null,"if_notice":true,"timestamp":1493017043904}]
#        @API
#        summary: 获取一个小时内每30s的访问数据
#        description: 获取一个小时内每30s的访问数据
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#          - name: key
#            in: query
#            description: 名单，可以为IP等
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 事件类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickItems'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        fromtime = self.get_argument('from_time', default=0)
#        endtime = self.get_argument('end_time', default=0)
#        key = self.get_argument('key', default='')
#        if key:
#            key = key.encode('utf-8')
#        key_type = self.get_argument('key_type', default='')
#
#        if not (fromtime and endtime and key and key_type):
#            self.process_error(-1, "接口参数不能为空")
#            return
#
#        min_ts = int(fromtime)
#        max_ts = int(endtime)
#        ts = min_ts / 1000.0
#        end_ts = max_ts / 1000.0
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(ts), datetime.fromtimestamp(end_ts))
#        try:
#            result = persist_utils.query_visit_stream(key, key_type, ts, end_ts)
#            result = filter( lambda x: min_ts <= x['timestamp'] <= max_ts, result)
#            self.finish(json.dumps({"status": 0, "values": result}))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status": -1, "error": e.message}))
#
#class OnlineVisitStreamHandler(BaseHandler):
#    REST_URL = '/platform/online/visit_stream'
#    
#    def get(self):
#        """
#        获取当前小时内一段时间范围内每条记录的 user, 时间戳, 是否有报警
#        Return:
#        values: [{user:, timestamp:, if_notice:}, ... ]
#        @API
#        summary: 获取一个小时内每30s的访问数据
#        description: 获取一个小时内每30s的访问数据
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: false
#            type: integer
#            format: int64
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: false
#            type: integer
#            format: int64
#          - name: key
#            in: query
#            description: 名单，可以为IP等
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 事件类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickItems'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        fromtime = self.get_argument('from_time', default=0)
#        endtime = self.get_argument('end_time', default=0)
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        if not fromtime or not endtime or not key or not key_type:
#            self.finish(json.dumps({"status":-1, "error":'参数不完整, 无法查询'}))
#        min_ts = int(fromtime)
#        max_ts = int(endtime)
#        try:
#            result = get_online_visit_stream(key, key_type, min_ts, max_ts)
#            self.finish(json.dumps({"status":0, "values":result}))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#
#class ClickListPeriodHandler(BaseHandler):
#    REST_URL = '/platform/behavior/clicks_period'
#    
#    def get(self,):
#        """
#        获取一个小时内每30s的DYNAMIC event的数量, 暂时没有当前小时
#        产品角度: 各个维度的风险分析，点击流页面， 当点击了某一个小时的访问柱状条之后，会显示每30s的 DYNAMIC event的数量及是否有报警的 数据.
#        Return:
#        values:{ timestamp:{count:, if_notice:}}
#        @API
#        summary: 获取一个小时内每30s的访问数据
#        description: 获取一个小时内每30s的访问数据
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: false
#            type: integer
#            format: int64
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: false
#            type: integer
#            format: int64
#          - name: key
#            in: query
#            description: 名单，可以为IP等
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 事件类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickItems'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        #其实只会去拿fromtime所在的小时的文件夹， 不跨小时endtime没啥意义, endtime为以后一个小时内一段时间范围内的需求保留
#        fromtime = self.get_argument('from_time', default='')
#        endtime = self.get_argument('end_time', default='')
#        key = self.get_argument('key', default='')
#        if key:
#            key = key.encode('utf-8')
#        key_type = self.get_argument('key_type', default='')
#        ts = int(fromtime) / 1000.0
#        end_ts = int(endtime) / 1000.0
#        now = millis_now()
#        now_in_hour_start = now / 1000 / 3600 * 3600
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(ts), datetime.fromtimestamp(end_ts))
#        try:
#            result = persist_utils.query_clicks_period(key, key_type, ts, end_ts)
#            result = dict( (int(float(ts)*1000), _) for ts,_ in result.iteritems())
#            self.finish(json.dumps({"status":0, "values":result}))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#        
#class OnlineClicksPeriodHandler(BaseHandler):
#    REST_URL = '/platform/online/clicks_period'
#    
#    def get(self,):
#        """
#        获取当前小时内每30s的DYNAMIC event的数量, 暂时没有当前小时
#        产品角度: 各个维度的风险分析，点击流页面， 当点击了某一个小时的访问柱状条之后，会显示每30s的 DYNAMIC event的数量及是否有报警的 数据.
#        Return:
#        values:{ timestamp:{count:, if_notice:}}
#        @API
#        summary: 获取一个小时内每30s的访问数据
#        description: 获取一个小时内每30s的访问数据
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: false
#            type: integer
#            format: int64
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: false
#            type: integer
#            format: int64
#          - name: key
#            in: query
#            description: 名单，可以为IP等
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 事件类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickItems'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        fromtime = self.get_argument('from_time', default='')
#        endtime = self.get_argument('end_time', default='')
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        if not fromtime or not endtime or not key or not key_type:
#            self.finish(json.dumps({"status":-1, "error":'参数不完整, 无法查询'}))
#        ts = int(fromtime)
#        end_ts = int(endtime)
#        try:
#            result = get_online_clicks_period(key, key_type, ts, end_ts)
#            self.finish(json.dumps({"status":0, "values":result}))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#            
#class OnlineClickListHandler(BaseHandler):
#    REST_URL = '/platform/online/clicks'
#
#    def post(self):
#        """
#        获取当前小时内的点击列表
#        @API
#        summary: 获取时间段内的点击列表
#        description: 获取指定时间段内指定名单的所有点击资料
#        tags:
#          - platform
#        parameters:
#          - name: query_body
#            in: body
#            description: 日志查询条件
#            required: true
#            type: json
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickItems'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        query_body = json.loads(self.request.body)
#        from_time = query_body.get('from_time', 0)
#        end_time = query_body.get('end_time', 0)
#        key = query_body.get('key', '')
#        if key:
#            key = key.encode('utf-8')
#        key_type = query_body.get('key_type', '')
#        size = query_body.get('size', 20)
#        query = query_body.get('query', [])
#
#        if not (from_time and end_time and key and key_type):
#            self.process_error(-1, "接口参数不能为空")
#            return
#        try:
#            result = get_online_clicks(key, key_type, from_time, end_time, size, query)
#            self.finish(json.dumps({"status":0, "values":result}))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#
#            
#class ClickListHandler(BaseHandler):
#    REST_URL = '/platform/behavior/clicks'
#
#    def post(self):
#        """
#        获取时间段内的点击列表
#        @API
#        summary: 获取时间段内的点击列表
#        description: 获取指定时间段内指定名单的所有点击资料
#        tags:
#          - platform
#        parameters:
#          - name: query_body
#            in: body
#            description: 日志查询条件
#            required: true
#            type: json
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickItems'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        query_body = json.loads(self.request.body)
#        filter_cols = ["uri_stem", "sid", "uid"]
#        from_time = query_body.get('from_time', 0)
#        end_time = query_body.get('end_time', 0)
#        key = query_body.get('key', '')
#        if key:
#            key = key.encode('utf-8')
#        key_type = query_body.get('key_type', '')
#        size = query_body.get('size', 20)
#        query = query_body.get('query', [])
#
#        if not (from_time and end_time and key and key_type):
#            self.process_error(-1, "接口参数不能为空")
#            return
#
#        ts = int(from_time) / 1000.0
#        end_ts = int(end_time) / 1000.0
#        now = millis_now()
#        now_in_hour_start = now / 1000 / 3600 * 3600
#        try:
#            db_lock.acquire()
#            records = []
#            errors = []
#            if ts < now_in_hour_start:
#                # 从离线持久化数据里面查找
#                logger.debug(DEBUG_PREFIX+'从历史里面查找点击列表...')
#                # 为了实现日志点击列表倒序，需要扫描整个时间段日志，再截取列表
#                limit = 10000000
#                ret, err = persist_utils.get_request_log(key, ts, key_type, query=query, end=end_ts, limit=limit)
#                records = ret if ret else []
#                if err:
#                    errors.append('%s: %s;' % (ts, err))
#                    self.finish(json.dumps({"status":0, "values":[]}))
#                    return
#                # 过滤一条日志中任意uri_stem uid sid 字段是否包含query
#                if records:
#                    logger.debug(DEBUG_PREFIX+'过滤关键词%s之前, 日志的大小是%s', query, len(records))
#                else:
#                    logger.debug(DEBUG_PREFIX+'过滤关键词%s之前, 日志就为空了', query)
#
#                # 过滤records @todo 优化，现在下面支持查询功能了, 至少可以用闭包弄个过滤函数
##                records = filter_records(records, filter_cols, query)
#                if records:
#                    logger.debug(DEBUG_PREFIX+'过滤关键词%s之后, 日志的大小是%s', query, len(records))
#
#            if end_ts - 1 >= now_in_hour_start and len(records) <= size:
#                logger.debug(DEBUG_PREFIX+'从当前小时里面查找点击列表...')
#                latest_events = get_latest_events(key, key_type, fromtime=from_time, size=size * 2)
##                print >> sys.stderr, "filter before",len(latest_events)
##                print >> sys.stderr, latest_events[0]["timestamp"], fromtime
#                logger.debug(DEBUG_PREFIX+u"返回的事件们是%s, type:%s", latest_events, type(latest_events))
##                latest_events = filter( lambda x: x["timestamp"]>= int(fromtime), latest_events)
##                print >> sys.stderr, "filter time",len(latest_events)
#                # 过滤当前日志中任意uri_stem uid sid 字段是否包含query
##                result.extend(latest_events)
#                records.extend(filter_records(latest_events, filter_cols, query))
##                print >> sys.stderr, "filter query", len(latest_events)
#
#            # 合并日志,将日志更新到父日志中。日志中的固定字段不更改,notices字段合并,其余的特殊字段覆盖父日志
#            record_dict = dict()
#            for record in records:
#                record_id = record['id']
#                record_pid = record['pid']
#
#                if record_pid in record_dict:
#                    pid_dict = record_dict[record_pid]
#
#                    for key, value in record.items():
#                        if key in Event_Schema['fixed']:
#                            continue
#                        elif key == 'notices':
#                            if record.get('notices', ''):
#                                if pid_dict.get('notices', ''):
#                                    pid_dict['notices'] = ','.join([pid_dict['notices'], record['notices']])
#                                else:
#                                    pid_dict['notices'] = record['notices']
#                        else:
#                            pid_dict[key] = value
#
#                    pid_dict['merged'] += 1
#                    record_dict[record_pid] = pid_dict
#                else:
#                    record['merged'] = 1
#                    record_dict[record_id] = record
#
#            # 根据每天记录的notice字段计算风险场景和风险值
#            for _, record in record_dict.items():
#                event_count = record.pop('merged', 1)
#
#                if record.get('notices', None):
#                    score = dict()
#                    notices = list(set(record.get('notices', '').split(',')))
#                    for n in notices:
#                        weigh = cache.Strategy_Weigh_Cache.get(n, dict())
#                        if weigh:
#                            category = weigh['category']
#
#                            if category in score:
#                                score[category] += weigh['score']
#                            else:
#                                score[category] = weigh['score']
#                    record['category'] = score.keys()
#                    record['risk_score'] = max([int(value / event_count) for value in score.values()]) if score else 0
#
#                # 去除log多余字段
#                for attr in ['buff_endpoint', 'record_size', 'buff_startpoint']:
#                    record.pop(attr, None)
#
#            result = record_dict.values()
#            result.sort(key=lambda r: r["timestamp"], reverse=True)
#            result = result[:size]
#            self.finish(json.dumps({"status": 0, "values": result}))
#
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status": -1, "error": e.message}))
#        finally:
#            db_lock.release()
#
#
#class ContinuousRelatedStatHandler(BaseHandler):
#
#    REST_URL = '/platform/behavior/continuous_related_statistic'
#
#    @authenticated
#    def get(self):
#        """
#        获取时间段内的点击列表
#
#        @API
#        summary: 获取时间段内的每个小时的点击数
#        description: ''
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#          - name: key
#            in: query
#            description: 关键字
#            required: false
#            type: string
#          - name: key_type
#            in: query
#            description: 关键字类型
#            required: false
#            type: string
#        responses:
#          '200':
#            description: 返回点击统计列表
#            schema:
#              $ref: '#/definitions/clickStatistics'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        from_time = int(self.get_argument('from_time', 0))
#        end_time = int(self.get_argument('end_time', 0))
#        key = self.get_argument('key', '')
#        key_type = self.get_argument('key_type', '')
#
#        if not (from_time and end_time):
#            self.process_error(400, 'parameters error')
#        ts = int(from_time) / 1000.0
#        end_ts = int(end_time) / 1000.0
#        now = millis_now()
#        now_in_hour_start = now / 1000 / 3600 * 3600
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(ts), datetime.fromtimestamp(end_ts))
#
#        ContinuousDB.get_db()
#        group_tags = ['ip', 'user', 'page', 'did', 'incident']
#        if end_ts >= now_in_hour_start:
#            timestamps = get_hour_strs_fromtimestamp(ts, now_in_hour_start-1)
#        else:
#            timestamps = get_hour_strs_fromtimestamp(ts, end_ts)
#
#        timestamps = map(lambda x: str(x), timestamps)
##        logger.debug(DEBUG_PREFIX+u"查询的时间戳: %s", timestamps)
#        related_vars = dict(
#            did=['did__visit__dynamic_distinct_ip__1h__slot', #did 关联ip数
#                 'did__visit__dynamic_distinct_user__1h__slot',# did 关联user数
#                 'did__visit__dynamic_distinct_page__1h__slot',# did 关联page数
#                 'did__visit__incident_count__1h__slot'],#did 风险事件数
#            user=['user__visit__dynamic_distinct_ip__1h__slot',# user 关联ip数
#                 'user__visit__dynamic_distinct_did__1h__slot',# user 关联did数
#                 'user__visit__dynamic_distinct_page__1h__slot',# user 关联page数
#                 'user__visit__incident_count__1h__slot'],# user 风险事件数
#            ip=['ip__visit__dynamic_distinct_did__1h__slot',# ip 关联did数
#                 'ip__visit__dynamic_distinct_user__1h__slot',# ip 关联user数
#                 'ip__visit__dynamic_distinct_page__1h__slot',# ip 关联page数
#                 'ip__visit__incident_count__1h__slot'],# ip 风险事件数
#            page=['page__visit__dynamic_distinct_ip__1h__slot',# page 关联ip数
#                 'page__visit__dynamic_distinct_user__1h__slot',# page 关联user数
#                 'page__visit__dynamic_distinct_did__1h__slot',# page 关联did数
#                 'page__visit__incident_count__1h__slot'],)# page 风险事件数
#
#        # var:col
#        vars_col_dict = {
#            'did__visit__dynamic_distinct_ip__1h__slot': 'ip',
#            'did__visit__dynamic_distinct_user__1h__slot':'user',# did 关联user数
#            'did__visit__dynamic_distinct_page__1h__slot':'page',# did 关联page数
#            'did__visit__incident_count__1h__slot':'incident',#did 风险事件数
#            'user__visit__dynamic_distinct_ip__1h__slot':'ip',# user 关联ip数
#            'user__visit__dynamic_distinct_did__1h__slot':'did',# user 关联did数
#            'user__visit__dynamic_distinct_page__1h__slot':'page',# user 关联page数
#            'user__visit__incident_count__1h__slot':'incident',# user 风险事件数
#            'ip__visit__dynamic_distinct_did__1h__slot':'did',# ip 关联did数
#            'ip__visit__dynamic_distinct_user__1h__slot':'user',# ip 关联user数
#            'ip__visit__dynamic_distinct_page__1h__slot':'page',# ip 关联page数
#            'ip__visit__incident_count__1h__slot':'incident',# ip 风险事件数
#            'page__visit__dynamic_distinct_ip__1h__slot':'ip',# page 关联ip数
#            'page__visit__dynamic_distinct_user__1h__slot':'user',# page 关联user数
#            'page__visit__dynamic_distinct_did__1h__slot':'did',# page 关联did数
#            'page__visit__incident_count__1h__slot':'incident',# page 风险事件数
#            'total__visit__dynamic_distinct_did__1h__slot':'did',
#            'total__visit__incident_count__1h__slot':'incident',
#            'total__visit__dynamic_distinct_user__1h__slot':'user',
#            'total__visit__dynamic_distinct_ip__1h__slot':'ip',
#        }
#        try:
#            if key_type and key:
#                related_dim = [dim for dim in DIM_LIST if dim != key_type]
#                click_var = '%s__visit__dynamic_count__1h__slot' % key_type
#                incident_var = '%s__visit__incident_count__1h__slot' % key_type
#                var_list = ['%s__visit__dynamic_distinct_%s__1h__slot' % (key_type, dim) for dim in related_dim]
#                var_list.append(click_var)
#                var_list.append(incident_var)
#                if timestamps:
#                    records = ContinuousDB.query_many(key, key_type, timestamps, var_list)
#                else:
#                    records = dict()
#            else:
#                click_var = 'total__visit__dynamic_count__1h__slot'
#                related_vars = {dim: 'total__visit__dynamic_distinct_{}__1h__slot'.format(dim) for dim in ['did', 'ip', 'user']}
#                related_vars['incident'] = 'total__visit__incident_count__1h__slot'
#                tmp_var_list = related_vars.values()
#                tmp_var_list.append(click_var)
#                if timestamps:
#                    records = ContinuousDB.query_many('all', 'total', timestamps, tmp_var_list)
#                else:
#                    records = dict()
#
#            logger.debug(DEBUG_PREFIX+u"查询的key: %s, key_type:%s, 返回的查询结果是:%s", key, key_type, records)
#        except Exception as e:
#            traceback.print_exc()
#            logger.error(e)
#            self.process_error(400, 'fail to get incidents from metrics')
#            return
#
#        click_statistics = list()
#        for ts in timestamps:
#            r = records.get(ts, None) if records else None # if aerospike fail.
#            if r is None:
#                click_statistics.append(dict(count=0, time_frame=int(float(ts)*1000), related_count={tag: 0 for tag in group_tags}))
#                continue
#
#            t = dict(count=r.pop(click_var, 0), related_count=dict(), time_frame=int(float(ts)*1000))
#            for k,v in r.iteritems():
#                col = vars_col_dict.get(k)
#                t['related_count'][col] = v
#            click_statistics.append(t)
#        try:
#
#            ts = get_current_hour_timestamp()
#            if end_time > ts:
#                if key_type and key:
#                    click = get_latest_statistic(key, key_type, var_list)
#                    related_counts = dict()
#                    if click:
#                        for dim in related_dim:
#                            var = '%s__visit__dynamic_distinct_%s__1h__slot' % (key_type, dim)
#                            related_counts[dim] = len(click[var])
#                        related_counts['incident'] = int(click[incident_var])
#                        click_statistics.append(
#                            {'count': int(click[click_var]), 'related_count': related_counts, 'time_frame': ts})
#                    else:
#                        click_statistics.append(dict(count=0, time_frame=ts, related_count={tag: 0 for tag in group_tags}))
#                else:
#                    click = get_latest_statistic(key='', key_type='', var_list=[click_var] + related_vars.values())
#                    if click:
#                        a_stat = dict()
#                        for tag, var in related_vars.iteritems():
#                            var_value = click[var]
#                            if isinstance(var_value, int):
#                                a_stat[tag] = var_value
#                            else:
#                                a_stat[tag] = len(var_value)
#                        click_statistics.append({'count': int(click[click_var]), 'related_count': a_stat, 'time_frame':ts})
#                    else:
#                        click_statistics.append(dict(count=0, time_frame=ts, related_count={tag: 0 for tag in group_tags}))
##                        records[ts] = {'count': int(click[click_var]), 'related_count': click_statistics}
#
#            self.finish(json_dumps(click_statistics))
#            return
#        except Exception as e:
#            traceback.print_exc()
#            logger.error(e)
#            self.process_error(400, 'fail to statistics click')
#
#
#class ContinuousTopRelatedStatHandler(BaseHandler):
#
#    REST_URL = '/platform/behavior/continuous_top_related_statistic'
#
#    @authenticated
#    def get(self):
#        """
#        获取指定时间点击数最高的7位用户点击量
#
#        @API
#        summary: 获取用户历史点击量
#        description: ''
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#          - name: key
#            in: query
#            description: 关键字
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 关键字类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击统计列表
#            schema:
#              $ref: '#/definitions/clickStatistics'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        from_time = int(self.get_argument('from_time', 0))
#        end_time = int(self.get_argument('end_time', 0))
#        key = self.get_argument('key', '')
#        key_type = self.get_argument('key_type', '')
#
#        if not (from_time and end_time and key and key_type):
#            self.process_error(400, 'parameters error')
#
#        interval = 60 * 60 * 1000
#        db = 'default'
#        metrics_name = 'click.related.{}'.format(key_type)
#        top_related = get_current_top_related(key_type, key)
#        top_related_keys = top_related.keys()
#        if key_type == 'ip':
#            group_tags = ['user']
#            filter_tags = {'user': top_related_keys}
#        else:
#            group_tags = ['ip']
#            filter_tags = {'ip': top_related_keys}
#
#        try:
#            metrics = MetricsAgent.get_instance().query(db, metrics_name, 'sum', from_time,
#                                                        end_time, interval, filter_tags, group_tags)
#            click_statistics = {top: [] for top in top_related_keys}
#            for time_frame in range(from_time, end_time, interval):
#                clicks = metrics.get(time_frame, {})
#                related_tops = {tags[0]: int(value) for tags, value in clicks.iteritems()}
#
#                for top in top_related_keys:
#                    if top in related_tops:
#                        click_statistics[top].append(dict(time_frame=time_frame, count=related_tops[top]))
#                    else:
#                        click_statistics[top].append(dict(time_frame=time_frame, count=0))
#
#            ts = get_current_hour_timestamp()
#            if end_time > ts:
#                for top, count in top_related.iteritems():
#                    click_statistics[top][-1]['count'] = count
#
#            self.finish(json_dumps(click_statistics))
#        except Exception as e:
#            logger.error(e)
#            self.process_error(400, 'fail to statistics click')
#
#
#def get_current_top_related(key_type, key):
#    if key_type == 'ip':
#        var = 'ip__visit__user_dynamic_count__1h__slot'
#    else:
#        var = '{}__visit__ip_dynamic_count__1h__slot'.format(key_type)
#    variables = get_latest_statistic(key=key, key_type=key_type, var_list=[var])
#    if variables:
#        top_related = variables[var]
#        sorted_top_related = sorted(top_related.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
#        len_related = 7 if len(sorted_top_related) >= 7 else len(sorted_top_related)
#        return {sorted_top_related[i][0]: sorted_top_related[i][1] for i in range(len_related)}
#
#    return False
#
#
#class SceneStatHandler(BaseHandler):
#
#    REST_URL = '/platform/behavior/scene_statistic'
#
#    @authenticated
#    def get(self):
#        """
#        获取各场景的命中数统计
#
#        @API
#        summary: 获取时间段内的每个小时的维度场景点击数
#        description: ''
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#          - name: key
#            in: query
#            description: 关键字
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 关键字类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击统计列表
#            schema:
#              $ref: '#/definitions/clickStatistics'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        from_time = int(self.get_argument('from_time', 0)) / 1000.0
#        end_time = int(self.get_argument('end_time', 0)) / 1000.0
#        key = self.get_argument('key', '')
#        key_type = self.get_argument('key_type', '')
#
#        # 检查API参数
#        if not (from_time and end_time and key and key_type) or key_type == 'page':
#            self.process_error(400, 'parameters error')
#
#        scene_statistics = {'VISITOR': 0, 'ACCOUNT': 0, 'ORDER': 0,
#                            'TRANSACTION': 0, 'MARKETING': 0, 'OTHER': 0}
#        scene_dict = dict()
#        scene_var = '{}__visit__scene_incident_count__1h__slot'.format(key_type)
#
#        try:
#            ts = get_hour_start()
#            if end_time > ts:
#                # 如果结束时间超过当前小时,请求Java RPC数据
#                subkeys = {scene_var: scene_statistics.keys()}
#                result = get_latest_statistic(key=key, key_type=key_type, var_list=[scene_var], subkeys=subkeys)
#                if result:
#                    scene_dict = result.get(scene_var, {})
#            else:
#                # 获取离线计算统计数据
#                scene_ret = get_statistic(key, key_type, from_time, end_time, [scene_var])
#                if scene_ret:
#                    scene_dict = scene_ret.get(scene_var, {})
#
#            for k, v in scene_dict.items():
#                if k not in scene_statistics.keys():
#                    scene_dict["VISITOR"] = scene_dict.get("VISITOR", 0) + v
#
#            scene_dict = {k: v for k, v in scene_dict.items() if k in scene_statistics.keys()}
#
#            if scene_dict:
#                dict_merge(scene_statistics, scene_dict)
#            self.finish(json_dumps(scene_statistics))
#        except Exception as e:
#            logger.error(e)
#            self.finish(json_dumps(scene_statistics))
#
#
#class StrategyStatHandler(BaseHandler):
#
#    REST_URL = '/platform/behavior/strategy_statistic'
#
#    @authenticated
#    def get(self):
#        """
#        获取各场景的命中策略统计
#
#        @API
#        summary: 获取时间段内的每个小时的命中策略统计数
#        description: ''
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#          - name: scene
#            in: query
#            description: 策略场景
#            required: true
#            type: string
#        """
#        from_time = self.get_argument('from_time', 0)
#        end_time = self.get_argument('end_time', 0)
#        scene = self.get_argument('scene', '')
#        # 检查API参数
#        if not (from_time and end_time and scene):
#            self.process_error(400, 'parameters error')
#        scene_statistics = []
#        try:
#            # 查询数据库,统计命中策略变量,只选取命中数量排名前8的策略
#            ret = NoticeDao().get_statistic_scene(from_time, end_time, scene)[:8]
#            scene_statistics = [{strategy: count} for strategy, count in ret]
#            self.finish(json_dumps(scene_statistics))
#        except Exception as e:
#            logger.error(e)
#            self.finish(json_dumps(scene_statistics))
#
#
#class TagStatHandler(BaseHandler):
#
#    REST_URL = '/platform/behavior/tag_statistics'
#
#    @authenticated
#    def get(self):
#        """
#        获取当前小时tags的统计
#
#        @API
#        summary: 获取当前小时tags的统计
#        description: ''
#        tags:
#          - platform
#        """
#        tag_statistics = []
#        temp_statistics = {}
#        try:
#            # 查询风险名单数据库,统计命中策略变量
#            from_time = get_hour_start() * 1000
#            end_time = millis_now()
#            ret = NoticeDao().get_statistic_scene(from_time, end_time)
#
#            # 根据命中策略查询策略包含的tags,并统计命中每一个tag的数量
#            strategy_weigh = cache.Strategy_Weigh_Cache
#            for strategy, count in ret:
#                tags = strategy_weigh.get(strategy, {}).get('tags', [])
#                for tag in tags:
#                    dict_merge(temp_statistics, {tag: count})
#
#            # tags根据命中数量排序
#            sorted_tags = sorted(temp_statistics.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)[:10]
#            tag_statistics = [{'name': tag, 'count': count} for tag, count in sorted_tags]
#            self.finish(json_dumps(tag_statistics))
#        except Exception as e:
#            logger.error(e)
#            self.finish(json_dumps(tag_statistics))
#
#
#class UserStatHandler(BaseHandler):
#
#    REST_URL = '/platform/behavior/user_statistics'
#
#    @authenticated
#    def get(self):
#        """
#        获取风险事件的用户数统计
#
#        @API
#        summary: 获取时间段内的每天的关联用户、风险用户统计数
#        description: ''
#        tags:
#          - platform
#        parameters:
#          - name: from_time
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#          - name: end_time
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#        """
#        from_time = int(self.get_argument('from_time', 0)) / 1000.0
#        end_time = int(self.get_argument('end_time', 0)) / 1000.0
#        # 检查API参数
#        if not (from_time and end_time):
#            self.process_error(400, 'parameters error')
#
#        # 获取查询aerospike的时间戳
#        now_in_hour_start = get_hour_start()
#        if end_time >= now_in_hour_start:
#            timestamps = get_hour_strs_fromtimestamp(from_time, now_in_hour_start-1)
#        else:
#            timestamps = get_hour_strs_fromtimestamp(from_time, end_time)
#        timestamps = map(lambda x: str(x), timestamps)
#
#        try:
#            # 查询aerospike数据,关联用户数和风险用户数
#            ContinuousDB.get_db()
#            related_var = 'total__visit__dynamic_distinct_user__1h__slot'
#            risk_var = 'total__visit__incident_distinct_user__1h__slot'
#            statistics_list = list()
#            if timestamps:
#                records = ContinuousDB.query_many('all', 'total', timestamps, [related_var, risk_var])
#            else:
#                records = dict()
#
#            for ts in timestamps:
#                temp_dict = dict()
#                var_values = records.get(ts, {})
#                temp_dict['related_users'] = var_values.get(related_var, 0)
#                temp_dict['risk_users'] = var_values.get(risk_var, 0)
#                temp_dict['timestamp'] = int(float(ts)) * 1000
#                statistics_list.append(temp_dict)
#
#            # 如果包含当前小时,则请求RPC,获取关联用户和风险用户数
#            if end_time > now_in_hour_start:
#                temp_dict = dict()
#                ret = get_latest_statistic(key='', key_type='', var_list=[related_var, risk_var])
#                temp_dict['timestamp'] = now_in_hour_start * 1000
#                temp_dict['related_users'] = ret.get(related_var, 0)
#                temp_dict['risk_users'] = ret.get(risk_var, 0)
#                statistics_list.append(temp_dict)
#
#            self.finish(json_dumps(statistics_list))
#        except Exception as e:
#            logger.error("fail to get incidents statistics from database: %s", e)
#            self.process_error(400, 'fail to get incidents statistics from database')
#
#
#def get_ts_from_hour(time_str, f="%Y%m%d%H"):
#    """
#    ex. 2016010212(str) -> timestamp * 1000(int)
#    """
#
#    import time
#    return int(time.mktime(time.strptime(time_str, f)) * 1000)
#
#class ClickDetailHandler(BaseHandler):
#    REST_URL = '/platform/behavior/clicks_detail'
#
#    def get(self, ):
#        """
#        @API
#        summary: 获取点击详情
#        description: 根据时间戳和名单获取点击详情
#        tags:
#          - platform
#        parameters:
#          - name: event_id
#            in: query
#            description: 事件id
#            required: true
#            type: string
#            format: string
#          - name: event_name
#            in: query
#            description: 事件名称
#            required: true
#            type: string
#          - name: key
#            in: query
#            description: 事件索引
#            required: true
#            type: string
#          - name: key_type
#            in: query
#            description: 事件类型
#            required: true
#            type: string
#          - name: timestamp
#            in: query
#            description: 事件时间戳
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/clickDetail'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        event_id = self.get_argument('event_id', default='')
#        event_name = self.get_argument('event_name', default='')
#        key = self.get_argument('key', default='')
#        key_type = self.get_argument('key_type', default='')
#        if not event_id:
#            self.finish(json.dumps({"status":-2, "error":"null id"}))
#            return
#
#        timestamp = self.get_argument('timestamp', default='')
#
#        if not timestamp:
#            self.finish(json.dumps({"status":-2, "error":"null timestamp"}))
#            return
#
#        ts = int(timestamp)/ 1000.0
#        logger.debug(DEBUG_PREFIX+u"查询的时间戳是%s", datetime.fromtimestamp(ts))
##        dt = ObjectId(event_id).generation_time
##        ts = (dt - datetime(1970, 1,1, tzinfo=pytz.utc)).total_seconds()
#
#        now_in_hour_start = get_hour_start()
#        if ts >= now_in_hour_start:
#            logger.debug(DEBUG_PREFIX+ u"当前小时从babel rpc获取")
#            ev = get_latest_events(key, key_type, fromtime=timestamp, event_id=event_id)
#            if ev:
#                e = ev[0]
#                ret = {
#                    "timestamp": e["timestamp"],
#                    "client_host": e["c_ip"],
#                    "server_host": e["s_ip"],
#                    "http": [{"name": k, "value":v} for k, v in e.iteritems()]
#                }
#                self.finish(json.dumps(ret))
#            else:
#                self.finish(json.dumps({"status":-2, "error":"not found"}))
#            return
##            for ev in get_latest_events(key, key_type):
##                if ev["id"] == event_id:
##                    ret = {
##                        "timestamp": ev["timestamp"],
##                        "client_host": ev["c_ip"],
##                        "server_host": ev["s_ip"],
##                        "http": [{"name": k, "value":v} for k, v in ev.iteritems()]
##                    }
##                    self.finish(json.dumps(ret))
##                    break
##                if ev["id"] > event_id:
##                    self.finish(json.dumps({"status":-2, "error":"not found"}))
##                    break
#
#        try:
#            db_lock.acquire()
#            logger.debug(DEBUG_PREFIX+ u"从离线获取，单条事件详情..")
#            record, err = persist_utils.get_request_log(key, ts, key_type, eid=ObjectId(event_id))
#            if err:
#                self.finish(json.dumps({"status":-2, "error":err}))
##            print record, type(record), len(record)
#            if record:
#                ret = dict(
#                     timestamp= record[0].get('timestamp'),
#                     client_host = record[0].get('c_ip'),
#                     server_host = record[0].get('s_ip'),
#                     http=[ dict(name=k, value=v) for k,v in record[0].iteritems()]
#                )
#            else:
#                ret = dict()
#            self.finish(json.dumps(ret))
#
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#        finally:
#            db_lock.release()
#
#class RelatedStatisticHandler(BaseHandler):
#    REST_URL = '/platform/behavior/related_statistics'
#
#    def get(self):
#        """
#        每个维度分析页面的左下角的不同维度两两关联的top榜单api
#        dict(
#            ip=[
#                {'value':'',
#                 'country':'',
#                 'province':'',
#                 'city':'',
#                 'related_key_type':'',
#                 'count':0}],
#            user=[
#                {'value':'',
#                 'related_key_type':'',
#                 'count':0}
#            ],
#            did=[{
#                'value':'',
#                'os':'',
#                'device_type':'',
#                'related_key_type':'',
#                'count':0,}
#            ],
#            page=[
#                {'value':'',
#                 'related_key_type':'',
#                 'count':0}
#            ],
#        )
#
#        @API
#        summary: 某个小时内关联数据排行
#        description: ''
#        tags:
#          - platform
#        parameters:
#          - name: key
#            in: query
#            description: key_type为page时需要
#            required: false
#            type: string
#          - name: key_type
#            in: query
#            description: 维度类型
#            required: true
#            type: string
#          - name: related_key_types
#            in: query
#            description: 关联数据类型
#            required: true
#            type: string
#          - name: fromtime
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#            format: int64
#          - name: endtime
#            in: query
#            description: 截止时间
#            required: true
#            type: integer
#            format: int64
#        responses:
#          '200':
#            description: 统计列表
#            schema:
#              $ref: '#/definitions/relatedStatistics'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        fromtime = self.get_argument('fromtime', default=None)
#        endtime = self.get_argument('endtime', default=None)
#        key_type = self.get_argument('key_type', default='')
#        related_key_types = self.get_argument('related_key_types', default='')
#        related_key_types = related_key_types.split(',')
#        key = self.get_argument('key', default='')
#        fromtime = int(fromtime) / 1000.0
#        endtime = int(endtime) / 1000.0
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(fromtime), datetime.fromtimestamp(endtime))
#
#        if not key_type or not related_key_types:
#            logger.error('/platform/behavior/related_statistics 没有传入两个关联因素。')
#            self.finish(json.dumps([]))
#        if key_type == 'page' and not key:
#            logger.error('/platform/behavior/related_statistics key_type为page,key为空')
#            self.finish(json.dumps([]))
#
#        # 根据key_type和related_key_type得到查询的var_list
#        var_list = []
#        top_list = []
#        temp_dict = {}
#        now_in_hour_start = get_hour_start()
#
#        # page维度只关联一个维度
#        if key_type == 'page':
#            related_type = related_key_types[0]
#            page_var_name = 'page__visit__{}_dynamic_count__1h__slot'.format(related_type)
#            var_list.append(page_var_name)
#
#            try:
#                if fromtime >= now_in_hour_start:
#                    # 当前小时数据,请求Java RPC
#                    # ret 结构为{variable1: {key1: value1}}
#                    ret = get_latest_statistic(key, key_type, var_list)
#                    top_statistic = ret.values()[0] if ret else {}
#                else:
#                    # 历史数据,离线计算查询
#                    # page维度只有单个key查询的值{variable: value}
#                    # todo
#                    ret = data_client.get_offline_key_stat(key, key_type, fromtime, var_list)
#                    top_statistic = ret.values()[0] if ret else {}
#
#                for top, var_value in top_statistic.items():
#                    v = len(var_value) if isinstance(var_value, (list, set)) else var_value
#                    top_dict = dict()
#                    top_dict['value'] = top
#                    top_dict['related_count'] = v
#                    if related_type == 'ip':
#                        country, province, city = find_ip_geo(top)
#                        top_dict['country'] = country
#                        top_dict['province'] = province
#                        top_dict['city'] = city
#
#                    top_list.append(top_dict)
#
#                top_list = sorted(top_list, lambda x, y: cmp(x['related_count'], y['related_count']), reverse=True)[:100]
#                self.finish(json_dumps(top_list))
#            except Exception as e:
#                logger.error(e)
#                self.finish(json.dumps([]))
#
#        # 除了page维度,其他维度可关联两个维度
#        else:
#            for related_type in related_key_types:
#                if related_type == 'click':
#                    var_list.append('{}__visit__dynamic_count__1h__slot'.format(key_type))
#                elif related_type == 'incident':
#                    var_list.append('{}__visit__incident_count__1h__slot'.format(key_type))
#                elif related_type == 'strategy':
#                    var_list.append('{}__visit__incident_distinct_strategy__1h__slot'.format(key_type))
#                else:
#                    var_list.append('{}__visit__dynamic_distinct_{}__1h__slot'.format(key_type, related_type))
#            try:
#                if fromtime >= now_in_hour_start:
#                    # 当前小时数据,请求Java RPC
#                    # ret数据结构为{"result": {variable1: {key: value} } }
#                    key_variable = var_list[0]
#                    ret = get_latest_baseline_statistic(key_variable, var_list)
#                    top_statistic = ret.get('result', {}) if ret else {}
#
#                    for top, variables in top_statistic.items():
#                        top_dict = dict()
#
#                        for i in range(len(related_key_types)):
#                            related_type = related_key_types[i]
#                            related_var = var_list[i]
#                            related_value = variables.get(related_var, 0)
#                            v = len(related_value) if isinstance(related_value, (list, set)) else related_value
#                            top_dict[related_type] = v
#
#                        temp_dict[top] = top_dict
#                else:
#                    # 根据离线计算查询的数据,得到top key, 例:related_key_types: ['did', 'incident']
#                    # top_dict {variable1: {key1: set[1, 2, 3, 4]}, variable2: {key1: 3}}
#                    # temp_dict {key1: {'did': 4, 'incident': 3}}
#                    #todo
#                    key = "__GLOBAL__"
#                    top_statistic = data_client.get_offline_key_stat(key, key_type, fromtime, var_list)
#                    if top_statistic:
#                        for i in range(len(related_key_types)):
#                            related_type = related_key_types[i]
#                            var = var_list[i]
#                            related_values = top_statistic.get(var, {})
#
#                            for top, var_value in related_values.items():
#                                v = len(var_value) if isinstance(var_value, (list, set)) else var_value
#                                if top in temp_dict:
#                                    temp_dict[top][related_type] = v
#                                else:
#                                    temp_dict[top] = {related_type: v}
#
#                # 将当前小时或离线计算数据组合,top_list例:
#                # [{'value': '3', related_count: {'ip': 4, 'did': 5}},
#                #  {'value': '4', related_count: {'ip': 10, 'did': 5}}]
#                for k, v in temp_dict.items():
#                    if not k:
#                        continue
#                    top_dict = dict()
#                    top_dict['value'] = k
#                    top_dict['related_count'] = {t: v.get(t, 0) for t in related_key_types}
#
#                    if key_type == 'ip' and ip_match(k):
#                        country, province, city = find_ip_geo(k)
#                        top_dict['country'] = country
#                        top_dict['province'] = province
#                        top_dict['city'] = city
#
#                    top_list.append(top_dict)
#
#                order_type = related_key_types[0]
#                top_list = sorted(top_list, lambda x, y: cmp(x['related_count'][order_type], y['related_count'][order_type]), reverse=True)[:100]
#
#                self.finish(json_dumps(top_list))
#            except Exception as e:
#                logger.error(e)
#                self.finish(json_dumps([]))
#
#
#def find_ip_geo(ip):
#    from threathunter_common.geo import threathunter_ip
#    info = threathunter_ip.find(ip)
#    info_segs = info.split()
#    len_info_segs = len(info_segs)
#    country = ''
#    province = ''
#    city = ''
#    if len_info_segs == 1:
#        if info_segs[0] != u'未分配或者内网IP':
#            country = info_segs[0]
#    elif len_info_segs == 2:
#        country = info_segs[0]
#        province = info_segs[1]
#        city = ""
#    elif len_info_segs == 3:
#        country = info_segs[0]
#        province = info_segs[1]
#        city = info_segs[2]
#    else:
#        print 'length: {}, ip: {}'.format(len_info_segs, ip)
#    return country, province, city
#
#def dict_merge(src_dict, dst_dict):
#    """
#    将两个dict中的数据对应键累加,
#    不同类型值的情况:
#    >>> s = dict(a=1,b='2')
#    >>> d = {'b': 3, 'c': 4}
#    >>> dict_merge(s,d)
#    >>> t = {'a': 1, 'b': 5, 'c': 4}
#    >>> s == t
#    True
#    >>> s = dict(a=set([1,2]), )
#    >>> d = dict(a=set([2, 3]),)
#    >>> dict_merge(s,d)
#    >>> t = {'a':set([1,2,3])}
#    >>> s == t
#    True
#    >>> s = dict(a={'a':1, 'b':2})
#    >>> d = dict(a={'a':1, 'b':2})
#    >>> dict_merge(s, d)
#    >>> t = dict(a={'a':2, 'b':4})
#    >>> s == t
#    True
#    """
#    if src_dict is None:
#        return dst_dict
#    for k,v in dst_dict.iteritems():
#        if not src_dict.has_key(k):
#            src_dict[k] = v
#        else:
#
#            if isinstance(v, (basestring, int, float)):
#                src_dict[k] = int(v) + int(src_dict[k])
#            elif isinstance(v, set):
#                assert type(v) == type(src_dict[k]), 'key %s,dst_dict value: %s type: %s, src_dict value: %s type:%s' % (k, v, type(v), src_dict[k], type(src_dict[k]))
#                src_dict[k].update(v)
#            elif isinstance(v, dict):
#                assert type(v) == type(src_dict[k]), 'key %s,dst_dict value: %s type: %s, src_dict value: %s type:%s' % (k, v, type(v), src_dict[k], type(src_dict[k]))
#                dict_merge(src_dict[k], v)
#
#def get_top_click_percent(top_dict, total_click, top_num=None):
#    """
#    获取top_dict 前n个的点击数，及其所占总点击数的比例
#    """
#    if total_click is None or int(total_click) == 0 or top_dict is None:
#        return 0, 0
#    if top_num is None:
#        top_num = 3
#    
#    top_list = list( (k,v) for k,v in top_dict.iteritems())
#    top_list.sort(
#        key = lambda x: x[1],
#        reverse = True
#    )
#    top_n_clicks = reduce(lambda a,b: a+b, ( _[1] for _ in top_list[:top_num]) )
#    return top_n_clicks, top_n_clicks/float(total_click) * 100
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
#class RelatedPageStatisticHandler(BaseHandler):
#    REST_URL = '/platform/behavior/page_statistics'
#
#    def get(self):
#        """
#        page维度分析的左中的数据表格api
#        return:
#        {
#        total_page:
#        data: dict( host = '',
#          url = '',
#          alarm_count = 0,
#          click_count = 0,
#          ip_count = 0,
#          top_3_ip_click = 0,
#          top_3_ip_click_percent = 0,
#          user_count = 0,
#          top_3_user_click = 0,
#          top_3_user_click_percent = 0,
#          did_count = 0,
#          top_3_did_click=0,
#          top_3_did_click_percent=0)
#        }
#
#        @API
#        summary: 获取某个时间段内Page访问的统计排行情况
#        description: 获取一个小时内的页面访问及统计数据分析排行
#        parameters:
#          - name: endtime
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#            format: int64
#          - name: fromtime
#            in: query
#            description: 起始时间
#            required: true
#            type: integer
#            format: int64
#          - name: type
#            in: query
#            type: string
#            enum:
#              - host
#              - url
#            required: true
#            description: 数据聚合类型
#          - name: query
#            in: query
#            description: 过滤字段
#            required: false
#            type: string
#          - name: query_scope
#            in: query
#            type: string
#            enum:
#              - host
#              - url
#              - all
#            description: 查询范围
#            required: false
#        responses:
#          '200':
#            description: 返回点击列表
#            schema:
#              $ref: '#/definitions/pageStatistics'
#          default:
#            description: Error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        fromtime = self.get_argument('fromtime', default=None)
#        endtime = self.get_argument('endtime', default=None)
#        ttype = self.get_argument('type', default='')
#        query = self.get_argument('query', default='')
#        query_scope = self.get_argument('query_scope', default='')
#        fromtime = int(fromtime) / 1000.0
#        endtime = int(endtime) / 1000.0
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(fromtime), datetime.fromtimestamp(endtime))
#        # @issue 还不能支持只有url_path段的查询
#        # @issue 只填host， 也只是把host当成page来的查的
#        # @done
#        ret_list = []
#
#        # vars: blacklist_count_page, click_count_page, ip_distinctcount_page, ip_count_top_byip_page, user_distinctcount_page, user_count_top_byuser_page,
#        # 从总的里面找, 也就能搜索了 点击之后没有表格 @确认
#        incident_count_var_name = 'page__visit__incident_count__1h__slot'
#        incident_count_name = 'incident_count'
#        click_count_var_name = 'page__visit__dynamic_count__1h__slot'
#        click_count_name = 'click_count'
#        ip_count_var_name = 'page__visit__ip_dynamic_count__1h__slot'
#        ip_count_name = 'ip_count'
#        ip_distinct_var_name = 'page__visit__dynamic_distinct_ip__1h__slot'
#        user_count_var_name = 'page__visit__user_dynamic_count__1h__slot'
#        user_count_name = 'user_count'
#        user_distinct_var_name = 'page__visit__dynamic_distinct_user__1h__slot'
#        did_count_var_name = 'page__visit__did_dynamic_count__1h__slot'
#        did_count_name = 'did_count'
#        did_distinct_var_name = 'page__visit__dynamic_distinct_did__1h__slot'
#        ip_top_count_var_name = 'page__visit__ip_dynamic_count__1h__slot'
#        ip_top_name = 'top_3_ip_click'
#        ip_top_percent_name = 'top_3_ip_click_percent'
#        user_top_count_var_name = 'page__visit__user_dynamic_count__1h__slot'
#        user_top_name = 'top_3_user_click'
#        user_top_percent_name = 'top_3_user_click_percent'
#        did_top_count_var_name = 'page__visit__did_dynamic_count__1h__slot'
#        did_top_name = 'top_3_did_click'
#        did_top_percent_name = 'top_3_did_click_percent'
#        var_names = [incident_count_var_name, click_count_var_name, ip_count_var_name, ip_top_count_var_name, user_count_var_name, user_top_count_var_name, did_count_var_name, did_top_count_var_name]
#
#        key_type = 'page'
#        now_in_hour_start = get_hour_start()
#        logger.debug('fromtime: %s, this hour start timestamp:%s', fromtime, now_in_hour_start)
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(fromtime), datetime.fromtimestamp(endtime))
#        try:
#            if fromtime >= now_in_hour_start:
#                logger.debug(DEBUG_PREFIX+"在当前小时去获取...")
#                # 当前小时
#                # {var: key :}
#                var_list = [incident_count_var_name, ip_count_var_name, ip_distinct_var_name, user_count_var_name,
#                            user_distinct_var_name, did_count_var_name, did_distinct_var_name]
#                ret = get_latest_baseline_statistic(click_count_var_name, var_list, count=100, topcount=100)
#            else:
#                ret = data_client.get_offline_baseline(click_count_var_name, key_type, var_names, set(), int(fromtime*1000), count=100, topcount=100)
#            if ret:
#                page_ret = ret.get('result', dict())
#            else:
#                page_ret = dict()
#            page_dict = dict()
#            flag = False
#            for url, url_vars in page_ret.iteritems():
#                if not flag:
#                    logger.debug("url: %s, d : %s", url, url_vars)
#                url_dict = {}
#                host, url_path = parse_host_url_path(url)
#                if ttype == 'host':
#                    key = host
#                else:
#                    url_dict['url'] = url
#                    key = url
#                url_dict['host'] = host
#                url_dict[incident_count_name] = url_vars.get(incident_count_var_name, 0)
#                url_dict[click_count_name] = url_vars.get(click_count_var_name, 0)
#                url_dict[ip_count_name] = url_vars.get(ip_distinct_var_name, 0)
#                url_dict[ip_top_name] = url_vars.get(ip_count_var_name, {})
#                url_dict[did_count_name] = url_vars.get(did_distinct_var_name, 0)
#                url_dict[did_top_name] = url_vars.get(did_count_var_name, {})
#                url_dict[user_count_name] = url_vars.get(user_distinct_var_name, 0)
#                url_dict[user_top_name] = url_vars.get(user_top_count_var_name, {})
#
#                if not flag:
#                    logger.debug("url_dict: %s", url_dict)
#                if key in page_dict:
#                    page_dict[key][incident_count_name] += url_dict[incident_count_name]
#                    page_dict[key][click_count_name] += url_dict[click_count_name]
#                    page_dict[key][ip_count_name] += url_dict[ip_count_name]
#                    page_dict[key][did_count_name] += url_dict[did_count_name]
#                    page_dict[key][user_count_name] += url_dict[user_count_name]
#                    dict_merge(page_dict[key][ip_top_name], url_dict[ip_top_name])
#                    dict_merge(page_dict[key][did_top_name], url_dict[did_top_name])
#                    dict_merge(page_dict[key][user_top_name], url_dict[user_top_name])
#                else:
#                    page_dict[key] = url_dict
#                if not flag:
#                    logger.debug("page_dict: %s", page_dict)
#                    flag = True
#
#            # 获取数据后，计算点击数前三的ip、did、user
#            for url, url_vars in page_dict.iteritems():
#                # 计算ip_top
#                ip_top = url_vars.get(ip_top_name, {})
#                ip_top_list = sorted(ip_top.items(), key=lambda x: x[1], reverse=True)
#                ip_top_3 = ip_top_list[:3]
#                logger.debug("ip_top_3: %s", ip_top_3)
#                url_vars[ip_top_name] = sum([_[1] for _ in ip_top_3])
#                url_vars[ip_top_percent_name] = url_vars[ip_top_name] / float(url_vars[click_count_name]) * 100 if url_vars[click_count_name] else 0
#
#                # 计算did_top
#                did_top = url_vars.get(did_top_name, {})
#                did_top_list = sorted(did_top.items(), key=lambda x: x[1], reverse=True)
#                did_top_3 = did_top_list[:3]
#                url_vars[did_top_name] = sum([_[1] for _ in did_top_3])
#                url_vars[did_top_percent_name] = url_vars[did_top_name] / float(url_vars[click_count_name]) * 100 if url_vars[click_count_name] else 0
#
#                # 计算user_top
#                user_top = url_vars.get(user_top_name, {})
#                user_top_list = sorted(user_top.items(), key=lambda x: x[1], reverse=True)
#                user_top_3 = user_top_list[:3]
#                url_vars[user_top_name] = sum([_[1] for _ in user_top_3])
#                url_vars[user_top_percent_name] = url_vars[user_top_name] / float(url_vars[click_count_name]) * 100 if url_vars[click_count_name] else 0
#
#                ret_list.append(url_vars)
#            logger.debug(DEBUG_PREFIX+"过滤的查询词是 %s, 范围是%s, 查询前的大小是%s", str(query), str(query_scope), len(ret_list))
#            if query_scope == 'all':
#                ret_list = [ _ for _ in ret_list if query in _.get('host','') or query in _.get('url', '')]
#            elif query_scope == 'host':
#                ret_list = [ _ for _ in ret_list if query in _.get('host','')]
#            elif query_scope == 'url':
#                ret_list = [ _ for _ in ret_list if query in _.get('url','')]
#
##            logger.debug(DEBUG_PREFIX+"查询后的大小是%s", len(ret_list))
#            # @未来 这个访问的分页, 是在遍历key的时候跳过n个?再限定一下数量?
#            ret_list.sort(key=lambda x: x['incident_count'], reverse=True)
#            self.finish(json.dumps(dict(total_page=len(ret_list), data=ret_list[:100])))
##            self.finish(json.dumps(dict(total_page=len(ret_list), data=ret_list)))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#
#Request_Ids = dict() # id: dict( file, offset, query_file, total)
#
#class LogQuery(BaseHandler):
#    REST_URL = '/platform/logquery'
#
#    @property
#    def executor(self):
#        return utils.executor
##        return self.application.executor
#
#    @coroutine
#    def post(self):
#        """
#        日志查询
#        api不能向前翻页, 所以没有必要offset, 
#        Input: post body
#        {
#        'fromtime':'',
#        'endtime':'',
#        'page_size':int,
#        'temrs' : [{'op':, 'left':, 'right':},],
#        'request_id':"",
#        'show_cols': [],
#        'temp_query_file': (str),
#        'total': (int), # 
#        'page': (int), # 指定第一次查询之后日志的页数
#        }
#        Return:
#        {'values':
#          {'download_path':'' # 查询出来的完整日志api地址
#           'logs': [ {} ],
#           'total':int,
#          }
#        }
#        @API
#        summary: 日志查询
#        description: 根据查询条件过滤查询离线存储的日志
#        tags:
#          - platform
#        parameters:
#          -
#            name: query
#            in: body
#            required: true
#            type: string
#            description: 查询提交的json, fromtime, endtime, page_size, request_id, terms
#        responses:
#          '200':
#            description: 返回关联IP点击数地点排行
#            schema:
#              $ref: '#/definitions/topClickLocation'
#          default:
#            description: Unexcepted error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        try:
#            query_body = json.loads(self.request.body)
#        except Exception as err:
#            yield self.process_error(400, "invalid request body: %s" % err.message )
#        
#        try:
#            with (yield query_lock.acquire(timeout=5)):
#                fromtime = query_body.get('fromtime', None)
#                endtime = query_body.get('endtime', None)
#                page_size = query_body.get('page_size', 20)
#                page = query_body.get('page', 1)
#                temp_query_file = query_body.get('temp_query_file', '')
#                request_id = query_body.get('request_id', None)
#                total = query_body.get('total', 0)
#                terms = query_body.get('terms', None)
#                show_cols = query_body.get('show_cols', [])
#                
#                if request_id is None or fromtime is None or fromtime is None:
#                    yield self.process_error(400, "without request_id or fromtime args in json body")
#                fromtime = fromtime/ 1000.0
#                endtime = endtime/ 1000.0
#                logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(fromtime), datetime.fromtimestamp(endtime))
#                logger.debug(DEBUG_PREFIX+u"查询之前的状态:%s", Request_Ids)
#
#                # 标识是否需要更新数据库日志查询状态
#                is_updated_logquery = False
#
#                if temp_query_file:
#                    if request_id in Request_Ids:
#                        # 继续查询
#                        q = Request_Ids[request_id]
#                        if q['fromtime'] != fromtime or\
#                           q['endtime'] != endtime or q['terms'] != terms:
#                            # 如果查询条件变化了, 更新之前查询的条件和中间结果
#                            q['fromtime'] = fromtime
#                            q['endtime'] = endtime
#                            q['terms'] = terms
#                            q.pop('offset', None)
#                            q.pop('temp_query_file', None)
#                            q.pop('last_file', None)
#                            q.pop('total', None)
#                        query_file = opath.join(settings.LogQuery_Path, q['temp_query_file']) 
#                    else:
#                        # 重启之后继续查询
#                        query_file_name = temp_query_file.rsplit('/',1)[-1]
#                        query_file = opath.join(settings.LogQuery_Path, query_file_name) 
#                        query_file_size = os.stat(query_file).st_size
#                        q = Request_Ids[request_id] = dict(
#                            is_running=False,
#                            fromtime=fromtime,
#                            endtime=endtime,
#                            terms=terms,
#                            temp_query_file=query_file_name,
#                            query_file_size=query_file_size)
#                    start_line = (page - 1) * page_size
#                    end_line = start_line + page_size
#                    records = []
#                    with open(query_file, 'r') as f:
#                        # 读取字段名说明
#                        f.readline()
#                        for l in xrange(0, end_line):
#                            if l < start_line:
#                                f.readline()
#                            else:
#                                line = f.readline()
#                                if not line:
#                                    continue
#                                trim_values = (_.rstrip() for _ in line.split(','))
#                                records.append( dict(zip(show_cols, trim_values)))
#                    self.finish(json.dumps({
#                        'status':0,
#                        'download_path':self.REST_URL + '/' + q['temp_query_file'],
#                        'logs': records,
#                        'total': total,
#                        'query_file_size': q.get('query_file_size',0),
#                    }))
#                    # 写入文件成功后更新数据库状态
#                    is_updated_logquery = True
#                    return
#                else:
#                    if request_id in Request_Ids:
#                        # 第一次查询没有产生查询文件
#                        self.finish(json.dumps({"status":-1, "error":u"该查询配置第一次查询时,没有生成查询的下载文件，无法翻页"}))
#                        return
#                    else:
#                        # 第一次查询
#                        write_to_file = True
#                        q = Request_Ids[request_id] = dict(is_running=False, fromtime=fromtime,
#                        endtime=endtime, terms=terms)
#    #                    q['is_running'] = True
#                        query_result = yield self.query_log(
#                            fromtime, endtime, terms, show_cols=show_cols, size = page_size,
#                            offset=q.get('offset', None), specify_file_path=q.get('last_file', None),
#                            write_to_file=write_to_file, request_id=request_id)
#                
#                        if query_result:
#                            logger.debug(DEBUG_PREFIX+u'查询结果: %s', query_result.keys())
#                            q['offset'] = query_result.get('last_offset',None)
#                            q['last_file'] = query_result.get('last_file',None)
#                            if write_to_file:
#                                q['total'] = query_result['total']
#                                q['temp_query_file'] = query_result['temp_log_path']
#                                
#                
#                            if len(query_result.get('logs',[])) < page_size:
#                                # 查询结束，查询不满一页
#                                q['is_haust'] = True
#                            logger.debug(DEBUG_PREFIX+u"查询之后的状态:%s", Request_Ids)
#                            logger.debug(DEBUG_PREFIX+u"查询出来的日志条数:%s", len(query_result.get('logs', [])))
#                            if q['temp_query_file']:
#                                download_path = self.REST_URL + '/' + q['temp_query_file']
#                                query_file = opath.join(settings.LogQuery_Path, q['temp_query_file']) 
#                                q['query_file_size'] = os.stat(query_file).st_size
#                            else:
#                                download_path = None
#        
#                            self.finish(json.dumps({
#                                'status':0,
#                                'download_path':download_path,
#                                'logs': query_result['logs'],
#                                'total':q['total'],
#                                'query_file_size':q.get('query_file_size',0),
#                            }))
#                            # 写入文件成功后更新数据库状态
#                            is_updated_logquery = True
#                        else:
#                            logger.info('查询接口返回为空')
#                            self.finish(json.dumps({'status':0,'logs':[], 'total':0, 'info':'没有查询到对应日志', 'query_file_size':0}))
#                        return
#
#        except gen.TimeoutError:
#            self.finish(json.dumps({"status":-1, "error":u"已经有别人正在使用该接口."}))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status":-1, "error":e.message}))
#        finally:
#            if locals().has_key('q'):
#                q['is_running'] = False
#                if is_updated_logquery:
#                    LogQueryDao().update_logquery_file(request_id, page=page,
#                                                       total=q['total'], temp_query_file=q['temp_query_file'])
#
#    @run_on_executor
#    def query_log(self, *args, **kwargs):
#        return persist_utils.query_log(*args, **kwargs)
#
#class ClickLocation(BaseHandler):
#
#    REST_URL = '/platform/behavior/top/clicks_location'
#
#    def get(self):
#        """
#        return [{city:d, click_count:d}, ...]
#        @API
#        summary: 获取TOP100关联IP点击数对应地区排行
#        description: 获取不同维度关联的IP TOP100点击数对应地区排行
#        tags:
#          - platform
#        parameters:
#          - name: fromtime
#            in: query
#            description: 开始时间
#            required: true
#            type: integer
#            format: int64
#          - name: endtime
#            in: query
#            description: 结束时间
#            required: true
#            type: integer
#            format: int64
#          - name: key
#            in: query
#            description: 当key_type为page才需要
#            required: false
#            type: string
#          - name: key_type
#            in: query
#            enum:
#              - ip
#              - user
#              - did
#              - page
#            description: 维度类型
#            required: true
#            type: string
#        responses:
#          '200':
#            description: 返回关联IP点击数地点排行
#            schema:
#              $ref: '#/definitions/topClickLocation'
#          default:
#            description: Unexcepted error
#            schema:
#              $ref: '#/definitions/Error'
#        """
#        # 关联ip的榜单来生成一个关联地理信息的榜单 一种filter
#        # @done
#        fromtime = self.get_argument('fromtime', default=None)
#        endtime = self.get_argument('endtime', default=None)
#        key_type = self.get_argument('key_type', default='')
#        key = self.get_argument('key', default='')
#        fromtime = int(fromtime) / 1000.0
#        endtime = int(endtime) / 1000.0
#        logger.debug(DEBUG_PREFIX+u"查询的时间范围是%s ~ %s", datetime.fromtimestamp(fromtime), datetime.fromtimestamp(endtime))
#
#        if key_type == 'page' and not key:
#            # page维度 是指定了 key才去查的
#            return
#
#        geo_varname = '{}__visit__geo_dynamic_count__1h__slot'.format(key_type)
#        count_varname = '{}__visit__dynamic_count__1h__slot'.format(key_type)
#        ip_varname = '{}__visit__ip_dynamic_count__1h__slot'.format(key_type)
#        ret_dict = dict()
#        now_in_hour_start = get_hour_start()
#        try:
#            if fromtime >= now_in_hour_start:
#                if key:
#                    rpc_ret = get_latest_statistic(key, key_type, [geo_varname])
#                    ret_dict = rpc_ret.get(geo_varname, {}) if rpc_ret else {}
#                else:
#                    # 有key时候,请求baseline RPC进行merge
#                    # ret: { varname: ip1:city:count }
#                    var_list = [count_varname, geo_varname]
#                    merge_list = [geo_varname]
#                    rpc_ret = get_latest_baseline_statistic(count_varname, var_list, merge_list)
#                    ret_dict = rpc_ret.get('merges', {}).get(geo_varname, {}) if rpc_ret else {}
#            else:
#                # 当前小时之前的离线数据
#                if key:
#                    # 如果指定key, 维度为IP时,直接查询访问数量
#                    if key_type == 'ip':
#                        ret = get_statistic(key, key_type, fromtime, endtime, [count_varname])
#                        count = ret.get(count_varname, 0) if ret else 0
#                        if count:
#                            _, _, city = find_ip_geo(key)
#                            dict_merge(ret_dict, {city: count})
#                    else:
#                        # 根据key查询geo统计访问数
#                        ret = get_statistic(key, key_type, fromtime, endtime, [geo_varname])
#                        ret_dict = ret.get(geo_varname, dict()) if ret else dict()
#                        # 如果城市不存在,则统计top ip,然后merge ip所在城市
#                        if None in ret_dict:
#                            top_ip_ret = get_statistic(key, key_type, fromtime, endtime, [ip_varname])
#                            top_ip_dict = top_ip_ret.get(ip_varname, {}) if top_ip_ret else {}
#                            for ip, count in top_ip_dict.items():
#                                _, _, city = find_ip_geo(ip)
#                                dict_merge(ret_dict, {city: count})
#                else:
#                    # 维度为ip时,统计访问前100的IP所在城市
#                    if key_type == 'ip':
#                        ret = get_all_statistic(key_type, fromtime, endtime, [count_varname])
#                        top_ip_dict = ret.get(count_varname, {}) if ret else {}
#                        sorted_top_ip = sorted(top_ip_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)[:100]
#
#                        for ip, count in sorted_top_ip:
#                            _, _, city = find_ip_geo(ip)
#                            dict_merge(ret_dict, {city: count})
#                    else:
#                        # 维度为user、did时,先统计访问前100的user或did,再统计每个user、did的访问top 1 geo城市
#                        ret = get_all_statistic(key_type, fromtime, endtime, [count_varname])
#                        top_dict = ret.get(count_varname, {}) if ret else {}
#                        sorted_top_dict = sorted(top_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)[:100]
#
#                        for key, _ in sorted_top_dict:
#                            top_geo_ret = get_statistic(key, key_type, fromtime, endtime, [geo_varname])
#                            top_geo_dict = top_geo_ret.get(geo_varname, {}) if top_geo_ret else {}
#                            sorted_top_geo = sorted(top_geo_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)[:1]
#
#                            if sorted_top_geo:
#                                city, count = sorted_top_geo[0]
#                                if city:
#                                    dict_merge(ret_dict, {city: count})
#                                else:
#                                    # 如果城市不存在,则统计top ip,然后merge ip所在城市
#                                    top_ip_ret = get_statistic(key, key_type, fromtime, endtime, [ip_varname])
#                                    top_ip_dict = top_ip_ret.get(ip_varname, {}) if top_ip_ret else {}
#                                    sorted_top_ip = sorted(top_ip_dict.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)[:1]
#                                    if sorted_top_ip:
#                                        ip, count = sorted_top_ip[0]
#                                        _, _, city = find_ip_geo(ip)
#                                        dict_merge(ret_dict, {city: count})
#
#            # geo city(str):count(int)
#            top_list = [dict(city=k, click_count=v) for k, v in ret_dict.iteritems()]
#            top_list.sort(key=lambda k: k['click_count'], reverse=True)
#            self.finish(json_dumps(top_list))
#        except Exception as e:
#            traceback.print_exc()
#            self.finish(json.dumps({"status": -1, "error": e.message}))
#
#
#from nebula.services import babel
#eventQueryClient = babel.get_eventquery_client()
#
#last_get_ts = 0
#cached_data = None
#cached_key = None
#
#def get_latest_events(key, key_type, fromtime=None, size=None, event_id=None, only_count=False):
#    logger.debug(DEBUG_PREFIX+u"获取最近的事件们key:%s, type:%s, key_type:%s", key, type(key), key_type)
#
##    global last_get_ts, cached_data, cached_key
#    now = millis_now()
##    if now - last_get_ts < 30000 and cached_key == key:
##        logger.debug(DEBUG_PREFIX+u"从cache返回了~~~")
##        return cached_data
#
#
#    prop_dict = dict(key_type=key_type, only_count=only_count)
#    if fromtime:
#        prop_dict['fromtime'] = fromtime
#    if size:
#        prop_dict['size'] = size
#    if event_id:
#        prop_dict['eventid'] = event_id
#
#    request = Event("__all__", "eventquery_request", key, millis_now(), prop_dict)
#    response = eventQueryClient.send(request, key, block=False, timeout=5)
#
#    if response[0]:
#        value = response[1].property_values.get("result")
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, value)
#        cached_data = value
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#        cached_data = 0 if only_count else []
#
##    last_get_ts = now
##    cached_key = key
##    print 9999, len(cached_data)
#    return cached_data
#
#statQueryClient = babel.get_statquery_client()
#
#last_stat_get_ts = 0
#stat_cached_data = None
#stat_cached_key = None
#
#def get_latest_statistic(key, key_type, var_list, subkeys=None):
#    data = {"app": "nebula", "count": 100, "var_list": var_list}
#    if subkeys:
#        data['subkeys'] = subkeys
#    logger.debug(DEBUG_PREFIX+u"获取最近的事件们key:%s, type:%s, key_type:%s, 变量列表:%s", key, type(key), key_type, var_list)
#    request = Event("__all__", "keystatquery_request", key, millis_now(), data)
#    response = statQueryClient.send(request, key, block=False, timeout=5)
#
#    if response[0]:
#        value = response[1].property_values.get("result")
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, value)
#        stat_cached_data = value
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#        stat_cached_data = dict()
#
##    last_stat_get_ts = now
##    stat_cached_key = key
##    print 9999, len(stat_cached_data)
#    return stat_cached_data
#
#offline_stat_client = babel.get_offline_stat_client()
#
##def get_statistic(key, key_type, fromtime, endtime, var_list):
##    return get_offline_statistic(key, key_type, fromtime, endtime, var_list)
##
##def get_all_statistic(key_type, fromtime, endtime, var_list):
##    return get_offline_statistic('', key_type, fromtime, endtime, var_list, True)
#
#def get_offline_statistic(key, key_type, fromtime, endtime, var_names, if_all_key=False):
#    logger.debug(DEBUG_PREFIX+u"获取最近的事件们key:%s, type:%s, key_type:%s, 开始时间: %s, 结束时间:%s, 变量列表:%s, 是否是拿总的key的统计? %s", key, type(key), key_type, fromtime, endtime, var_names, if_all_key)
#    opt_dict = {
#        'fromtime': fromtime,
#        'endtime': endtime,
#        'var_names': var_names,
#        'if_all_key': if_all_key,
#        'key_type': key_type,
#    }
#    request = Event("__all__", "offline_stat_query_request", key, millis_now(), opt_dict)
#    response = offline_stat_client.send(request, key, block=False, timeout=5)
#    logger.debug('返回的response: %s', response)
#
#def get_current_hour_timestamp():
#    """
#    返回当前小时整点时间戳,ex. 1470913200000
#    """
#    return curr_timestamp() / 3600 * 3600 * 1000
#
#
#Incident_Query_Client = babel.get_incident_query_client()
#
#
#def get_latest_incident(var_list, key='', key_variable='', count=20, page=0):
#    Incident_Query_Client = babel.get_incident_query_client()
#    data = dict()
#    data['app'] = 'nebula'
#    data['count'] = count
#    data['page'] = page
#    if key:
#        data['key'] = key
#    if key_variable:
#        data['key_variable'] = key_variable
#    data['var_list'] = var_list
#
#    request = Event("nebula_web", "incidentquery", key, millis_now(), data)
#    response = Incident_Query_Client.send(request, key, 10)
#    if response[0]:
#        values = [event.property_values for event in response[1]]
#        result = dict()
#        for value in values:
#            dict_merge(result, value)
#
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, result)
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#        result = dict()
#
#    return result
#
#Baseline_Query_client = babel.get_baseline_query_client()
#
#
#def get_latest_baseline_statistic(key_variable, var_list, merge_list=None, count=100, topcount=1):
#    data = dict()
#    data['app'] = 'nebula'
#    data['count'] = count
#    data['topcount'] = topcount
#    data['key_variable'] = key_variable
#    data['var_list'] = var_list
#    if merge_list:
#        data['merge_list'] = merge_list
#
#    request = Event("nebula_web", "baselinekeystatquery", '', millis_now(), data)
#    response = Baseline_Query_client.send(request, '', 10)
#    if response[0]:
#        values = [event.property_values for event in response[1]]
#        result = dict()
#        for value in values:
#            dict_merge(result, value)
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, result)
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#        result = dict()
#
#    return result
#
#def get_online_clicks_period(key, key_type, fromtime, endtime):
#    query_type = 'clicks_period'
#    res = get_online_detail_data(key, key_type, fromtime, endtime, query_type)
#    return res.get(query_type, None)
#    
#def get_online_visit_stream(key, key_type, fromtime, endtime):
#    query_type = 'visit_stream'
#    res = get_online_detail_data(key, key_type, fromtime, endtime, query_type)
#    return res.get(query_type, None)
#    
#def get_online_clicks(key, key_type, fromtime, endtime, limit, query=None):
#    query_type = 'clicks'
#    res = get_online_detail_data(key, key_type, fromtime, endtime, query_type, query=query, log_limit=limit)
#    return res.get(query_type, None)
#
#Online_Detail_Client = babel.get_online_detail_client()
#
#def get_online_detail_data(key, key_type, fromtime, endtime, query_type, log_limit=None, stream_limit=None, query=None):
#    if not query:
#        query = []
#
#    if log_limit is None:
#        log_limit = 20
#        
#    if stream_limit is None:
#        stream_limit = 2000
#        
#    prop = dict(
#        clickscount=log_limit,
#        query=query,
#        query_type=query_type,
#        from_time=int(fromtime),
#        end_time=int(endtime),
#        dimension=key_type,
#    )
#    req = Event("nebula", "clickstreamrequest", key, millis_now(), prop)
#    res = Online_Detail_Client.send(req, key, block=False, timeout=5)
#    if res[0]:
#        result = res[1].property_values
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", res, result)
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", res)
#        result = dict()
#
#    return result

