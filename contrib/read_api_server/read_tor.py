#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import json
import click
import subprocess
from os import path as opath

from tornado.web import Application
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.httpclient import AsyncHTTPClient

from contrib.read_api_server import settings
from contrib.read_api_server.cache_property import set_notice_cache
from contrib.read_api_server.read_api import Notice_List_Handler, Notice_Cache_Handler, GiveMeAcceptHandler, \
    GiveMeReviewHandler, GiveMeRejectHandler, GiveMeNothingHandler, GiveMeErrorHandler


logger = logging.getLogger("read_tor.notice")


def pull_master_notice_cache_callback():
    api_url = "http://{0}:{1}/platform/notices?limit=3000&auth={2}".format(
        settings.WebUI_Address, settings.WebUI_Port, settings.Auth_Code)

    http_client = AsyncHTTPClient()
    http_client.fetch(api_url, master_notice_cache_async_callback)


def master_notice_cache_async_callback(response):
    if response.error:
        logger.info("Error: {}".format(response.error))
    else:
        notices = json.loads(response.body)

        if not notices:
            logger.info("no cache get")

        notices_dict = dict()
        for notice in notices["values"]["items"]:
            key = notice.get("key")
            if notices_dict.has_key(key):
                notices_dict[key].append(notice)
            else:
                notices_dict[key] = [notice, ]

        set_notice_cache(notices_dict)


def pull_client_notice_cache_callback():
    api_url = "http://{0}:{1}/notices".format(
        settings.ReadApi_Master_Address, settings.ReadApi_Master_Port)

    http_client = AsyncHTTPClient()
    http_client.fetch(api_url, client_notice_cache_async_callback)


def client_notice_cache_async_callback(response):
    if response.error:
        logger.info("Error: {}".format(response.error))
    else:
        notices = json.loads(response.body)

        if not notices:
            logger.info("no cache get")
            notices = dict()

        set_notice_cache(notices)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    logger.info('check risk server start...')


@cli.command()
@click.option('-p', '--port', default=settings.ReadApi_Master_Port, help="master port")
@click.pass_context
def master(ctx, port):
    application = Application([
        (r"/notices", Notice_List_Handler),
        (r"/checkRisk", Notice_Cache_Handler),
        (r"/checkRiskTest", Notice_Cache_Handler),
        (r"/checkRiskTest/GiveMeAccept", GiveMeAcceptHandler),
        (r"/checkRiskTest/GiveMeReview", GiveMeReviewHandler),
        (r"/checkRiskTest/GiveMeReject", GiveMeRejectHandler),
        (r"/checkRiskTest/GiveMeNothing", GiveMeNothingHandler),
        (r"/checkRiskTest/GiveMeError", GiveMeErrorHandler),
    ])
    application.listen(port, address=settings.ReadApi_Master_Address)
    io_loop = IOLoop.current()

    # 注册定时拉取notice cache 回调函数
    pull_master_notice_cache_callback()
    pc = PeriodicCallback(pull_master_notice_cache_callback, 30000)
    pc.start()

    # 启动client进程,提供check risk外部API
    for i in range(0, settings.ReadApi_subprocess_number):
        client_port = settings.ReadApi_Client_Port + i
        path = opath.join(opath.dirname(__file__), "read_tor")
        out = subprocess.call(
            "{0} -m {1} client --port {2} &".format(settings.Nebula_Python_Path, path, client_port), shell=True)
        logger.info("subprocess status: {}".format(out))

    # server start..
    io_loop.start()


@cli.command()
@click.option('-p', '--port', default=settings.ReadApi_Client_Port, help="client port")
@click.pass_context
def client(ctx, port):
    application = Application([
        (r"/checkRisk", Notice_Cache_Handler),
        (r"/checkRiskTest", Notice_Cache_Handler),
        (r"/checkRiskTest/GiveMeAccept", GiveMeAcceptHandler),
        (r"/checkRiskTest/GiveMeReview", GiveMeReviewHandler),
        (r"/checkRiskTest/GiveMeReject", GiveMeRejectHandler),
        (r"/checkRiskTest/GiveMeNothing", GiveMeNothingHandler),
        (r"/checkRiskTest/GiveMeError", GiveMeErrorHandler),
    ])
    application.listen(port, address=settings.ReadApi_Master_Address)
    io_loop = IOLoop.current()

    # 注册定时拉取notice cache 回调函数
    pull_client_notice_cache_callback()
    pc = PeriodicCallback(pull_client_notice_cache_callback, 10000)
    pc.start()

    # server start..
    io_loop.start()


if __name__ == "__main__":
    cli()
