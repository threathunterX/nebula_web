# -*- coding: utf-8 -*-

import time
from os import path as opath
from datetime import datetime

import jinja2

executor = None # ThreadExecutor

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'

def render(template_path, context):
    """
    Assuming a template at /some/path/my_tpl.html, containing:

    Hello {{ firstname }} {{ lastname }}!

    >> context = {
    'firstname': 'John',
    'lastname': 'Doe'
    }
    >> result = render('/some/path/my_tpl.html', context)
    >> print(result)
    Hello John Doe!
    """

    path, filename = opath.split(template_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def get_hour_strs_fromtimestamp(fromtime, endtime ):
    # fromtime, endtime is float timestamp
    if fromtime >= endtime:
        return []
    ts = []
    while fromtime < endtime:
        ts.append(fromtime)
        fromtime = fromtime + 3600

    if ts and ts[-1] + 3600 < endtime:
        ts.append(endtime)
    return ts

def get_hour_strs(fromtime, endtime, f='%Y%m%d%H'):
    timestamps = get_hour_strs_fromtimestamp(fromtime, endtime)
    hours = [ datetime.fromtimestamp(_).strftime(f) for _ in timestamps]
    return hours


def get_hour_start(point=None):
    """
    获取point时间戳所在的小时的开始的时间戳, 默认获取当前时间所在小时的开始时的时间戳
    """
    if point is None:
        p = time.time()
    else:
        p = point

    return (int(p) / 3600) * 3600

def dict_merge(src_dict, dst_dict):
    """
    将两个dict中的数据对应键累加,
    不同类型值的情况:
    >>> s = dict(a=1,b='2')
    >>> d = {'b': 3, 'c': 4}
    >>> dict_merge(s,d)
    >>> t = {'a': 1, 'b': 5, 'c': 4}
    >>> s == t
    True
    >>> s = dict(a=set([1,2]), )
    >>> d = dict(a=set([2, 3]),)
    >>> dict_merge(s,d)
    >>> t = {'a':set([1,2,3])}
    >>> s == t
    True
    >>> s = dict(a={'a':1, 'b':2})
    >>> d = dict(a={'a':1, 'b':2})
    >>> dict_merge(s, d)
    >>> t = dict(a={'a':2, 'b':4})
    >>> s == t
    True
    """
    if src_dict is None:
        return dst_dict
    for k,v in dst_dict.iteritems():
        if not src_dict.has_key(k):
            src_dict[k] = v
        else:

            if isinstance(v, (basestring, int, float)):
                src_dict[k] = int(v) + int(src_dict[k])
            elif isinstance(v, set):
                assert type(v) == type(src_dict[k]), 'key %s,dst_dict value: %s type: %s, src_dict value: %s type:%s' % (k, v, type(v), src_dict[k], type(src_dict[k]))
                src_dict[k].update(v)
            elif isinstance(v, dict):
                assert type(v) == type(src_dict[k]), 'key %s,dst_dict value: %s type: %s, src_dict value: %s type:%s' % (k, v, type(v), src_dict[k], type(src_dict[k]))
                dict_merge(src_dict[k], v)
