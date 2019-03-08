#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import traceback, time, smtplib
from email.mime.text import MIMEText

import gevent
from tornado import template
import redis
import collections
import sys

from . import babel
from ..dao.DBDataCache import dbcontext
from ..dao.notice_dao import NoticeDao
from ..dao.strategy_dao import StrategyCustDao
from ..dao.config_helper import get_config

from threathunter_common.metrics.metricsrecorder import MetricsRecorder
from threathunter_common.util import millis_now
from nebula_meta.model.notice import Notice

def convert_ts(ts):
    seconds = time.localtime(ts/1000.0)
    return time.strftime('%Y-%m-%d %H:%M:%S', seconds)


def send_mail(body):
    sender = get_config("alerting.send_email", '')
    receiver = get_config("alerting.to_emails", '')
    subject = get_config("alerting.email_topic", 'nebula alarms')
    smtpserver = get_config("alerting.smtp_server", '')
    username = get_config("alerting.smtp_account", '')
    password = get_config("alerting.smtp_password", '')
    ssl = get_config("alerting.smtp_ssl", '0')
    port = get_config("alerting.smtp_port", "0")
    port = int(port)
    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    receiver = receiver.split(",")
    print "!!!sending", smtpserver, port, username, password, sender, receiver, ssl, body
    try:
        if ssl.lower() in {"yes", "y", "1", "true"}:
            smtp = smtplib.SMTP_SSL(host=smtpserver, port=port)
        else:
            smtp = smtplib.SMTP(host=smtpserver, port=port)
        smtp.login(username, password)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()
    except Exception as err:
        print "sent smtp error", err
        import sys;sys.stdout.flush()

    print "!!! sent mail for {} bytes".format(len(body))


type_mapping = {
    "IP": "ip",
    "USER": "user",
    "DEVICEID": "did",
}

def get_body_data(notices):
    if not notices:
        return list()

    result = dict()
    strategies = dbcontext.nebula_strategies
    strategy_dict = {s.name: s for s in strategies}
    for n in notices:
        if n.strategy_name not in result:
            strategy = strategy_dict.get(n.strategy_name)
            if not strategy:
                continue

            result[n.strategy_name] = {
                "name": n.strategy_name,
                "desc": strategy.remark,
                "action_desc": n.remark,
                "notices": list(),
                "keys": set(),
                "test": n.test,
                "risk_score": n.risk_score
            }

        sub_notice_list = result[n.strategy_name]["notices"]
        sub_keys = result[n.strategy_name]["keys"]
        if n.key in sub_keys:
            continue

        sub_notice_list.append(n)
        sub_keys.add(n.key)

    result = result.values()
    test_result = filter(lambda x: x["test"], result)
    prod_result = filter(lambda x: not x["test"], result)

    test_result.sort(key=lambda x: x["risk_score"], reverse=True)
    prod_result.sort(key=lambda x: x["risk_score"], reverse=True)
    result = prod_result + test_result

    return result


def render_mail(template_path, template_name, **kargs):
    loader = template.Loader(template_path)
    t = loader.load(template_name)
    kargs["convert_ts"] = convert_ts
    kargs["mapping_type"] = lambda t: type_mapping.get(t, "ip")
    result = t.generate(**kargs)
    send_mail(result)


def check_white_list(ip):
    white_list = get_config("notices.whitelist", "")
    white_list = white_list.split(",")
    white_list = set(white_list)
    return ip in white_list


ops = {
    '>':  '大于"{}"',
    '<': '小于"{}"',
    '>=': '大于等于"{}"',
    '<=': '小于等于"{}"',
    '==': '等于"{}"',
    '!=': '不等于"{}"',
    'between': '介于"{}"',
    'in': '属于"{}"',
    '!in': '不属于"{}"',
    'contain': '包含"{}"',
    '!contain': '不包含"{}"',
    'startwith': '以"{}"开始',
    '!startwith': '不以"{}"开始',
    'endwith': '以"{}"结束',
    '!endwith': '不以"{}"结束',
    'regex': '包含正则"{}"',
    '!regex': '不包含正则"{}"',
    '=': '等于变量"{}"',
}


def get_op_tip(left, op, right):
    return "{}".format(left) + op.format(right)


def get_tip(name, values):
    strategies = dbcontext.nebula_strategies
    strategy_dict = {s.name: s for s in strategies}
    s = strategy_dict.get(name)
    tip = ""
    if s:
        for tid, t in enumerate(s.terms):
            left = t.left
            if left.type == "event":
                tip += '当{}等于"{}"发生时:'.format("{}.{}".format(left.event[-1], left.field), values.get(left.field, ""))
            if left.type == "func":
                if left.subtype == "count":
                    counter_name = "_strategy_{}_{}_counter_{}".format(s.version, s.name, tid)
                    v = values.get(counter_name)
                    if v:
                        source_event = left.source_event[-1]
                        interval = left.interval
                        conditions = []
                        for c in left.condition:
                            left = c["left"]
                            op = c["op"]
                            right = c["right"]
                            conditions.append(get_op_tip(left, ops[op], right))
                        tip += '{}s内，{}{}的总数等于{};'.format(interval, source_event, conditions and '在满足{}的情况下'.format(",".join(conditions)) or "", v)
                elif left.subtype == "getvariable":
                    counter = dbcontext.nebula_ui_variables_dict.get(tuple(left.variable))
                    counter_name = counter.name
                    v = values.get(counter_name)
                    if v:
                        tip += '{}等于"{}";'.format(counter_name, v)
                else:
                    continue
    tip += "满足策略{}".format(name)
