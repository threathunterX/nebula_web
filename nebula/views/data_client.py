# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

#from nebula.services import babel
#from threathunter_common.util import millis_now
#from threathunter_common.event import Event

logger = logging.getLogger('nebula.api.data_client')

DEBUG_PREFIX = '==============='

#statQueryClient = babel.get_statquery_client()
#GlobalSlotQueryClient = babel.get_globalslot_query_client()
#Baseline_Query_client = babel.get_baseline_query_client()
#RiskEventInfoClient = babel.get_risk_event_info_query_client()
#RealtimeQueryClent = babel.get_realtime_query_client()

#OfflineBaselineClient = babel.get_offline_baseline_query_client()
#OfflineKeyStatClient = babel.get_offline_keystat_query_client()
#OfflineContinuousClient = babel.get_offline_continuous_query_client()

def dict_merge(src_dict, dst_dict):
    """
    将两个dict中的数据对应键累加,
    不同类型值的情况:
    >>> s = dict(a=1,b='2')
    >>> d = {'b': 3, 'c': 4}
    >>> dict_merge(s,d)
    >>> t = {'a': 1, 'b': 5, 'c': 4}
    >>> s == t
    True
    >>> s = dict(a=set([1,2]), )
    >>> d = dict(a=set([2, 3]),)
    >>> dict_merge(s,d)
    >>> t = {'a':set([1,2,3])}
    >>> s == t
    True
    >>> s = dict(a={'a':1, 'b':2})
    >>> d = dict(a={'a':1, 'b':2})
    >>> dict_merge(s, d)
    >>> t = dict(a={'a':2, 'b':4})
    >>> s == t
    True
    """
    if src_dict is None:
        return dst_dict
    for k,v in dst_dict.iteritems():
        if not src_dict.has_key(k):
            src_dict[k] = v
        else:

            if isinstance(v, (basestring, int, float)):
                src_dict[k] = int(v) + int(src_dict[k])
            elif isinstance(v, set):
                assert type(v) == type(src_dict[k]), 'key %s,dst_dict value: %s type: %s, src_dict value: %s type:%s' % (k, v, type(v), src_dict[k], type(src_dict[k]))
                src_dict[k].update(v)
            elif isinstance(v, dict):
                assert type(v) == type(src_dict[k]), 'key %s,dst_dict value: %s type: %s, src_dict value: %s type:%s' % (k, v, type(v), src_dict[k], type(src_dict[k]))
                dict_merge(src_dict[k], v)

#def get_offline_key_stat(key, dimension, timestamp, var_list, count=100):
#    data = dict()
#    data['app'] = 'nebula'
#    data["key"] = key
#    data["count"] = count
#    if isinstance(var_list, list):
#        data["var_list"] = var_list
#    elif isinstance(var_list, (str, unicode)):
#        data["var_list"] = var_list.split(",")
#    else:
#        return dict()
#    data["dimension"] = dimension
#    data["timestamp"] = timestamp
#
#    req = Event("nebula", "offlinekeystatquery", key, millis_now(), data)
#    KeyStatClient = babel.get_offline_keystat_query_client()
#    response = KeyStatClient.send(req, key, block=False, timeout=5)
#    if response[0]:
#        if isinstance(response[1], list):
#            result = dict()
#            for r in response[1]:
#                logger.debug(DEBUG_PREFIX+"返回的一个event:%s", r)
#                dict_merge(result, r.property_values.get("result", {}))
#        else:
#            result = response[1].property_values.get("result", {})
#
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, result)
#        return result
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#
#def get_offline_baseline(key_variable, key_dimension, var_list, merge_list, timestamp, count=100, topcount=1):
#    data = dict()
#    data['count'] = count
#    data['topcount'] = topcount
#    data['key_variable'] = key_variable if isinstance(key_variable, list) else [key_variable, ]
#    data['key_dimension'] = key_dimension
#    data['var_list'] = var_list
#    data['merge_list'] = list(merge_list)
#    data["timestamp"] = timestamp
#    
#    req = Event("nebula", "offline_baselinekeystatquery", "", millis_now(), data)
#    BaselineClient = babel.get_offline_baseline_query_client()
#    response = BaselineClient.send(req, "", timeout=10)
#    if response[0]:
#        if isinstance(response[1], list):
#            result = dict()
#            for r in response[1]:
#                logger.debug(DEBUG_PREFIX+"返回的一个event:%s", r)
#                dict_merge(result, r.property_values or dict())
#        else:
#            result = response[1].property_values or dict()
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, result)
#        return result
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#
#def get_offline_continuous(key, dimension, timestamps, var_list):
#    data = dict()
#    data["key"] = key
#    data["dimension"] = dimension
#    data["var_list"] = var_list
#    data["timestamps"] = timestamps
#    req = Event("nebula", "continuousquery", key, millis_now(), data)
#    ContinuousClient = babel.get_offline_continuous_query_client()
#    response = ContinuousClient.send(req, key, block=False, timeout=5)
#        
#    if response[0]:
#        if isinstance(response[1], list):
#            result = dict()
#            for r in response[1]:
#                logger.debug(DEBUG_PREFIX+"返回的一个event:%s", r)
#                dict_merge(result, r.property_values.get("result", {}))
#        else:
#            result = response[1].property_values.get("result", {})
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, result)
#        return result
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)

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
#        result = response[1].property_values
#        logger.debug(DEBUG_PREFIX+"有返回的结果是:%s, 返回的结果是%s", response, result)
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#        result = dict()
#
#    return result
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
#    return stat_cached_data

