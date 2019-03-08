#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from threathunter_common.util import millis_now
from .config_dao import ConfigCustDao

configs = dict()
last_update = 0


def get_configitems():
    global configs
    global last_update

    current = millis_now()
    if current - last_update < 10 * 1000:
        return configs

    data = ConfigCustDao().list_all_config()
    new_configs = dict()
    for item in data:
        new_configs[item["key"]] = item["value"]

    configs = new_configs
    last_update = current
    return configs


def get_config(key, default=""):
    return get_configitems().get(key, default)


