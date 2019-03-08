# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger('nebula.dao.cache')

Strategy_Weigh_Cache = None

Cache_Init_Functions = []

def init_caches():
    global Cache_Init_Functions
    for func in Cache_Init_Functions:
        func()
    
    