#def get_global_statistic(var_list, subkeys=None):
#    data = {"app": "nebula", "count": 100, "var_list": var_list}
#    if subkeys:
#        data['subkeys'] = subkeys
#    request = Event("__all__", "globalslotquery_request", '', millis_now(), data)
#    response = GlobalSlotQueryClient.send(request, '', block=False, timeout=5)
#
#    if response[0]:
#        values = [event.property_values.get("result") for event in response[1]]
#        logger.debug(DEBUG_PREFIX + "有返回的结果是:%s, 返回的结果是%s", response, values)
#        result = None
#        if values:
#            if isinstance(values[0], (int, float)):
#                result = sum(values)
#            elif isinstance(values[0], dict):
#                result = dict()
#                for value in values:
#                    dict_merge(result, value)
#    else:
#        logger.debug(DEBUG_PREFIX+"当前没有事件..., 返回的是%s", response)
#        result = dict()
#
#    return result


#def get_realtime_statistic(key, key_type, var_list):
#    data = {"app": "nebula", "count": 20, "var_list": var_list, "dimension": key_type}
#    request = Event("__all__", "realtimequery_request", key, millis_now(), data)
#    response = RealtimeQueryClent.send(request, key, False, 10)
#
#    if response[0]:
#        result = response[1].property_values.get("result", {})
#    else:
#        result = {}
#    return result
#
#
#def get_threat_map(from_time, end_time, limit=1000):
#    # 初始化incidenteventinfoquery RPC client
#    property_values = {
#        'from_time': from_time,
#        'end_time': end_time,
#        'limit': limit
#    }
#    request = Event("nebula_web", "riskeventsinfoquery", '', millis_now(), property_values)
#    response = RiskEventInfoClient.send(request, '', False, 10)
#    if response[0]:
#        result = response[1].property_values.get("result", [])
#        if result is None:
#            return False, '导弹图参数错误'
#        else:
#            return True, result
#    else:
#        return False, '导弹图查询超时'


def find_ip_geo(ip):
    from threathunter_common.geo import threathunter_ip
    info = threathunter_ip.find(ip)
    info_segs = info.split()
    len_info_segs = len(info_segs)
    country = ''
    province = ''
    city = ''
    if len_info_segs == 1:
        if info_segs[0] != u'未分配或者内网IP':
            country = info_segs[0]
    elif len_info_segs == 2:
        country = info_segs[0]
        province = info_segs[1]
        city = ""
    elif len_info_segs == 3:
        country = info_segs[0]
        province = info_segs[1]
        city = info_segs[2]
    else:
        logger.error('get ip geo fail, length: %s, ip: %s', len_info_segs, ip)
    return country, province, city
    
def find_mobile_geo(mobile, country_code=None):
    from threathunter_common.geo import phonelocator
    
    info = phonelocator.get_geo(mobile, country_code)
    country, description = info.split()
    
    return country, description