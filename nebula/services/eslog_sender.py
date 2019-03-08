#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time

import elasticsearch
import gevent

from . import babel
from ..dao.notice_dao import NoticeDao
from ..dao.config_helper import get_config

from threathunter_common.util import millis_now

def get_flat_map_from_event(event):
    result = event.property_values or dict()
    result["app"] = event.app
    result["name"] = event.name
    result["key"] = event.key
    result["timestamp"] = event.timestamp
    return result

last_update = 0
blacklist = list()

def get_blacklist():
    global last_update
    global blacklist
    current = millis_now()
    if current - last_update < 10 * 1000:
        return blacklist

    endtime = millis_now()
    fromtime = endtime - 360000 * 1000
    notices = NoticeDao().list_notices(fromtime=fromtime, endtime=endtime)
    notices = filter(lambda n: not n.test, notices)
    notices.sort(cmp=lambda x, y: cmp(x.timestamp, y.timestamp), reverse=True)
    notices = filter(lambda n: n.expire > current, notices)
    ip_set = {n.key for n in notices}
    blacklist = ip_set
    last_update = current

def filter_httplog(ev):
    ev.property_values["c_ip"] not in get_blacklist()

class ESLogSender(object):
    def __init__(self):
        self.es = None
        self.es_last_create = 0
        self.queue = gevent.queue.Queue(maxsize=1000) # @todo
        pass

    def get_es(self):
        es_enabled = get_config("nebula.eslog.enabled", "false")
        if es_enabled != "true":
            return

        current = millis_now()
        if current - self.es_last_create < 10000:
            return self.es

        es_host = get_config("nebula.eslog.host", "")
        es_port = int(get_config("nebula.eslog.port", "9200"))
        if not es_host:
            self.es = None
        else:
            self.es = elasticsearch.Elasticsearch([{"host": es_host, "port": es_port}])
        self.es_last_create = current
        return self.es

    def add_event(self, event):
        try:
            self.queue.put_nowait(event)
        except Exception as ignore:
            pass

    def send_events(self):
        while True:
            try:
                es_enabled = get_config("nebula.eslog.enabled", "false")
                if es_enabled != "true":
                    # es is not enabled, sleep for a short while
                    gevent.sleep(0.5) # @todo
                    continue

                events = {}
                while True:
                    count = 0
                    try:
                        ev = self.queue.get_nowait()
                        m = get_flat_map_from_event(ev)
                        name = ev.name
                        events.setdefault(name, []).append(m) # name undefine
                        count += 1
                        if count > 100: break
                    except Empty: # @todo undefine
                        # no events now, sleep for a short while
                        gevent.sleep(0.5)
                        break

                es = self.get_es()
                if es:
                    for name, data in events.iteritems():
                        if name.startswith("httplog"):
                            name = "{}-{}".format(name, time.strftime("%Y.%m.%d", time.localtime()))
                        else:
                            name = "{}-{}".format(name, time.strftime("%Y.%m", time.localtime()))
                        data = [
                            {
                            "_index": name,
                            "_type": "logs",
                            "_source": _
                            } for _ in data
                        ]
                        elasticsearch.helpers.bulk(es, data)
            except Exception as ignore:
                pass

class ESLogSenderServer(object):

    def __init__(self):
        self.server = babel.get_misclog_notify_server()
        self.http_server = babel.get_httplog_notify_server()
        self.notice_server = babel.get_noticelog_notify_server()
        self.event_proxy = None
        self.bg_task = None

    def start(self):
        self.event_proxy = ESLogSender()
        self.server.start(self.process)
        self.http_server.start(self.http_process)
        self.notice_server.start(self.process)
        self.bg_task = gevent.spawn(self.send_logs) # @todo

    def send_logs(self):
        self.event_proxy.send_events()

    def process(self, event):
        if self.event_proxy:
            self.event_proxy.add_event(event)

    def http_process(self, event):
        if self.event_proxy:
            if filter_httplog(event):
                return
            self.event_proxy.add_event(event)

if __name__ == '__main__':
    get_blacklist()
