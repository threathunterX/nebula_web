#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from os import path as opath

from complexconfig.loader.file_loader import FileLoader
from complexconfig.parser.properties_parser import PropertiesParser
from complexconfig.config import Config, CascadingConfig
from complexconfig.configcontainer import configcontainer

# debug 模式
DEBUG = True

# path
Base_Path = opath.dirname(__file__)

# build conf path
Conf_Local_Path = opath.join(Base_Path, "conf", "setting.conf")
Conf_Global_Path = "/etc/nebula/nebula.conf"
Conf_Web_Path = "/etc/nebula/web/settings.conf"
if not os.path.exists(Conf_Global_Path) or not os.path.isfile(Conf_Global_Path):
    print "!!!!Fatal, global conf path {} doesn't exist, using the local path {}".format(Conf_Global_Path, Conf_Local_Path)
    Conf_Global_Path = Conf_Local_Path
if not os.path.exists(Conf_Web_Path) or not os.path.isfile(Conf_Web_Path):
    print "!!!!Fatal, web conf path {} doesn't exist, using the local path {}".format(Conf_Web_Path, Conf_Local_Path)

# init the global config
global_config_loader = FileLoader("global_config_loader", Conf_Global_Path)
global_config_parser = PropertiesParser("global_config_parser")
global_config = Config(global_config_loader, global_config_parser)
global_config.load_config(sync=True)

# init the web config
web_config_loader = FileLoader("web_config_loader", Conf_Web_Path)
web_config_parser = PropertiesParser("web_config_parser")
web_config = Config(web_config_loader, web_config_parser)
web_config.load_config(sync=True)

# build the cascading config
# file config will be updated every half an hour, while the web config
# will be updated every 5 minute
cascading_config = CascadingConfig(global_config, web_config)
configcontainer.set_config("nebula", cascading_config)
_config = configcontainer.get_config("nebula")

Nebula_Path = 'nebula'
GRAFANA_PATH = 'grafana_app'
SITE_TITLE = 'Nebula'
# 前端版本
Nebula_Web_Version = '3.0.1'
# API版本
API_VERSION = '1.4.0'
Constructing = u'前方施工中,请自觉绕行...'
# swagger模板位置
Swagger_Assets_Path = opath.join(Base_Path, Nebula_Path, "middleware/swagger")
# web监听设置
WebUI_Address = '0.0.0.0'
# log配置
Logging_File = opath.join(
    "/data/logs/web", 'nebula.log') if opath.exists('/data/logs') else 'nebula.log'
Logging_Format = '%(asctime)s\t%(filename)s,line %(lineno)s\t%(levelname)s: %(message)s'
Logging_Datefmt = '%Y-%m-%d %H:%M'
Logging_MaxBytes = 100 * 1024 * 1024   # 100M
Logging_BackupCount = 5   # 5 copies
# frontend path
FRONTEND_BASE_PATH = opath.join(Base_Path, "..", "nebula_fe")
if not opath.exists(FRONTEND_BASE_PATH):
    FRONTEND_BASE_PATH = opath.join(Base_Path, Nebula_Path)
# tornado 配置
Login_Url = "/user#login"
Tornado_Setting = {
    "static_path": opath.join(FRONTEND_BASE_PATH, "statics"),
    "template_path": opath.join(FRONTEND_BASE_PATH, "templates"),
    "cookie_secret": '/zagx4zuSReKnMO9i1Qxrh08l6mNTkePqiaXBAmpke4=',
    "xsrf_cookies": False,
    "autoescape": None,
    "gzip": True,
    "debug": DEBUG,
    "autoreload": False,
    "login_url": Login_Url
}
# kerberos 配置
sso_service = "HTTP"
sso_realm = "THREATHUNTER.TEST"

# internal setting
Internal_Auth = {
    "sniffer": "1ac1a08630d68a2fdd0b719d5c07f915",
    "offline": "196ca0c6b74ad61597e3357261e80caf",
    "online": "40eb336d9af8c9400069270c01e78f76",
    "read_api": "7a7c4182f1bef7504a1d3d5eaa51a242",
    "profile": "feb2d59522d9794e065cf1bb0a6f53d0"
}

WebUI_Port = _config.get_int("webui_port", 9001)
Redis_Host = _config.get_string("redis_host", "redis")
Redis_Port = _config.get_int("redis_port", 6379)
Babel_Mode = _config.get_string("babel_server", "redis")
Metrics_Server = _config.get_string("metrics_server", "redis")
Rmq_Username = _config.get_string("rmq_username", "guest")
Rmq_Password = _config.get_string("rmq_password", "guest")
Rmq_Host = _config.get_string("rmq_host", "127.0.0.1")
Rmq_Port = _config.get_int("rmq_port", 5672)
Influxdb_Url = _config.get_string("influxdb_url", "http://127.0.0.1:8086/")
LogQuery_Path = _config.get_string("logquery_path", "./")
Log_Path = _config.get_string("log_path", "./")
Persist_Path = _config.get_string("persist_path", "./")
NoticeExport_Path = _config.get_string("noticeexport_path", "./")
StrategyExport_Path = _config.get_string("strategyexport_path", "./")
StrategyExport_Salt = _config.get_string("strategyexport_salt", "threathunter")
Expire_Days = _config.get_int("persist_expire_days", 3)
AeroSpike_Port = _config.get_int("aerospike_port", 3000)
AeroSpike_Address = _config.get_string("aerospike_address", "aerospike")
AeroSpike_Timeout = _config.get_int("aerospike_timeout", 2000)
AeroSpike_DB_Name = _config.get_string("aerospike_offline_db", "offline")
AeroSpike_DB_Expire = _config.get_int("aerospike_offline_expire", 1)
Notice_RPC_Template_Path = _config.get_string(
    "notice_rpc_template_path", "conf")
Internal_Hosts = _config.get_dict("internal_hosts", {"127.0.0.1"})
# mysql 默认配置
MySQL_Host = _config.get_string("mysql_host", "mysql")
MySQL_Port = _config.get_int("mysql_port", 3306)
MySQL_User = _config.get_string("mysql_user", "nebula")
MySQL_Passwd = _config.get_string("mysql_passwd", "threathunter")
Nebula_Default_DB = _config.get_string("nebula_default_db", "nebula_default")
Nebula_Data_DB = _config.get_string("nebula_data_db", "nebula_data")
Nebula_DB = _config.get_string("nebula_db", "nebula")
# sentry 配置
Sentry_Enable = _config.get_boolean("sentry_enable", False)
Sentry_Dsn_Web = _config.get_string(
    "sentry_dsn_web", "https://<key>:<secret>@sentry.io/<project>")
Sentry_Min_Level = _config.get_string("sentry_min_level", "error")
Server_Name = _config.get_string("server_name", "nebula_web")
Enable_Online = _config.get_boolean("nebula.online.slot.enable", True)

# 全局配置路径，如果路径不存在，则新建目录
for path in ['LogQuery_Path', 'Persist_Path', 'NoticeExport_Path', 'StrategyExport_Path']:
    if not opath.exists(globals()[path]):
        os.makedirs(globals()[path])

# 全局配置数据库地址，修改数据库连接串
db_connect_string = 'mysql://%s:%s@%s:%s/' % (
    MySQL_User, MySQL_Passwd, MySQL_Host, MySQL_Port)
DB_CONNECT_STRING = db_connect_string + '%s?charset=utf8' % Nebula_DB
DB_Default_CONNECT_STRING = db_connect_string + \
    '%s?charset=utf8' % Nebula_Default_DB
DB_Data_CONNECT_STRING = db_connect_string + '%s?charset=utf8' % Nebula_Data_DB

