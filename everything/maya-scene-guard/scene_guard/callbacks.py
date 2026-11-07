# -*- coding: utf-8 -*-
"""配置驱动的回调注册器。

配置里声明「事件 -> 函数名列表」，这里按事件类型分派到三类通道：
  - OpenMaya 场景消息（打开前 / 打开后 / 保存前）
  - scriptJob 事件
  - 定时器消息

所有回调 ID 以 '事件.函数名' 记账，支持重复注册检测与按需反注册，
避免反复 reload 时回调叠加。
"""
from __future__ import absolute_import

import logging

from maya import cmds

try:                                    # Maya 2017+ 提供 API 2.0
    from maya.api import OpenMaya as om
except ImportError:                     # pragma: no cover
    from maya import OpenMaya as om

from scene_guard import cleanup, config
from scene_guard.reporter import LOGGER

_SCENE_EVENTS = {
    'before_open': 'kBeforeOpen',
    'after_open': 'kAfterOpen',
    'before_save': 'kBeforeSave',
}

# 回调 ID 账本：{'event.function': callback_id}
_CALLBACKS = {}

# 可执行动作表，默认取 cleanup 模块里的公开函数
_ACTIONS = dict(
    (name, getattr(cleanup, name))
    for name in dir(cleanup)
    if not name.startswith('_') and callable(getattr(cleanup, name))
)


def register_action(name, func):
    """注册自定义动作，之后即可在配置的事件列表里按名字引用。"""
    _ACTIONS[name] = func


def registered():
    """返回当前已注册的回调 key 列表。"""
    return sorted(_CALLBACKS.keys())


def _resolve(names):
    actions = []
    for name in names or []:
        func = _ACTIONS.get(name)
        if func is None:
            LOGGER.warning('scene_guard: unknown action %r, skipped', name)
            continue
        actions.append((name, func))
    return actions


def _run(actions, *args):
    """顺序执行动作，单个失败不打断后续。"""
    for name, func in actions:
        try:
            func(*args)
        except Exception:
            LOGGER.exception('scene_guard: action %s failed', name)


def _make_after_open(actions):
    """打开文件后的清理链，用 finally 保证恢复 script 节点执行开关。"""
    def _handler(*args):
        try:
            _run(actions, *args)
        finally:
            try:
                cleanup.restore_script_node_execution()
            except Exception:
                LOGGER.exception(
                    'scene_guard: failed to restore executeScriptNodes')
    return _handler


def _add_scene_callback(key, event_attr, handler):
    if key in _CALLBACKS:
        return
    callback_id = om.MSceneMessage.addCallback(
        getattr(om.MSceneMessage, event_attr), handler)
    _CALLBACKS[key] = callback_id
    LOGGER.info('scene_guard: installed %s', key)


def install(config_path=None):
    """按配置注册全部回调。重复调用是安全的（已注册的会跳过）。"""
    conf = config.load(config_path)

    # --- OpenMaya 场景消息 -------------------------------------------------
    for conf_key, event_attr in _SCENE_EVENTS.items():
        actions = _resolve(conf.get(conf_key))
        if not actions and conf_key != 'after_open':
            continue

        if conf_key == 'after_open':
            # 即使清理链为空也要挂，否则 before_open 关掉的开关没人恢复
            handler = _make_after_open(actions)
            _add_scene_callback('after_open.cleanup_chain',
                                event_attr, handler)
            continue

        for name, func in actions:
            _add_scene_callback('{0}.{1}'.format(conf_key, name),
                                event_attr, func)

    # --- scriptJob ---------------------------------------------------------
    for event_name, names in (conf.get('script_jobs') or {}).items():
        for name, func in _resolve(names):
            key = 'scriptJob:{0}.{1}'.format(event_name, name)
            if key in _CALLBACKS:
                continue
            job_id = cmds.scriptJob(event=[event_name, func])
            _CALLBACKS[key] = job_id
            LOGGER.info('scene_guard: installed %s', key)

    # --- 定时器 ------------------------------------------------------------
    for name, minutes in (conf.get('timer') or {}).items():
        key = 'timer.{0}'.format(name)
        if key in _CALLBACKS:
            continue
        resolved = _resolve([name])
        if not resolved:
            continue
        callback_id = om.MTimerMessage.addTimerCallback(
            float(minutes) * 60, resolved[0][1])
        _CALLBACKS[key] = callback_id
        LOGGER.info('scene_guard: installed %s (every %s min)', key, minutes)

    return registered()


def uninstall(key=None):
    """反注册：给 key 则只摘一个，不给则全摘。"""
    keys = [key] if key else list(_CALLBACKS.keys())

    for item in keys:
        callback_id = _CALLBACKS.pop(item, None)
        if callback_id is None:
            continue
        try:
            if item.startswith('scriptJob:'):
                cmds.scriptJob(kill=callback_id, force=True)
            else:
                om.MMessage.removeCallback(callback_id)
            LOGGER.info('scene_guard: removed %s', item)
        except Exception:
            LOGGER.exception('scene_guard: failed to remove %s', item)

    # 全部摘掉后确保开关不残留在禁用态
    if not _CALLBACKS:
        try:
            cleanup.restore_script_node_execution()
        except Exception:
            LOGGER.log(logging.WARNING,
                       'scene_guard: restore executeScriptNodes skipped')
