#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import Mapping, Sequence

__author__ = 'lw'


# name mapping of the internal name and visual name
scene_name_mapping_to_visual = {
    "VISITOR": "访客",
    "ACCOUNT": "帐号",
    "ORDER": "订单",
    "TRANSACTION": "支付",
    "MARKETING": "营销",
    "OTHER": "其他",
    }

scene_name_mapping_to_internal = {v: k for k, v in scene_name_mapping_to_visual.iteritems()}


def _mapping_name(obj, mapping):
    if not obj:
        return obj

    if isinstance(obj, (str, unicode)):
        return mapping.get(obj, obj)
    elif isinstance(obj, Mapping):
        result = dict()
        for k, v in obj.iteritems():
            k = _mapping_name(k, mapping)
            v = _mapping_name(v, mapping)
            result[k] = v
        return result
    elif isinstance(obj, Sequence):
        return [_mapping_name(_, mapping) for _ in obj]
    else:
        return obj


def mapping_name_to_visual(obj):
    """
    mapping internal name to visual name

    :param obj: origin object
    :return: converted object within with the name is converted to visual name
    """
    return _mapping_name(obj, scene_name_mapping_to_visual)


def mapping_name_to_internal(obj):
    """
    mapping visual name to internal name

    :param obj: origin object
    :return: converted object within with the name is converted to internal name
    """
    return _mapping_name(obj, scene_name_mapping_to_internal)
