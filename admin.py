#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from logging import Formatter

# from nebula.views.nebula_strategy import NebulaStrategy
# from nebula.views.nebula_strategy import Supervisor
from nebula.views import nebula_strategy
from nebula.views.supervisor import Supervisor
import tornado.web
import tornado.httpserver
import tornado.options
# from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
import click
from tornado import ioloop

import settings
from common import utils
from nebula.dao.user_dao import authenticated, init_session_jar

from tornado_profile_gen import application_api_wrapper
from crontab.tasks import scheduler_tasks

# change to rotate file handler
rotate_file_handler = RotatingFileHandler(settings.Logging_File, mode='a', maxBytes=settings.Logging_MaxBytes,
                                          backupCount=settings.Logging_BackupCount)
fmt = Formatter(settings.Logging_Format, settings.Logging_Datefmt)
rotate_file_handler.setFormatter(fmt)
logging.root.addHandler(rotate_file_handler)
level = logging.DEBUG if settings.DEBUG else logging.WARN
if level is not None:
    logging.root.setLevel(level)

# 判断是否开启sentry
if settings.Sentry_Enable:
    from raven import Client
    from raven.handlers.logging import SentryHandler
    from raven.conf import setup_logging

    client = Client(settings.Sentry_Dsn_Web, name=settings.Server_Name)
    handler = SentryHandler(client)
    if settings.Sentry_Min_Level.lower() == 'debug':
        handler.level = logging.DEBUG
    elif settings.Sentry_Min_Level.lower() == 'info':
        handler.level = logging.INFO
    else:
        handler.level = logging.ERROR
    setup_logging(handler)

logger = logging.getLogger('nebula.cli.admin')

# metrics 初始化配置
metrics_dict = {
    "app": "nebula_web",
    "redis": {
        "type": "redis",
        "host": settings.Redis_Host,
        "port": settings.Redis_Port
    },
    "influxdb": {
        "type": "influxdb",
        "url": settings.Influxdb_Url,
        "username": "test",
        "password": "test"
    },
    "server": settings.Metrics_Server
}


def constructing():
    """
    click 未完成功能说明
    """
    click.echo('')
    click.echo(settings.Constructing)
    click.echo('')


@click.group(invoke_without_command=True)
@click.version_option(settings.Nebula_Web_Version)
@click.pass_context
def cli(ctx, **kwargs):
    ctx.obj = utils.Storage()
    ctx.obj.update(kwargs)


@cli.command()
def activate():
    """
    检查运行环境
    激活virtualenv @todo
    """
    constructing()


@cli.command()
def initdb():
    """
    初始化数据库
    """
    from nebula.models import init_db
    init_db()
    from nebula.models.default import init_db as init_default_db
    init_default_db()
    from nebula.models.data import init_db as init_data_db
    init_data_db()


@cli.command()
def install():
    """
    安装nebula @todo
    """
    # @todo initdb
    constructing()


@cli.command()
def read_tor():
    """
    启动nebula只读api server @todo
    """
    constructing()


@cli.command()
def create_conf():
    '''
    根据settings配置成配置文件们, ex.metrics
    '''
    Nebula_Config = dict((k, v)
                         for k, v in settings.iteritems() if k[0].isupper())

    # 生成metrics配置
    metrics_conf = utils.render(settings.Metrics_Conf_Tem, Nebula_Config)
    with open(settings.Metrics_Conf_FN, 'w') as f:
        f.write(metrics_conf)

    click.echo(u'生成配置成功完成')
    click.echo('')


