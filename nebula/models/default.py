# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json, logging

from sqlalchemy import Column
from sqlalchemy.types import Integer, VARCHAR, CHAR, BLOB, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base

from .engine import default_engine

from threathunter_common.eventmeta import EventMeta
from threathunter_common.util import millis_now
from nebula_meta.variable_meta import VariableMeta
from nebula_meta.model.strategy import Strategy

from nebula_meta.event_model import EventModel, add_event_to_registry
from nebula_meta.variable_model import VariableModel, add_variable_to_registry

BaseModel = declarative_base()

logger = logging.getLogger('nebula.models.default')


class ConfigDefaultModel(BaseModel):
    __tablename__ = 'config_default'

    configkey = Column(VARCHAR(1000), primary_key=True)
    configvalue = Column(VARCHAR(4000))
    last_modified = Column(Integer)

    def get_dict(self):
        return {
            "key": self.configkey,
            "value": self.configvalue,
            "last_modified": self.last_modified
        }

    @staticmethod
    def from_dict(d):
        return ConfigDefaultModel(
            configkey=d["key"],
            configvalue=d["value"],
            last_modified=d.get("last_modified", 0)
        )

    def __str__(self):
        return str(self.__dict__)


class StrategyDefaultModel(BaseModel):
    __tablename__ = 'strategy_default'

    id = Column(Integer, primary_key=True)
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    category = Column(CHAR(100))
    score = Column(Integer)
    isLock = Column(Integer)
    tags = Column(CHAR(200))
    remark = Column(String(1000))
    version = Column(CHAR(100))
    status = Column(CHAR(100))
    createtime = Column(BigInteger)
    modifytime = Column(BigInteger)
    starteffect = Column(BigInteger)
    endeffect = Column(BigInteger)
    last_modified = Column(BigInteger)
    config = Column(BLOB)
    group_id = Column(Integer)

    def __str__(self):
        return str(self.__dict__)

    def to_strategy(self):
        return Strategy.from_json(self.config)

    @staticmethod
    def from_strategy(strategy):
        return StrategyDefaultModel(
            app=strategy.app,
            name=strategy.name,
            category=strategy.category,
            isLock=strategy.isLock,
            score=strategy.score,
            tags = strategy.tags,
            remark=strategy.remark,
            version=strategy.version,
            status=strategy.status,
            createtime=strategy.create_time,
            modifytime=strategy.modify_time,
            starteffect=strategy.start_effect,
            endeffect=strategy.end_effect,
            group_id=strategy.group_id,
            last_modified=millis_now(),
            config=strategy.get_json()
        )
        

class VariableMetaDefaultModel(BaseModel):
    __tablename__ = 'variablemeta_default'

    id = Column(Integer, primary_key=True)
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    chinese_name = Column(CHAR(100))
    module = Column(CHAR(100))
    type = Column(CHAR(100))
    dimension = Column(CHAR(100))
    value_type = Column(CHAR(100))
    src_variablesid = Column(CHAR(100))
    src_eventid = Column(CHAR(100))
    priority = Column(Integer)
    properties = Column(VARCHAR(4000))
    expire = Column(Integer)
    ttl = Column(Integer)
    internal = Column(Integer)
    remark = Column(VARCHAR(1000))
    last_modified = Column(Integer)
    fulldata = Column(BLOB)

    def to_variablemeta(self):
        #j = json.loads(self.fulldata)
        try:
            return VariableMeta.from_json(self.fulldata)
        except Exception:
            logger.error('variable default to variablemeta error...')
            logger.error('%s %s %s' % (type(self.fulldata), dir(self.fulldata), self.fulldata))
            return None

    @staticmethod
    def from_variablemeta(meta):
        return VariableMetaDefaultModel(
            app=meta.app,
            name=meta.name,
            chinese_name=meta.chinese_name,
            module=meta.module,
            type=meta.type,
            dimension=meta.dimension,
            value_type=meta.value_type,
            src_variablesid=str(meta.src_variablesid),
            src_eventid=str(meta.src_eventid),
            priority=meta.priority,
            properties=json.dumps(meta.get_dict()["properties"]),
            expire=meta.expire,
            ttl=meta.ttl,
            internal=meta.internal,
            remark=meta.remark,
            last_modified=millis_now(),
            fulldata=meta.get_json()
        )

    def __str__(self):
        return str(self.__dict__)


