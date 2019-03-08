#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 不能强制动态导入, 不然单例就不起作用了..
import functools

from nebula_meta.model.notice import Notice


notice_cache = dict()


def get_notice_cache():
    global notice_cache
    return notice_cache


def set_notice_cache(notices_dict=None):
    if notices_dict is None:
        notices_dict = {}

    global notice_cache
    notice_cache = notices_dict


def memoize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return get_notices(*args, **kwargs)


def update_memoize(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        notice = args[1]
        set_notices([notice, ])
        return func(*args, **kwargs)
    return wrapper


def hit_cache(key):
    notice_cache = get_notice_cache()

    if notice_cache.has_key(key):
        return True
    return False


def get_notices(noticedao, check_type, key, test, scene_names=None):
    """
    noticedao 为了兼容这是一个类实例的self参数
    """
    notice_cache = get_notice_cache()

    with_key_notices = notice_cache.get(key, None)
    if with_key_notices is None:
        return []

    valid_notices = with_key_notices

    notices = (Notice(**_) for _ in valid_notices
               if _.get('test') is test)

    if check_type:
        notices = (_ for _ in notices
                   if _.check_type.lower() == check_type.lower())

    if scene_names:
        notices = (_ for _ in notices
                   if _.scene_name in scene_names)

    return list(notices)


def set_notices(notices):
    key = notices[0].get('key')

    notice_cache = get_notice_cache()
    if notice_cache.has_key(key):
        notice_cache[key].extend(notices)
    else:
        notice_cache[key] = notices


def delete_notices(key):
    try:
        notice_cache.pop(key)
    except KeyError:
        pass
