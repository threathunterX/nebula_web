# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import logging
import hashlib

from sqlalchemy import Column
from sqlalchemy.types import Integer, VARCHAR, CHAR, BLOB, String
from sqlalchemy.ext.declarative import declarative_base

from .engine import data_engine

from threathunter_common.util import json_dumps
from threathunter_common.util import millis_now, text
from nebula_meta.model.notice import Notice

BaseModel = declarative_base()

logger = logging.getLogger('nebula.models')

class NoticeModel(BaseModel):
    __tablename__ = 'notice'

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer, index=True)
    key = Column(VARCHAR(512), index=True)
    strategy_name = Column(CHAR(100))
    scene_name = Column(CHAR(100))
    checkpoints = Column(CHAR(100))
    check_type = Column(CHAR(100))
    decision = Column(CHAR(100))
    risk_score = Column(Integer)
    expire = Column(Integer)
    remark = Column(VARCHAR(1000))
    last_modified = Column(Integer)
    variable_values = Column(BLOB)
    geo_province = Column(CHAR(100))
    geo_city = Column(CHAR(100))
    test = Column(Integer)
    tip = Column(String(1024))
    uri_stem = Column(String(1024))
    trigger_event = Column(BLOB)

    def to_notice(self):
        data = {
            "timestamp": self.timestamp,
            "key": self.key,
            "strategy_name": self.strategy_name,
            "scene_name": self.scene_name,
            "checkpoints": self.checkpoints,
            "check_type": self.check_type,
            "decision": self.decision,
            "risk_score": self.risk_score,
            "expire": self.expire,
            "remark": self.remark,
            "test": self.test,
            "geo_province": self.geo_province,
            "geo_city": self.geo_city,
            "tip": self.tip,
            "uri_stem": self.uri_stem,
            "variable_values": json.loads(self.variable_values) if self.variable_values else dict(),
            "trigger_event": json.loads(self.trigger_event) if self.trigger_event else dict()
        }
        return Notice.from_dict(data)

    @staticmethod
    def from_notice(n):
        return NoticeModel(
            timestamp=n.timestamp,
            key=n.key,
            strategy_name=n.strategy_name,
            scene_name=n.scene_name,
            checkpoints=n.checkpoints,
            check_type=n.check_type,
            decision=n.decision,
            risk_score=n.risk_score,
            expire=n.expire,
            remark=n.remark,
            variable_values=json.dumps(n.variable_values),
            test=n.test,
            tip=n.tip,
            geo_province=n.geo_province,
            geo_city=n.geo_city,
            uri_stem=n.uri_stem,
            trigger_event=n.trigger_event
        )

    def __str__(self):
        return str(self.__dict__)

class RiskIncidentModel(BaseModel):

    __tablename__ = 'risk_incident'

    id = Column(Integer, primary_key=True)
    ip = Column(CHAR(20))
    associated_events = Column(VARCHAR(2000))
    start_time = Column(Integer)
    strategies = Column(VARCHAR(2000))
    hit_tags = Column(VARCHAR(1000))
    risk_score = Column(Integer)
    uri_stems = Column(VARCHAR(2000))
    hosts = Column(VARCHAR(1000))
    most_visited = Column(CHAR(100))
    peak = Column(CHAR(20))
    dids = Column(CHAR(100))
    associated_users = Column(VARCHAR(1000))
    users_count = Column(Integer)
    associated_orders = Column(VARCHAR(1000))
    status = Column(Integer)
    last_modified = Column(Integer)

    @staticmethod
    def from_dict(risk_incident):
        return RiskIncidentModel(
            ip=risk_incident["ip"],
            associated_events=json_dumps(risk_incident.get(
                "associated_events") or '[]'),  # 风险事件关联事件id
            start_time=risk_incident["start_time"],
            strategies=json_dumps(risk_incident["strategies"]),
            hit_tags=json_dumps(risk_incident["hit_tags"]),
            risk_score=risk_incident["risk_score"],
            uri_stems=json_dumps(risk_incident["uri_stems"]),
            hosts=json_dumps(risk_incident["hosts"]),
            most_visited=risk_incident["most_visited"],
            peak=risk_incident.get("peak"),  # 风险事件关联IP访问峰值
            dids=json_dumps(risk_incident["dids"]),
            associated_users=json_dumps(risk_incident["associated_users"] or '{}'),
            users_count=risk_incident["users_count"],
            associated_orders=json_dumps(
                risk_incident.get("associated_orders") or '{}'),
            status=risk_incident.get("status", 0),
            last_modified=millis_now()
        )

    def to_dict(self):
        return dict(
            id=self.id,
            ip=self.ip,
            associated_events=json.loads(self.associated_events or '[]'),
            start_time=self.start_time,
            strategies=json.loads(self.strategies),
            hit_tags=json.loads(self.hit_tags),
            risk_score=self.risk_score,
            uri_stems=json.loads(self.uri_stems),
            hosts=json.loads(self.hosts),
            most_visited=self.most_visited,
            peak=self.peak,
            dids=json.loads(self.dids),
            associated_users=json.loads(self.associated_users or '{}'),
            users_count=self.users_count,
            associated_orders=json.loads(self.associated_orders or '{}'),
            status=self.status
        )


def init_db():
    BaseModel.metadata.create_all(data_engine)


def drop_db():
    BaseModel.metadata.drop_all(data_engine)