#    print tip
    return tip


metrics_recorder_stats = MetricsRecorder("web.notices.stats", expire=86400*60, interval=300, type="sum", db="default")


def add_metrics(notice):
    metrics_recorder_stats.record(1, {"test": 1 if notice.test else 0})


def process_notify(event):
    if not event:
        return

    try:
        data = {
            "timestamp": event.timestamp,
            "key": event.key,
            "scene_name": event.property_values["sceneName"],
            "checkpoints": event.property_values["checkpoints"],
            "check_type": event.property_values["checkType"],
            "strategy_name": event.property_values["strategyName"],
            "decision": event.property_values["decision"],
            "risk_score": event.property_values["riskScore"],
            "expire": event.property_values["expire"],
            "remark": event.property_values["remark"],
            "variable_values": event.property_values["variableValues"],
            "test": event.property_values["test"],
            "geo_province": event.property_values.get("geo_province", ""),
            "geo_city": event.property_values.get("geo_city", ""),
            "tip": get_tip(event.property_values["strategyName"], event.property_values.get("triggerValues", dict())),
            "uri_stem": event.property_values.get("triggerValues", {}).get("propertyValues", {}).get("page", "")
        }
        if not data.get("geo_province", ""):
            data["geo_province"] = "unknown"
        if not data.get("geo_city", ""):
            data["geo_city"] = "unknown"
        if not data.get("uri_stem", ""):
            data["uri_stem"] = "unknown"
        notice = Notice(**data)
        NoticeDao().add_notice(notice)

        # 报警数据记录metrics
        if notice.decision != 'accept':
            add_metrics(notice)

        # @todo 提出来放到db
        redis_enable = str(get_config("notice.redis.enable", 'false'))
        if not redis_enable.lower() == "true":
            return

        redis_host = str(get_config("notice.redis.host", 'localhost'))
        redis_port = int(get_config("notice.redis.port", '6379'))
        if notice.strategy_name in StrategyCustDao().get_cached_online_strategies() and notice.decision == 'reject':
            key = notice.key
            ttl = (notice.expire - millis_now()) / 1000
            r = redis.Redis(host=redis_host, port=redis_port)
            r.setex(key, 1, ttl)
    except:
        traceback.print_exc()


class NoticeRPCServer(object):

    def __init__(self, template_path):
        self.server = babel.get_notice_notify_server()
        self.template_path = template_path
        self.bg_task = None

    def start(self):
        self.server.start(func=process_notify)
        self.bg_task = gevent.spawn(self.send_alarm_task) # @todo

    def send_alarm_task(self):
        while True:
            interval = 3600# default value
            try:
                # @todo out 2 db
                enable = get_config("alerting.status", "0")
                if enable.lower() not in {"true", "yes", "y", "1"}:
                    continue

                template_file = "mail.html"
                interval = int(get_config("alerting.delivery_interval", '60')) * 60
                endtime = millis_now()
                fromtime = endtime - interval * 1000
                base_url = get_config("alerting.nebula_address", "http://localhost:9001")

                notices = NoticeDao().list_notices(fromtime=fromtime, endtime=endtime)
                is_test_needed = get_config("alerting.need_test", '1')
                if is_test_needed.lower() not in {"true", "yes", "y", "1"}:
                    notices = filter(lambda n: not n.test, notices)
                print "sending notices %s" % notices, fromtime, endtime
                if notices:
                    data = get_body_data(notices)
                    render_mail(self.template_path, template_file, data=data, fromtime=fromtime, endtime=endtime,
                                base_url=base_url)

            except Exception as err:
                print >> sys.stderr, "sending mail error", err
                pass
            finally:
                gevent.sleep(interval) # @todo


if __name__ == "__main__":
    from threathunter_common.util import millis_now, run_in_thread
    import traceback, time, smtplib
    from email.mime.text import MIMEText
    sender = "threathuntertest@sina.com"
    subject = "luwen"
    receiver = "luwen@threathunter.cn"
    smtpserver = "smtp.sina.com"
    username = "threathuntertest"
    password = "bigtech"

    ssl = "false"
    port = 25
    msg = MIMEText("test", 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    try:
        if ssl == "true":
            smtp = smtplib.SMTP_SSL(host=smtpserver, port=port)
        else:
            smtp = smtplib.SMTP(host=smtpserver, port=port)
        print 1112
        print 1114
        smtp.login(username, password)
        print 1115
        smtp.sendmail(sender, receiver, msg.as_string())
        print 1115
        smtp.quit()
    except Exception as err:
        print "sent smtp error", err
        import sys;sys.stdout.flush()

