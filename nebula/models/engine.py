#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings

engine = create_engine(settings.DB_CONNECT_STRING, echo=False, pool_size=100, pool_recycle=14400)
DB_Session = sessionmaker(bind=engine)

default_engine = create_engine(settings.DB_Default_CONNECT_STRING, echo=False, pool_size=100, pool_recycle=14400)
Default_DB_Session = sessionmaker(bind=default_engine)

data_engine = create_engine(settings.DB_Data_CONNECT_STRING, echo=False, pool_size=100)
Data_DB_Session = sessionmaker(bind=data_engine)

# 数据库连接设置
tornado_mysql_config = {
    'host': settings.MySQL_Host,
    'port': settings.MySQL_Port,
    'user': settings.MySQL_User,
    'passwd': settings.MySQL_Passwd,
    'db': settings.Nebula_Data_DB,
    'charset': 'utf8'
}

