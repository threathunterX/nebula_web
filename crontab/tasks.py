#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:sdot
# datetime:2018/12/26 16:38
# software: PyCharm
import time
import logging
import psutil

# from apscheduler.schedulers.background import BackgroundScheduler

from easy_redis import EasyRedis
logger = logging.getLogger('crontab.tasks')

class SystemStaus():
    """
    每一分钟检测一次，取的话取最新的五次数据
    {"space":30,"cpu":[10,5,8,2,6,0],"memory":[4,1,2,3,4,3]}
    """

    def __init__(self):
        self.redis = EasyRedis.getinstance()
        self.tag = "monitor.systemStats.{}"

    def get_cpu_percent(self):
        cpu_percent_list = psutil.cpu_percent(interval=1, percpu=True)
        cpu_per=0
        for cpu_percen in cpu_percent_list:
            cpu_per += cpu_percen
        return int(cpu_per / len(cpu_percent_list))

    def get_mermory_percent(self):
        return int(psutil.virtual_memory().percent)

    def get_space_percent(self):
        return int(psutil.disk_usage('/').percent)

    def init_tag(self):
        tag_cpu = self.tag.format("cpu")
        tag_memory = self.tag.format("memory")
        tag_space = self.tag.format("space")
        for i in range(5):
            # 如果是第一次启动，则将当前数 据注入进去
            self.redis.list_rpush(tag_cpu, self.get_cpu_percent())
            self.redis.list_rpush(tag_memory, self.get_mermory_percent())
            self.redis.list_rpush(tag_space, self.get_space_percent())

    def start_record(self):
        '''
        每隔一分钟更新一次数据
        :return:
        '''
        logging.debug( "start_record ....... {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        tag_cpu = self.tag.format("cpu")
        tag_memory = self.tag.format("memory")
        tag_space = self.tag.format("space")
        tag_list = [tag_cpu, tag_memory, tag_space]
        if self.redis.exists(tag_cpu):
            logging.debug( "exists start_record ....... {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            self.redis.list_rpush(tag_cpu, self.get_cpu_percent())
            self.redis.list_rpush(tag_memory, self.get_mermory_percent())
            self.redis.list_rpush(tag_space, self.get_space_percent())
            for tag in tag_list:
                while self.redis.list_llen(tag) > 5:
                    self.redis.list_lpop(tag)
        else:
            logging.debug( "init start_record ....... {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
            self.init_tag()


    def get_system_status(self):
        """
        get system status, if one status is error should check this moudle and redis status
        :return: {"space": 0, "cpu": [0, 0, 0, 0, 0], "memory": [0, 0, 0, 0, 0]}
        """
        tag_cpu = self.tag.format("cpu")
        tag_memory = self.tag.format("memory")
        tag_space = self.tag.format("space")
        cpus = self.redis.list_lrange(tag_cpu, 0, 5)
        memorys = self.redis.list_lrange(tag_memory, 0, 5)
        space = self.redis.list_lrange(tag_space, 4, 5)[0]
        if cpus and memorys and space:
            return {"space": space, "cpu": cpus, "memory": memorys}
        else:
            return {"space": 0, "cpu": [0, 0, 0, 0, 0], "memory": [0, 0, 0, 0, 0]}


system_status = SystemStaus()
scheduler_tasks = [system_status.start_record]

if __name__ == '__main__':
    system_status.get_cpu_percent()
    # scheduler = BackgroundScheduler()
    # 添加调度任务
    # 调度方法为 timedTask，触发器选择 interval(间隔性)，间隔时长为 60 秒
    # scheduler.add_job(scheduler_tasks[0], 'interval', seconds=60)
    # # 启动调度任务
    # scheduler.start()
    # while True:
    #     system_status.get_cpu_status()
    #     print time.time()
    #     time.sleep(3)
# cpu = SystemStaus.get_cpu_percent()
# memory = SystemStaus.get_mermory_percent()
# space = SystemStaus.get_space_percent()
# print cpu, memory, space
# crontab = SystemStaus()
# print crontab.start_record()