class VariableMetaDefaultOfflineModel(BaseModel):

    __tablename__ = 'variablemeta_default_offline'

    id = Column(Integer, primary_key=True)
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    type = Column(CHAR(100))
    src_variablesid = Column(CHAR(100))
    src_eventid = Column(CHAR(100))
    priority = Column(Integer)
    properties = Column(VARCHAR(4000))
    expire = Column(Integer)
    ttl = Column(Integer)
    internal = Column(Integer)
    remark = Column(VARCHAR(1000))
    last_modified = Column(Integer)
    fulldata = Column(BLOB)

    def to_variablemeta(self):
        try:
            return VariableMeta.from_json(self.fulldata)
        except Exception as e:
            logger.error(e)
            return None

    @staticmethod
    def from_variablemeta(meta):
        return VariableMetaDefaultOfflineModel(
            app=meta.app,
            name=meta.name,
            type=meta.type,
            src_variablesid=str(meta.src_variablesid),
            src_eventid=str(meta.src_eventid),
            priority=meta.priority,
            properties=json.dumps(meta.get_dict()["properties"]),
            expire=meta.expire,
            ttl=meta.ttl,
            internal=meta.internal,
            remark=meta.remark,
            last_modified=millis_now(),
            fulldata=meta.get_json()
        )

    def __str__(self):
        return str(self.__dict__)


class EventMetaDefaultModel(BaseModel):
    __tablename__ = 'eventmeta_default'

    id = Column(Integer, primary_key=True)
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    type = Column(CHAR(100))
    derived = Column(Integer)
    src_variableid = Column(CHAR(100))
    properties = Column(VARCHAR(4000))
    expire = Column(Integer)
    remark = Column(VARCHAR(1000))
    last_modified = Column(Integer)
    config = Column(BLOB)

    def to_eventmeta(self):
        return EventMeta.from_json(self.config)

    @staticmethod
    def from_eventmeta(meta):
        return EventMetaDefaultModel(
            app=meta.app,
            name=meta.name,
            type=meta.type,
            derived=meta.derived,
            src_variableid=str(meta.src_variableid),
            properties=json.dumps(meta.get_dict()["properties"]),
            expire=meta.expire,
            last_modified=millis_now(),
            config=meta.get_json(),
            remark=meta.remark
        )

    def __str__(self):
        return str(self.__dict__)


class EventModelDefault(BaseModel):
    """
    新的event model
    """

    __tablename__ = 'eventmodel_default'

    id = Column(Integer, primary_key=True)
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    visible_name = Column(CHAR(100))
    type = Column(CHAR(100))
    remark = Column(VARCHAR(1000))
    source = Column(VARCHAR(1000))
    version = Column(CHAR(100))
    properties = Column(VARCHAR(8000))
    last_modified = Column(BigInteger)

    def to_eventmodel(self):
        result = EventModel(self.app, self.name, self.visible_name, self.type, self.remark, json.loads(self.source),
                            self.version, json.loads(self.properties))
        add_event_to_registry(result)
        return result

    @staticmethod
    def from_eventmodel(model):
        return EventModelDefault(
            app=model.app,
            name=model.name,
            visible_name=model.visible_name,
            type=model.type,
            remark=model.remark,
            source=json.dumps(model.source or list()),
            version=model.version,
            properties=json.dumps([_.get_simplified_ordered_dict() for _ in model.simplified_properties]),
            last_modified=millis_now(),
        )

    def __str__(self):
        return str(self.__dict__)


class VariableModelDefault(BaseModel):
    __tablename__ = 'variablemodel_default'

    id = Column(Integer, primary_key=True)
    module = Column(CHAR(100))
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    remark = Column(VARCHAR(1000))
    visible_name = Column(CHAR(100))
    dimension = Column(CHAR(100))
    status = Column(CHAR(100))
    type = Column(CHAR(100))
    value_type = Column(CHAR(100))
    value_subtype = Column(CHAR(100))
    value_category = Column(CHAR(100))
    source = Column(VARCHAR(1000))
    filter = Column(VARCHAR(4000))
    period = Column(VARCHAR(100))
    function = Column(VARCHAR(1000))
    groupbykeys = Column(VARCHAR(1000))
    hint = Column(VARCHAR(1000))
    last_modified = Column(BigInteger)

    def to_variablemodel(self):
        try:
            result = VariableModel(self.module, self.app, self.name, self.remark, self.visible_name, self.dimension,
                                   self.status, self.type, self.value_type, self.value_subtype, self.value_category,
                                   json.loads(self.source), json.loads(self.filter), json.loads(self.period),
                                   json.loads(self.function), json.loads(self.groupbykeys), json.loads(self.hint))
            add_variable_to_registry(result)
            return result
        except Exception as err:
            logger.error('variable model default error...')
            return None

    @staticmethod
    def from_variablemodel(model):
        return VariableModelDefault(
            module=model.module,
            app=model.app,
            name=model.name,
            remark=model.remark,
            visible_name=model.visible_name,
            dimension=model.dimension,
            status=model.status,
            type=model.type,
            value_type=model.value_type,
            value_subtype=model.value_subtype,
            value_category=model.value_category,
            source=json.dumps(model.source),
            filter=model.filter.get_json(),
            period=json.dumps(model.period),
            function=model.function.get_json(),
            groupbykeys=json.dumps(model.groupbykeys),
            last_modified=millis_now(),
            hint=json.dumps(model.hint or dict())
        )

    def __str__(self):
        return str(self.__dict__)


def init_db():
    BaseModel.metadata.create_all(default_engine)


def drop_db():
    BaseModel.metadata.drop_all(default_engine)
