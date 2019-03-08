# -*- coding: utf-8 -*-
import requests

import unittest

default_pycount = """
import json

def event(properties):
    properties = json.loads(properties)
    result = []
    r1 = dict()
    r1['properties'] = properties
    r1['event_name'] = "HTTP_EVENT_TEST_0213"
    r1['event_result'] = True
    result.append(r1)            
    return json.dumps(result)
"""
headers = {
    'Cookie': 'username=threathunter_test; group_id="2|1:0|10:1550028927|8:group_id|4:Mg==|f5f07ff168fcb2cb6a82d6089117f83e217422d2c50f5a6d21a0d6fbd0565e48"; user_id="2|1:0|10:1550028927|7:user_id|4:Mg==|b479445d3374416e0bb4d95fa950da361f221be9c5b4680a3f256da0f73fc9cf"; user="2|1:0|10:1550028927|4:user|24:dGhyZWF0aHVudGVyX3Rlc3Q=|4b0fd7f33da78ac7b56353d766d7cc9b5bff4caceaac37a0a67407f90a44588b"; auth="2|1:0|10:1550028927|4:auth|44:ZmU1YjI1NmY0ZWU2M2Y0ODM3Zjg2OTYwOWM2ZmU3YWE=|e1daa99be00f35afa99f4391fc2cd2658c8d45aacc19fafb33ec0ac917f50a8a"'
}


class TestAddBaseEvent(unittest.TestCase):

    def test_add_event(self):
        "新增基础事件"
        url = 'http://112.74.58.210:9003/nebula/NewNebulaStrategy'
        a = [{
            "py_name": "HTTP_EVENT_TEST_0213",
            "py_content": default_pycount,
            "app": "nebula",
            "name": "HTTP_EVENT_TEST_0213",
            "visible_name": "动态事件请求-测试_0213",
            "remark": "动态事件请求-测试_0213",
            "type": "base",
            "version": "1.0",
            "source": [{
                "app": "nebula",
                "name": "HTTP_DYNAMIC"
            }],
            "properties": [
                {
                    "name": "c_ip",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "客户端ip",
                    "remark": "客户端IP(默认取xforward最后一个)"
                },
                {
                    "name": "sid",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "session会话ID",
                    "remark": "session会话ID"
                },
                {
                    "name": "uid",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "用户ID",
                    "remark": "用户ID"
                },
                {
                    "name": "did",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "设备ID",
                    "remark": "设备ID"
                },
                {
                    "name": "platform",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "客户端类型",
                    "remark": "客户端类型"
                },
                {
                    "name": "page",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "伪静态页面加工后地址",
                    "remark": "伪静态页面加工后地址(全部小写，去端口)"
                },
                {
                    "name": "c_port",
                    "type": "long",
                    "subtype": "",
                    "visible_name": "客户端端口",
                    "remark": "客户端端口"
                },
                {
                    "name": "c_bytes",
                    "type": "long",
                    "subtype": "",
                    "visible_name": "请求内容大小",
                    "remark": "请求内容大小"
                },
                {
                    "name": "c_body",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "请求内容",
                    "remark": "请求内容(json和form表单脱敏)"
                },
                {
                    "name": "c_type",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "请求内容类型",
                    "remark": "请求内容类型"
                },
                {
                    "name": "s_ip",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "服务端IP",
                    "remark": "服务端IP"
                },
                {
                    "name": "s_port",
                    "type": "long",
                    "subtype": "",
                    "visible_name": "服务端端口",
                    "remark": "服务端端口"
                },
                {
                    "name": "s_bytes",
                    "type": "long",
                    "subtype": "",
                    "visible_name": "响应内容大小",
                    "remark": "响应内容大小"
                },
                {
                    "name": "s_body",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "响应内容",
                    "remark": "响应内容(json和form表单脱敏)"
                },
                {
                    "name": "s_type",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "响应内容类型",
                    "remark": "响应内容类型(全部小写)"
                },
                {
                    "name": "host",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "主机地址",
                    "remark": "主机地址(全部小写，去端口)"
                },
                {
                    "name": "uri_stem",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "请求路径",
                    "remark": "请求路径(全部小写)"
                },
                {
                    "name": "uri_query",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "请求参数",
                    "remark": "请求参数(全部小写,脱敏)"
                },
                {
                    "name": "referer",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "引用页面",
                    "remark": "引用页面(全部小写，去端口)"
                },
                {
                    "name": "method",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "请求方法",
                    "remark": "请求方法(全部大写)"
                },
                {
                    "name": "status",
                    "type": "long",
                    "subtype": "",
                    "visible_name": "响应状态码",
                    "remark": "响应状态码"
                },
                {
                    "name": "cookie",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "用户身份存储",
                    "remark": "用户身份存储"
                },
                {
                    "name": "useragent",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "用户代理信息",
                    "remark": "用户代理信息(浏览器类型)"
                },
                {
                    "name": "xforward",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "用户的xff header",
                    "remark": "用户的xff header，具体header名可配"
                },
                {
                    "name": "request_time",
                    "type": "long",
                    "subtype": "",
                    "visible_name": "请求消耗时间",
                    "remark": "请求消耗时间(毫秒精度)"
                },
                {
                    "name": "request_type",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "请求类型",
                    "remark": "请求类型"
                },
                {
                    "name": "referer_hit",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "referer是否命中",
                    "remark": "referer是否命中"
                },
                {
                    "name": "notices",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "风险名单",
                    "remark": "风险名单"
                },
                {
                    "name": "geo_city",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "地理位置",
                    "remark": "地理位置"
                },
                {
                    "name": "geo_province",
                    "type": "string",
                    "subtype": "",
                    "visible_name": "地理位置",
                    "remark": "地理位置"
                }
            ]
        }]
        response = requests.request('PUT', url, headers=headers, json=a)
        res_dict = response.json()
        print res_dict
        self.assertEqual(res_dict["status"], 0)

    def test_delete_event(self):
        "删除基础事件"
        url = 'http://112.74.58.210:9003/nebula/NewNebulaStrategy'
        data = {
            "app": "nebula",
            "name": "HTTP_EVENT_TEST_0213"
        }
        response = requests.delete(url, headers=headers, json=data)
        res_dict = response.json()
        print res_dict
        self.assertEqual(res_dict["status"], 0)