@cli.command()
@click.option('--debug/--no-debug', default=settings.DEBUG, help="debug mode")
@click.option('-p', '--port', default=settings.WebUI_Port, help="nebula port")
@click.pass_context
def webui(ctx, port, debug):
    if debug:
        logger.setLevel(logging.DEBUG)
    from nebula.views import (auth, general, influxdbproxy, config, metrics, notice,
                              system_perf, system_log,
                              nebula_config, strategy, checkrisk, strategy_default,
                              config_default, read_batch,
                              alarm, network, user, group, risk_incident, logparser,
                              permission, notice_export, notice_report,
                              strategy_export, upgrade, logquery, follow, event_model, event_model_default,
                              variable_model, variable_model_default)

    # 注册nebula_backend type2class
    from nebula_meta.model import variable_meta
    print variable_meta.VariableMeta.TYPE2Class
    # 初始化 redis 服务
    try:
        from threathunter_common.redis.redisctx import RedisCtx
    except ImportError:
        logger.error(u"from threathunter_common.redis.redisctx import RedisCtx 失败.")
        sys.exit(-1)
    RedisCtx.get_instance().host = settings.Redis_Host
    RedisCtx.get_instance().port = settings.Redis_Port
    logger.debug(u"成功初始化redis: {}".format(RedisCtx.get_instance()))

    # 初始化 metrics 服务
    try:
        from threathunter_common.metrics.metricsagent import MetricsAgent
    except ImportError:
        logger.error(
            u"from threathunter_common.metrics.metricsagent import MetricsAgent 失败")
        sys.exit(-1)

    MetricsAgent.get_instance().initialize_by_dict(metrics_dict)
    logger.debug(u"成功初始化metrics服务: {}.".format(MetricsAgent.get_instance().m))

    # 初始化 babel service
#    from nebula.services import babel
#    babel.set_mode(settings.Babel_Mode)
#    logger.debug(u"成功初始化 {} 模式的babel服务.".format(babel.mode))

    # 启动 performance metrics logger
    from nebula.services.metricspoller import HistoryMetricsPoller
    his_metrics = HistoryMetricsPoller()
    his_metrics.start()
    logger.debug(u"成功启动metrics性能日志服务.")

#    # 启动 定期清理notice任务
#    from nebula.services.notice_cleaner import NoticeCleaner
#    cleaner = NoticeCleaner()
#    cleaner.start()
#    logger.debug(u"成功启动定期清理notice服务.")

    # 初始化 dbcontext
    from nebula.dao.DBDataCache import dbcontext
    dbcontext.init()

#    # 启动 NoticeRPCServer
#    template_path = settings.Notice_RPC_Template_Path#os.path.join(os.path.dirname(__file__), "templates")
#    from nebula.services.notice_server import NoticeRPCServer
#    notice_server = NoticeRPCServer(template_path)
#    notice_server.start()

    # load取cache们
    from nebula.dao.cache import Cache_Init_Functions, init_caches

    # 策略权重的缓存
    from nebula.dao.strategy_dao import init_strategy_weigh
    Cache_Init_Functions.append(init_strategy_weigh)
    init_caches()

    # load session auth code
    init_session_jar()

    # 启动 ESLogSendServer
