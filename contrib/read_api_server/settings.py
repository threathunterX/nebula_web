#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import path as opath

#web监听设置
WebUI_Port = 9001
WebUI_Address = '0.0.0.0'
Auth_Code = '7a7c4182f1bef7504a1d3d5eaa51a242'

# 黑白名单监听配置
ReadApi_Master_Port = 9002
ReadApi_Master_Address = '0.0.0.0'
ReadApi_Client_Port = 9003
ReadApi_Client_Address = '0.0.0.0'
ReadApi_subprocess_number = 4

# 进程启动所需Python web配置路径
Nebula_Python_Path = opath.join('/home/threathunter/nebula/nebula_web/venv/bin/python')
