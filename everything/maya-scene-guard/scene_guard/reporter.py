# -*- coding: utf-8 -*-
"""上报旁路。

默认写入标准 logging；接入内部埋点系统时用 set_reporter() 注入即可，
核心清理逻辑不感知上报实现。
"""
from __future__ import absolute_import

import json
import logging

LOGGER = logging.getLogger('scene_guard')

_reporter = None


def set_reporter(func):
    """注入自定义上报实现。

    func(name, remark='', level=logging.INFO, metadata=None)
    传入 None 可恢复默认 logging 行为。
    """
    global _reporter
    _reporter = func


def report(name, remark='', level=logging.INFO, metadata=None):
    metadata = metadata or {}
    metadata['status'] = 'failed' if level >= logging.WARNING else 'success'

    if _reporter is not None:
        _reporter(name, remark=remark, level=level, metadata=metadata)
        return

    try:
        detail = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        detail = repr(metadata)
    LOGGER.log(level, '%s %s %s', name, remark, detail)
