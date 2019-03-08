#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:sdot
# datetime:2018/12/20 17:35
# software: PyCharm
'''

将一些常用的redis方法进行封装加上注释

'''

import settings
import redis


class EasyRedis():
    _instance = None

    def __init__(self):
        self.redis = redis.Redis(host=settings.Redis_Host, port=settings.Redis_Port, db="", password="")

    @classmethod
    def getinstance(cls):
        if not cls._instance:
            cls._instance = EasyRedis()
        return cls._instance

    def exists(self, key):
        return self.redis.exists(key)

    def pattern(self, pattern_key):
        return self.redis.keys(pattern=pattern_key)

    def expiers(self, key, t_time):
        "设置过期时间"
        return self.redis.expire(key, t_time)

    def delete(self, *keys):
        "允许删除多个key"
        return self.redis.delete(*keys)

    def list_llen(self, key):
        "取列表长度"
        return self.redis.llen(key)

    def list_lpush(self, key, *values):
        "添加元素到列表头部，可一次添加多个元素"
        return self.redis.lpush(key, *values)

    def list_rpush(self, key, *values):
        "添加元素到列表尾部，可一次添加多个元素"
        return self.redis.rpush(key, *values)

    def list_lrange(self, key, start_index, stop_index):
        "获取列表元素"
        return self.redis.lrange(key, start_index, stop_index)

    def list_rpop(self, key):
        return self.redis.rpop(key)

    def list_lpop(self, key):
        return self.redis.lpop(key)

    def list_get_allelement(self, key):
        "获取列表所有元素"
        start_index, end_index = 0, self.list_llen(key)
        return self.list_lrange(key, start_index, end_index)

    def set_sadd(self, key, *values):
        "向集合添加一个或多个成员"
        return self.redis.sadd(key, *values)

    def set_scard(self, key):
        "返回集合成员数"
        return self.redis.scard(key)

    def set_smembers(self, key):
        "返回集合所有成员"
        return self.redis.smembers(key)

    def set_sdiff(self, *keys):
        "返回多个集合中的差集"
        return self.redis.sdiff(*keys)

    def set_sinter(self, *keys):
        "返回多个集合中的交集"
        return self.redis.sinter(*keys)

    def set_sunion(self, *keys):
        "返回多个集合中的并集"
        return self.redis.sunion(*keys)

    def hash_hdel(self, key, *field):
        "删除一个或多个哈希表字段"
        return self.redis.hdel(key, *field)

    def hash_hexists(self, key, *field):
        "查看哈希表 key 中，指定的字段是否存在"
        return self.redis.hexists(key, *field)

    def hash_hget(self, key, field):
        "获取存储在哈希表中指定字段的值。"
        return self.redis.hget(key, field)

    def hash_hgetall(self, key):
        "获取在哈希表中指定 key 的所有字段和值"
        return self.redis.hgetall(key)

    def hash_hkeys(self, key):
        "获取所有哈希表中的字段"
        return self.redis.hkeys(key)


if __name__ == '__main__':
    red = EasyRedis()
    print red.pattern("*_allproject")
