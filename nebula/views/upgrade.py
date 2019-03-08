# -*- coding: utf-8 -*-

import subprocess, logging
import shlex
from os import path as opath

from tornado.gen import coroutine, Task, Return
from tornado.process import Subprocess
from tornado.web import RequestHandler

from threathunter_common.util import json_dumps

from nebula.dao.user_dao import authenticated

logger = logging.getLogger("web.api.upgrade")

Distinct_Upgrade_Module_Set = set()

class UpgradeHandler(RequestHandler):
    @coroutine
    @authenticated
    def get(self):
        try:
            upgrade_file_name = self.get_argument("upgrade_file_name")
            file_dir = self.get_argument("file_dir")
            if not file_dir:
                self.finish(json_dumps({"status": -1, "msg":u"未知上传文件路径"}))
                return
            if not upgrade_file_name:
                self.finish(json_dumps({"status": -1, "msg":u"未知上传文件名"}))
                return
            if upgrade_file_name in Distinct_Upgrade_Module_Set:
                self.finish(json_dumps({"status": -1, "msg":u"同名文件正在升级"}))
                return
            Distinct_Upgrade_Module_Set.add(upgrade_file_name)
            option = None
            if upgrade_file_name.find("web") != -1:
                option = "deploy_web"
            elif upgrade_file_name.find("profile") != -1:
                option = "deploy_profile"
            elif upgrade_file_name.find("fe") != -1:
                option = "deploy_fe"
            elif upgrade_file_name.find("online") != -1:
                option = "deploy_online"
            
            if not option:
                self.finish(json_dumps({"status": -1, "msg":u"未知更新模块类型, 文件名未包含web、profile、fe或者online"}))
                return
            filepath = opath.join(file_dir, upgrade_file_name)
            result, error = yield call_subprocess("nebula_ctrl.sh --%s %s" % (option, filepath))
            Distinct_Upgrade_Module_Set.remove(upgrade_file_name)
            logger.debug("result:", result, type(result), "error:", error, type(result))
            if error:
                self.finish(json_dumps({"status": -1, "msg":"Result: %s,\nError:%s" % (result, error)}))
                return
            self.finish(json_dumps({"status":0, "msg":result}))
        except Exception as err:
            Distinct_Upgrade_Module_Set.remove(upgrade_file_name)
            logger.error(err)
            self.finish(json_dumps({"status": -1, "msg": err}))
        
@coroutine
def call_subprocess(cmd, stdin_data=None, stdin_async=True):
    """call sub process async
        Args:
            cmd: str, commands
            stdin_data: str, data for standard in
            stdin_async: bool, whether use async for stdin
    """
    stdin = Subprocess.STREAM if stdin_async else subprocess.PIPE
    sub_process = Subprocess(shlex.split(cmd),
                             stdin=stdin,
                             stdout=Subprocess.STREAM,
                             stderr=Subprocess.STREAM,)

    if stdin_data:
        if stdin_async:
            yield Task(sub_process.stdin.write, stdin_data)
        else:
            sub_process.stdin.write(stdin_data)

    if stdin_async or stdin_data:
        sub_process.stdin.close()

    result, error = yield [Task(sub_process.stdout.read_until_close),
                           Task(sub_process.stderr.read_until_close),]

    raise Return((result, error))
