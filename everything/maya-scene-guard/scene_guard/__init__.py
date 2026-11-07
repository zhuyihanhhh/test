# -*- coding: utf-8 -*-
"""Maya Scene Guard —— 场景卫生治理：恶意 script 节点防护 + 配置驱动的回调注册。

`import scene_guard` 本身不碰 Maya API：config / reporter 两个旁路可在
任何 Python 环境下导入与测试，只有真正注册回调时才需要 Maya。
"""
from __future__ import absolute_import

from scene_guard.config import load as load_config, set_config
from scene_guard.reporter import set_reporter

__version__ = '1.0.0'

__all__ = [
    'install',
    'uninstall',
    'registered',
    'register_action',
    'load_config',
    'set_config',
    'set_reporter',
]


def install(config_path=None):
    """按配置注册全部回调（需要在 Maya 内调用）。"""
    from scene_guard.callbacks import install as _install
    return _install(config_path=config_path)


def uninstall(key=None):
    """反注册回调。"""
    from scene_guard.callbacks import uninstall as _uninstall
    return _uninstall(key=key)


def registered():
    """返回当前已注册的回调 key 列表。"""
    from scene_guard.callbacks import registered as _registered
    return _registered()


def register_action(name, func):
    """注册自定义动作，之后可在配置的事件列表里按名字引用。"""
    from scene_guard.callbacks import register_action as _register
    return _register(name, func)