#    from nebula.services.eslog_sender import ESLogSenderServer
#    eslogserver = ESLogSenderServer()
#    eslogserver.start()

    urls = [
        # 通用模块
        (r"/", general.IndexHandler),
        (r"/project", general.ProjectHandler),
        (r"/user", general.LoginHandler),
        (r"/nebula/web/config", general.WebConfigHandler),
        (r"/auth/register", auth.RegisterHandler),

        # 权限模块
        (r"/auth/login", auth.LoginHandler),
        (r"/auth/logout", auth.LogoutHandler),
        (r"/auth/changepwd", auth.ChangePasswordHandler),
        (r"/auth/users", user.UserListHandler),
        (r"/auth/users/(.*)", user.UserQueryHandler),
        (r"/auth/groups", group.GroupListHandler),
        (r"/auth/groups/(.*)", group.GroupQueryHandler),
        (r"/auth/permissions", permission.PermissionListHandler),
        (r"/auth/permissions/(.*)/(.*)", permission.PermissionQueryHandler),
        (r"/auth/strategy_access", group.StrategyAccessHandler),
        (r"/auth/privileges", group.PrivilegesHandler),

        # 系统模块
        (r"/system/performance/digest", system_perf.SystemPerformanceHandler),
        (r'/system/log', system_log.LogInfoHandler),
        (r'/geo/all_city', general.AllCityHandler),
        (r'/geo/all_province', general.AllProvinceHandler),
        (r'/platform/geoinfo', general.GeoStatsHandler),

        # 默认的策略、配置、变量们
        (r"/default/variable_models/variable/(.*)/(.*)", variable_model_default.VariableModelQueryHandler),
        (r"/default/variable_models", variable_model_default.VariableModelListHandler),
        (r"/default/strategies", strategy_default.StrategyListHandler),
        (r"/default/strategies/strategy/(.*)/(.*)", strategy_default.StrategyQueryHandler),
        (r"/default/strategies/changestatus/", strategy_default.StrategyStatusHandler),
        (r"/default/config", config_default.ConfigListHandler),
        (r"/default/configproperties", config_default.ConfigPropertiesHandler),
        (r"/default/config/(.*)", config_default.ConfigHandler),
        (r"/default/event_models/event/(.*)/(.*)", event_model_default.EventQueryHandler),
        (r"/default/event_models", event_model_default.EventModelListHandler),

        # 定制配置接口
        (r"/platform/config", config.ConfigListHandler),
        (r"/platform/configproperties", config.ConfigPropertiesHandler),
        (r"/platform/config/(.*)", config.ConfigHandler),

        # 定制事件接口
        (r"/platform/event_models/event/(.*)/(.*)", event_model.EventQueryHandler),
        (r"/platform/event_models", event_model.EventListHandler),
        (r"/platform/event_models_beautify", event_model.EventModelBeautifyHandler),

        # 定制变量接口
        (r"/platform/variable_models/variable/(.*)/(.*)", variable_model.VariableModelQueryHandler),
        (r"/platform/variable_models", variable_model.VariableModelListHandler),
        (r"/platform/variable_models_beautify", variable_model.VariableModelBeautifyHandler),

        # 定制策略接口
        (r"/nebula/strategies", strategy.StrategyListHandler),
        (r"/nebula/strategies/strategy/(.*)/(.*)", strategy.StrategyQueryHandler),
        (r"/nebula/strategies/changestatus/", strategy.StrategyStatusHandler),
        (r"/nebula/strategies/delete", strategy.StrategyBatchDelHandler),
        (r"/nebula/strategy/import", strategy_export.StrategyImportHandler),
        (r"/nebula/strategy/export", strategy_export.StrategyExportHandler),
        (r"/nebula/strategy/export/(.*)", strategy_export.StrategyDownloadHandler),
        (r"/nebula/strategyweigh", strategy.StrategyWeighHandler),
        (r"/nebula/tags", strategy.TagsHandler),
        (r"/nebula/tag/(.*)", strategy.TagQueryHandler),

        (r"/nebula/glossary", nebula_config.VariableGlossaryHandler),
        (r"/nebula/events", nebula_config.NebulaUIEventsHandler),
        (r"/nebula/variables", nebula_config.NebulaUIVariablesHandler),

        (r"/nebula/online/events", nebula_config.NebulaOnlineEventsHandler),
        (r"/nebula/online/variables", nebula_config.NebulaOnlineVariablesHandler),

        # 策略定制脚本相关接口
        (r"/nebula/NebulaStrategy", nebula_strategy.NebulaStrategy),
        (r"/nebula/supervisor", Supervisor),
#        (r"/platform/variabledata/latest/(.*)", variable_value.VariableValueQueryHandler),
#        (r"/platform/variabledata/top/(.*)", variable_value.VariableValueTopHandler),
#        (r"/platform/variabledata/list/(.*)", variable_value.VariableValueListHandler),
#        (r"/platform/variabledata/keytop/(.*)", variable_value.VariableValueKeyTopHandler),

        # 风险事件相关
        (r"/platform/risk_incidents", risk_incident.IncidentListHandler),
#        (r"/platform/risks/statistics", risk_incident.RisksStatisticsHandler),
#        (r"/platform/risks/realtime", risk_incident.RisksRealtimeHandler),
        (r"/platform/risks/history", risk_incident.RisksHistoryHandler),
        (r"/platform/risks/(.*)", risk_incident.IncidentQueryHandler),
        (r"/platform/notices/export", notice_export.NoticeExportHandler),
        (r"/platform/notices/export/(.*)", tornado.web.StaticFileHandler, {"path": settings.NoticeExport_Path}),
        (r'/platform/stats/notice_report', notice_report.NoticeReportHandler),

        # 统计数据源通用查询接口
        #        (r'/platform/stats/online', data_bus.OnlineDataHandler),
        #        (r'/platform/stats/slot', data_bus.SlotDataHandler),
        #        (r'/platform/stats/slot_baseline', data_bus.SlotBaseLineDataHandler),
        #        (r'/platform/stats/offline', data_bus.OfflineDataHandler),
        #        (r'/platform/stats/offline_baseline', data_bus.OfflineBaseLineDataHandler),
        #        (r'/platform/stats/profile', data_bus.ProfileDataHandler),
        #        (r'/platform/stats/offline_serial', data_bus.OfflineSerialDataHandler),
        #        (r'/platform/stats/metrics', data_bus.MetricsDataHandler),
        #        (r'/platform/stats/notice', data_bus.NoticeDataHandler),
        #        (r'/platform/stats/risk_incident', data_bus.RiskIncidentDataHandler),
        #        (r'/platform/stats/geo', data_bus.GEODataHandler),
        #        (r'/platform/stats/threat_map', data_bus.ThreatMapDataHandler),
        #        (r'/platform/stats/clean_cache', data_bus.CleanCacheHandler),

        # 持久化事件查询数据
        (r'/platform/alarm', alarm.AlarmListHandler),
        (r'/platform/alarm/valid_count', alarm.ValidCountHandler),
        (r'/platform/alarm/statistics', alarm.StatisticsHandler),
        (r'/platform/network/statistics', network.NetworkStatisticsHandler),
#        (r'/platform/alarm/statistics_detail', alarm.StatisticsDetailHandler),
#        (r'/platform/behavior/strategy_statistic', incident_stat.StrategyStatHandler),
        (r'/platform/behavior/tag_statistics', alarm.TagStatHandler),
        
        #        (r'/platform/behavior/start_time',incident_stat.PersistBeginTimeHandler),
        #        (r'/platform/behavior/statistics', incident_stat.IncidentStatsHandler),
        #        (r'/platform/behavior/clicks_detail', incident_stat.ClickDetailHandler),
        #        (r'/platform/behavior/related_statistics', incident_stat.RelatedStatisticHandler),
        #        (r'/platform/behavior/continuous_related_statistic', incident_stat.ContinuousRelatedStatHandler),
        #        (r'/platform/behavior/continuous_top_related_statistic', incident_stat.ContinuousTopRelatedStatHandler),
        #        (r'/platform/behavior/scene_statistic', incident_stat.SceneStatHandler),

        #        (r"/platform/behavior/user_statistics", incident_stat.UserStatHandler),
        #        (r'/platform/behavior/page_statistics', incident_stat.RelatedPageStatisticHandler),
        #        (r'/platform/behavior/top/clicks_location', incident_stat.ClickLocation),

        #        (r'/platform/online/visit_stream', incident_stat.OnlineVisitStreamHandler),
        #        (r'/platform/behavior/visit_stream', incident_stat.OnlineVisitStreamHandler),
        #        (r'/platform/online/clicks_period', incident_stat.OnlineClicksPeriodHandler),
        #        (r'/platform/behavior/clicks_period', incident_stat.OnlineClicksPeriodHandler),
        #        (r'/platform/online/clicks', incident_stat.OnlineClickListHandler),
        #        (r'/platform/behavior/clicks', incident_stat.OnlineClickListHandler),


        # 日志解析
        (r"/platform/logparser", logparser.LogParserListHandler),
        # 日志查询
#        (r'/platform/logquery', incident_stat.LogQuery),
#        (r'/platform/logquery/(.*)', tornado.web.StaticFileHandler, {'path':settings.LogQuery_Path}),
#        (r"/platform/logquery_config", logquery.LogQueryConfigHandler),

        # metrics
        (r"/platform/metrics/(.*)", metrics.MetricsHandler),
        (r"/platform/batchmetrics/", metrics.BatchMetricsHandler),
        (r"/metricsproxy/.*", influxdbproxy.InfluxdbProxyHandler),

        # 黑名单相关
        (r"/platform/notices", notice.NoticeListHandler),
        (r"/platform/notices/trigger_event", notice.TriggerEventHandler),
        (r"/platform/noticestats", notice.NoticeStatsHandler),
        (r"/platform/bwlist", notice.NoticeBWListHandler),
        (r"/platform/noticetimestamps", notice.NoticeTimestampListHandler),
        (r"/checkRisk", checkrisk.CheckRiskHandler),
        (r"/checkRiskTest", checkrisk.CheckRiskHandler),
        (r"/checkRiskTest/GiveMeAccept", checkrisk.GiveMeAcceptHandler),
        (r"/checkRiskTest/GiveMeReview", checkrisk.GiveMeReviewHandler),
        (r"/checkRiskTest/GiveMeReject", checkrisk.GiveMeRejectHandler),
        (r"/checkRiskTest/GiveMeNothing", checkrisk.GiveMeNothingHandler),
        (r"/checkRiskTest/GiveMeError", checkrisk.GiveMeErrorHandler),

#        (r"/platform/monitor/riskyitems", monitor.RiskyItemsHandler),
#        (r"/platform/monitor/toptargets", monitor.TopTargetsHandler),
#        (r"/platform/monitor/topcities", monitor.TopCitiesHandler),

        (r"/platform/data/export/notice", notice.NoticeExportHandler),
        (r"/platform/batchCheckRisk/bwlist", read_batch.BatchBWListHandler),

        # 档案查询
#        (r"/platform/stats/profile", profile.ProfileHandler),
#        (r"/platform/stats/page_risk", profile.ProfilePageRiskHandler),
#        (r"/platform/stats/account_risk", profile.ProfileAccountRiskHandler),

        # 爬虫统计
        (r"/platform/follow_keyword", follow.FollowKeywordHandler),
        (r"/platform/follow_keyword/(.*)", follow.FollowKeywordAnotherHandler),

        # 更新nebula各组件
        (r"/platform/api/upgrade", upgrade.UpgradeHandler),

        # restful相关接口
        (r"/restful/", general.SwaggerUIHandler, {'assets_path': settings.Swagger_Assets_Path}),
        (r"/restful/(.*)", tornado.web.StaticFileHandler, {'path': settings.Swagger_Assets_Path}),
    ]

    # 注册 grafana url
    metrics = [
        (r'/metrics/(.*)', general.CustomizedFileHandler, {'path': settings.GRAFANA_PATH}),
        ]
    urls.extend(metrics)

    settings.Tornado_Setting["compress_response"] = True
    settings.Tornado_Setting["job_worker"] = 10

    utils.executor = ThreadPoolExecutor(max_workers=settings.Tornado_Setting.get('job_worker', 10))
    application = tornado.web.Application(urls, **settings.Tornado_Setting)

    # 注册 restful api url
    application_api_wrapper(application, authenticated, need_auth=False) #restful api not need auth

    # 注册nebula_strategy
    from nebula.views.nebula_config import context as nebula_context

    def load_event_schema():
        events = [_.get_dict() for _ in nebula_context.nebula_events]
        event_schema = dict()
        for e in events:
            properties = {p["name"]: p["type"] for p in e["properties"]}
            event_schema[e["name"]] = properties
        return event_schema

    def load_variable_schema():
        variables = [_.get_dict() for _ in nebula_context.nebula_variables]
        variable_schema = dict()
        for v in variables:
            variable_schema[v["name"]] = {}
        return variable_schema

    # """定时任务处理，此后需要定时任务都可往里面加，无需加机器上的crontab"""
    # scheduler = BackgroundScheduler()
    # # 添加调度任务
    # # 触发器选择 interval(间隔性)，间隔时长为 60 秒
    # scheduler.add_job(scheduler_tasks[0], 'interval', seconds=60)
    # # 启动调度任务
    # scheduler.start()

    # 定时60秒启动一次
    tornado.ioloop.PeriodicCallback(scheduler_tasks[0],callback_time=1000 * 60).start()

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    http_server.listen(str(port), settings.WebUI_Address)
    click.echo("Nebula Web Start, Port:%s" % port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    cli()
