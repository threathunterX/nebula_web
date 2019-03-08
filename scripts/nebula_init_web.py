#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import json
import click
import requests
from os import path as opath

prefix = '*********************************************'

CONFIG_DEFAULT_URL = "http://127.0.0.1:9001/default/config?auth=7a7c4182f1bef7504a1d3d5eaa51a242"
CONFIG_CUSTOM_URL = "http://127.0.0.1:9001/platform/config?auth=7a7c4182f1bef7504a1d3d5eaa51a242"

EVENTMETA_DEFAULT_URL = "http://127.0.0.1:9001/default/events?auth=7a7c4182f1bef7504a1d3d5eaa51a242"
EVENTMETA_CUSTOM_URL = "http://127.0.0.1:9001/platform/events?auth=7a7c4182f1bef7504a1d3d5eaa51a242"

EVENTMODEL_DEFAULT_URL = "http://127.0.0.1:9001/default/event_models?auth=7a7c4182f1bef7504a1d3d5eaa51a242"
EVENTMODEL_CUSTOM_URL = "http://127.0.0.1:9001/platform/event_models?auth=7a7c4182f1bef7504a1d3d5eaa51a242"

VARIABLEMETA_DEFAULT_URL = "http://127.0.0.1:9001/default/variables?auth=7a7c4182f1bef7504a1d3d5eaa51a242"
VARIABLEMETA_CUSTOM_URL = "http://127.0.0.1:9001/platform/variables?auth=7a7c4182f1bef7504a1d3d5eaa51a242"

VARIABLEMODEL_DEFAULT_URL = "http://127.0.0.1:9001/default/variable_models?auth=7a7c4182f1bef7504a1d3d5eaa51a242"
VARIABLEMODEL_CUSTOM_URL = "http://127.0.0.1:9001/platform/variable_models?auth=7a7c4182f1bef7504a1d3d5eaa51a242"

LOGIN_URL = "http://127.0.0.1:9001/auth/login"
STRATEGY_URL = "http://127.0.0.1:9001/nebula/strategies"


def parser_json_file(file_path):
    if opath.exists(file_path):
        with open(file_path) as json_file:
            data = json.load(json_file)
            return json.dumps(data)
    else:
        return None


def send_web_request(url, data):
    r = requests.post(url, data=data)
    return r.json()


def add_config(path, env):
    # 添加默认配置
    default_path = opath.join(path, 'default', 'config_default.json')
    default_config = parser_json_file(default_path)
    if default_config:
        r = send_web_request(CONFIG_DEFAULT_URL, default_config)
        if r['status'] == 0:
            print (prefix + '\n' + 'add default config succeed')
        else:
            print (prefix + '\n' + 'add default config failed')
    else:
        print (prefix + '\n' + 'default config not exist')

    # 添加env custom配置
    if env != 'default':
        custom_path = opath.join(path, env, 'config_cust.json')
        custom_config = parser_json_file(custom_path)
        if custom_config:
            r = send_web_request(CONFIG_CUSTOM_URL, custom_config)
            if r['status'] == 0:
                print (prefix + '\n' + 'add %s config succeed' % env)
            else:
                print (prefix + '\n' + 'add %s config failed' % env)
        else:
            print (prefix + '\n' + '%s config not exist' % env)


def add_eventmodel(path, env):
    # 添加默认event model
    default_path = opath.join(path, 'default', 'event_model_default.json')
    default_eventmodel = parser_json_file(default_path)
    if default_eventmodel:
        r = send_web_request(EVENTMODEL_DEFAULT_URL, default_eventmodel)
        if r['status'] == 0:
            print (prefix + '\n' + 'add default event model succeed')
        else:
            print (prefix + '\n' + 'add default event model failed')
    else:
        print (prefix + '\n' + 'default event model not exist')

    # 添加env custom 事件
    if env != 'default':
        custom_path = opath.join(path, env, 'event_model_cust.json')
        custom_eventmodel = parser_json_file(custom_path)
        if custom_eventmodel:
            r = send_web_request(EVENTMODEL_CUSTOM_URL, custom_eventmodel)
            if r['status'] == 0:
                print (prefix + '\n' + 'add %s event model succeed' % env)
            else:
                print (prefix + '\n' + 'add %s event model failed' % env)
        else:
            print (prefix + '\n' + '%s event model not exist' % env)


def add_variablemodel(path, env):
    models = ['common_variable', 'realtime_variable', 'slot_variable', 'profile_variable']

    # 添加默认variable model
    for model in models:
        default_path = opath.join(path, 'default', '{}_default.json'.format(model))
        default_variablemodel = parser_json_file(default_path)
        if default_variablemodel:
            r = send_web_request(VARIABLEMODEL_DEFAULT_URL, default_variablemodel)
            if r['status'] == 0:
                pass
            else:
                print (prefix + '\n' + 'add default variable model failed')
                return -1;
        else:
            print (prefix + '\n' + 'default variable model not exist')

    print (prefix + '\n' + 'add default variable model succeed')

    # 添加env custom 变量
    if env == 'default':
        return 0

    for model in models:
        custom_path = opath.join(path, env, '{}_cust.json'.format(model))
        custom_variablemodel = parser_json_file(custom_path)
        if custom_variablemodel:
            r = send_web_request(VARIABLEMODEL_CUSTOM_URL, custom_variablemodel)
            if r['status'] == 0:
                pass
            else:
                print (prefix + '\n' + 'add %s variable model failed' % env)
                return -1;
        else:
            print (prefix + '\n' + '%s variable model not exist' % env)
    print (prefix + '\n' + 'add %s variable model succeed' % env)
    return 0


def add_strategy(path, env, test_pwd):
    user = json.dumps({"username": "threathunter_test", "password": test_pwd})
    login = requests.post(LOGIN_URL, data=user)
    cookies = login.cookies

    # 添加默认strategy
    default_path = opath.join(path, 'default', 'strategy_default.json')
    default_strategy = parser_json_file(default_path)
    if default_strategy:
        r = requests.post(STRATEGY_URL,
                          data=default_strategy, cookies=cookies)
        res = r.json()
        if res['status'] == 200:
            print (prefix + '\n' + 'add default strategy succeed')
        else:
            print (prefix + '\n' + 'add default strategy failed')
            return -1
    else:
        print (prefix + '\n' + 'default strategy not exist')

    # 添加env custom 策略
    if env != 'default':
        custom_path = opath.join(path, env, 'strategy_cust.json')
        custom_strategy = parser_json_file(custom_path)
        if custom_strategy:
            r = requests.post(STRATEGY_URL,
                              data=custom_strategy, cookies=cookies)
            res = r.json()
            if res['status'] == 200:
                print (prefix + '\n' + 'add %s strategy succeed' % env)
            else:
                print (prefix + '\n' + 'add %s strategy failed' % env)
                return -1
        else:
            print (prefix + '\n' + '%s strategy not exist' % env)
    return 0


@click.command()
@click.option('--path', default='nebula_resources/mysql', help='nebula resources mysql path')
@click.option('--env', default='default', help='nebula web deploy env')
@click.option('--test_pwd', default='threathuntertest', help='threathunter_test password')
def cli(path, env, test_pwd):
    # 添加nebula web config
    time.sleep(3)
    add_config(path, env)
    time.sleep(1)

    add_eventmodel(path, env)
    time.sleep(1)
    add_variablemodel(path, env)
    time.sleep(1)

    # 添加nebula web strategy
    for num in range(0, 2):
        if add_strategy(path, env, test_pwd) >= 0:
            time.sleep(1)
            break
    time.sleep(1)


if __name__ == '__main__':
    cli()

