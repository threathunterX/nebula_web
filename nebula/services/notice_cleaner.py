#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from tornado.ioloop import PeriodicCallback

from threathunter_common.util import millis_now
from nebula.dao.notice_dao import NoticeDao


logger = logging.getLogger("nebula.notice.cleaner")

Notice_Clean_Interval = 60 * 60 * 1000  # 每个小时
Last_Avail_Notice_Time = millis_now()- (10 * 86400 * 1000) # 删除10天前的黑名单

class NoticeCleaner(object):
    def __init__(self):
        self._task = None

    def _run(self):
        try:
            dao = NoticeDao()
            dao.purge_notices(Last_Avail_Notice_Time)
        except Exception as error:
            logger.error("fail to purge notices")

    def start(self):
        self._task = PeriodicCallback(self._run, Notice_Clean_Interval)
        self._task.start()

    def stop(self):
        if self._task:
            self._task.stop()

    def close(self):
        self.stop()

    def __del__(self):
        self.stop()

