# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging
import hashlib

from sqlalchemy import Column
from sqlalchemy.types import Integer, VARCHAR, CHAR, BLOB, Enum, Boolean, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base

from nebula.models.engine import engine

from threathunter_common.util import json_dumps
from threathunter_common.eventmeta import EventMeta
from threathunter_common.util import millis_now, text
from nebula_meta.variable_meta import VariableMeta
from nebula_meta.model.strategy import Strategy
from nebula_meta.event_model import EventModel, add_event_to_registry
from nebula_meta.variable_model import VariableModel, add_variable_to_registry

BaseModel = declarative_base()

logger = logging.getLogger('nebula.models')


class UserModel(BaseModel):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(100))
    password = Column(CHAR(100))
    creator = Column(Integer)
    create_time = Column(Integer)
    last_login = Column(Integer)
    last_modified = Column(Integer)
    is_active = Column(Integer)

    @staticmethod
    def from_dict(user):
        return UserModel(
            name=user["name"],
            password=hashlib.sha1(user["password"]).hexdigest(),
            creator=user["creator"],
            create_time=user.get("create_time", millis_now()),
            last_login=user.get("last_login", 0),
            last_modified=user.get("last_modified", millis_now()),
            is_active=user.get("is_active", 0)
        )

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            creator=self.creator,
            create_time=self.create_time,
            last_login=self.last_login,
            is_active=self.is_active
        )


class GroupModel(BaseModel):

    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(100))
    description = Column(VARCHAR(1000))
    creator = Column(Integer)
    create_time = Column(Integer)
    last_modified = Column(Integer)
    is_active = Column(Integer)

    def is_root(self):
        return True if self.id == 1 else False

    def is_manager(self):
        return True if self.id == 2 else False

    @staticmethod
    def from_dict(group):
        return GroupModel(
            name=group["name"],
            description=group["description"],
            creator=group["creator"],
            create_time=group.get("create_time", millis_now()),
            last_modified=millis_now(),
            is_active=group.get("is_active", 0)
        )

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            description=self.description,
            creator=self.creator,
            create_time=self.create_time,
            is_active=self.is_active
        )


class UserGroupModel(BaseModel):

    __tablename__ = 'user_group'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    group_id = Column(Integer)
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(user_group):
        return UserGroupModel(
            user_id=user_group["user_id"],
            group_id=user_group["group_id"],
            last_modified=millis_now()
        )


class PermissionModel(BaseModel):

    __tablename__ = 'permission'

    id = Column(Integer, primary_key=True)
    codename = Column(CHAR(100))
    app = Column(CHAR(100))
    remark = Column(VARCHAR(1000))
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(permission):
        return PermissionModel(
            codename=permission["codename"],
            app=permission.get("app", "nebula"),
            remark=permission["remark"],
            last_modified=millis_now()
        )

    def to_dict(self):
        return dict(
            id=self.id,
            codename=self.codename,
            app=self.app,
            remark=self.remark
        )


class GroupPermissionModel(BaseModel):

    __tablename__ = 'group_permission'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    permission_id = Column(Integer)
    extra_settings = Column(VARCHAR(1000))
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(group_permission):
        return GroupPermissionModel(
            group_id=group_permission['group_id'],
            permission_id=group_permission['permission_id'],
            extra_settings=group_permission.get('extra_settings', ''),
            last_modified=millis_now()
        )

    def to_dict(self):
        return dict(
            id=self.id,
            group_id=self.group_id,
            permission_id=self.permission_id,
            extra_settings=self.extra_settings
        )


class SessionModel(BaseModel):

    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    user_name = Column(CHAR(100))
    auth_code = Column(CHAR(100))
    expire_time = Column(Integer)

    @staticmethod
    def from_dict(session):
        return SessionModel(
            user_name=session['user_name'],
            auth_code=session['auth_code'],
            expire_time=session['expire_time']
        )


class ConfigCustModel(BaseModel):
    """
    Config*Model share same schema, but default face to Devs, cust ones for customer to custmize.
    """
    __tablename__ = 'config_cust'

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
        return ConfigCustModel(
            configkey=d["key"],
            configvalue=d["value"],
            last_modified=d.get("last_modified", 0)
        )

    def __str__(self):
        return str(self.__dict__)


