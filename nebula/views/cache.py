# -*- coding: utf-8 -*-

import functools

import pylru

size = 1000

API_Cache = pylru.lrucache(size) # key: "uri_path:method:query_dict" value: method's result

def cache(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        cache_key = ':'.join([self.request.path,
                              self.request.method,
                              repr(self.request.query_arguments)])
        if not cache_key in API_Cache:
            print 'return from realtime query'
            method(self, *args, **kwargs)
        else:
            print 'return from cache'
            # 4 convenient debug
            self.set_header("Content-Location", "Cache")
            self.finish(b"".join(API_Cache[cache_key]))
            return
    return wrapper

class CacheMixin(object):
    def finish(self, chunk):
        # set result to cache
        cache_key = ':'.join([self.request.path,
                              self.request.method,
                              repr(self.request.query_arguments)])
        if not cache_key in API_Cache:
            print 'write cache key:%s' % cache_key
            # now self._write_buffer is [], so we just can add a reference.
            API_Cache[cache_key] = self._write_buffer

        super(CacheMixin, self).finish(chunk)