class EventMetaModel(BaseModel):
    __tablename__ = 'eventmeta'

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
        return EventMetaModel(
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


class EventModelCust(BaseModel):
    """
    新的event model cust
    """
    __tablename__ = 'eventmodel_cust'

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
        properties=json.dumps([_.get_dict() for _ in model.properties])
        return EventModelCust(
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


class RPCServiceModel(BaseModel):
    __tablename__ = 'rpcservice'

    id = Column(Integer, primary_key=True)
    request_app = Column(CHAR(100))
    request_name = Column(CHAR(100))
    response_app = Column(CHAR(100))
    response_name = Column(CHAR(100))
    oneway = Column(Integer)
    remark = Column(VARCHAR(1000))
    last_modified = Column(Integer)

    def to_service_dict(self):
        return {
            "request_app": text(self.request_app),
            "request_name": text(self.request_name),
            "response_app": text(self.response_app),
            "response_name": text(self.response_name),
            "oneway": bool(self.oneway),
            "remark": text(self.remark or "")
        }

    @staticmethod
    def from_service(service):
        request_app = service.request_meta.app
        request_name = service.request_meta.name
        oneway = service.oneway
        remark = service.remark
        if oneway:
            response_app = ""
            response_name = ""
        else:
            response_app = service.response_meta.app
            response_name = service.response_meta.name
        return RPCServiceModel(
            request_name=request_name,
            request_app=request_app,
            response_app=response_app,
            response_name=response_name,
            remark=remark,
            oneway=oneway,
            last_modified=millis_now())

    def __str__(self):
        return str(self.__dict__)


class TagModel(BaseModel):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    last_modified = Column(Integer)

    def __str__(self):
        return str(self.__dict__)

    def to_tag(self):
        return {
            'app': self.app,
            'id': self.id,
            'name': self.name,
        }

    @staticmethod
    def from_tag(tag):
        return TagModel(
            app=tag.get('app'),
            name=tag.get('name'),
            last_modified=millis_now(),
        )


class StrategyCustModel(BaseModel):
    __tablename__ = 'strategy_cust'

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
        return StrategyCustModel(
            app=strategy.app,
            name=strategy.name,
            category=strategy.category,
            isLock=strategy.isLock,
            score=strategy.score,
            tags=','.join(strategy.tags),
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


class VariableMetaCustModel(BaseModel):
    __tablename__ = 'variablemeta_cust'

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
        return VariableMeta.from_json(self.fulldata)

    @staticmethod
    def from_variablemeta(meta):
        return VariableMetaCustModel(
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


class VariableMetaCustOfflineModel(BaseModel):

    __tablename__ = 'variablemeta_cust_offline'

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
        return VariableMeta.from_json(self.fulldata)

    @staticmethod
    def from_variablemeta(meta):
        return VariableMetaCustOfflineModel(
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


class LogParserModel(BaseModel):
    __tablename__ = 'logparser'

    id = Column(Integer, primary_key=True)
    source = Column(CHAR(100))
    dest = Column(CHAR(100))
    terms = Column(VARCHAR(4000))
    host = Column(CHAR(100))
    url = Column(CHAR(100))
    remark = Column(VARCHAR(1000))
    status = Column(Integer)
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(logparser):
        return LogParserModel(
            source=logparser['source'],
            dest=logparser['dest'],
            terms=json.dumps(logparser['terms']),
            host=logparser.get('host', ''),
            url=logparser.get('url', ''),
            remark=logparser.get('remark', ''),
            status=logparser.get('status', 0),
            last_modified=millis_now()
        )

    def to_dict(self):
        return dict(
            id=self.id,
            source=self.source,
            dest=self.dest,
            terms=json.loads(self.terms),
            host=self.host,
            url=self.url,
            remark=self.remark,
            status=self.status
        )


class LogQueryModel(BaseModel):
    __tablename__ = 'logquery'

    id = Column(Integer, primary_key=True)
    fromtime = Column(Integer)
    endtime = Column(Integer)
    terms = Column(VARCHAR(2000))
    show_cols = Column(VARCHAR(1000))
    user_id = Column(Integer)
    page = Column(Integer)
    total = Column(Integer)
    temp_query_file = Column(CHAR(100))
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(logquery):
        return LogQueryModel(
            fromtime=logquery['fromtime'],
            endtime=logquery['endtime'],
            terms=json_dumps(logquery['terms']),
            show_cols=','.join(logquery['show_cols']),
            user_id=logquery['user_id'],
            page=logquery.get('page', 1),
            total=logquery.get('total', 1),
            temp_query_file=logquery.get('temp_query_file', ''),
            last_modified=millis_now()
        )

    def to_dict(self):
        return dict(
            id=self.id,
            fromtime=self.fromtime,
            endtime=self.endtime,
            terms=json.loads(self.terms),
            show_cols=self.show_cols.split(','),
            user_id=self.user_id,
            page=self.page,
            total=self.total,
            temp_query_file=self.temp_query_file
        )


class FollowKeywordModel(BaseModel):
    __tablename__ = 'follow_keyword'

    id = Column(Integer, primary_key=True)
    keyword = Column(VARCHAR(100))
    keyword_type = Column(Enum("page", "uid", "did", "ip"))
    is_followed = Column(Boolean)
    is_ignored = Column(Boolean)
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(follow):
        return FollowKeywordModel(
            keyword=follow['keyword'],
            keyword_type=follow['keyword_type'],
            is_followed=follow['is_followed'],
            is_ignored=follow['is_ignored'],
            last_modified=follow.get('last_modified', millis_now())
        )

    def to_dict(self):
        return dict(
            id=self.id,
            keyword=self.keyword,
            keyword_type=self.keyword_type,
            is_followed=self.is_followed,
            is_ignored=self.is_ignored
        )


class VariableModelCust(BaseModel):
    __tablename__ = 'variablemodel_cust'

    id = Column(Integer, primary_key=True)
    module = Column(CHAR(100))
    app = Column(CHAR(100))
    name = Column(CHAR(100))
    remark = Column(VARCHAR(255))
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
        except Exception:
            logger.error('variable model cust error...')
            return None

    @staticmethod
    def from_variablemodel(model):
        return VariableModelCust(
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
    BaseModel.metadata.create_all(engine)


def drop_db():
    BaseModel.metadata.drop_all(engine)
