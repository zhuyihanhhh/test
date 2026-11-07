# -*- coding: utf-8 -*-
"""放到 <userAppDir>/scripts/userSetup.py 即可开机生效。

注意：scene_guard 会隔离用户脚本目录里除白名单外的 .py / .pyc，
userSetup.py 本身在白名单内，但如果你还有别的常驻脚本，
记得加进配置的 user_script_keep。
"""
import logging
import os

logging.basicConfig(level=logging.INFO)

CONFIG = os.path.join(os.path.dirname(__file__), 'scene_guard.yaml')


def _install():
    import scene_guard
    scene_guard.install(config_path=CONFIG if os.path.isfile(CONFIG) else None)


try:
    import maya.utils
    # 延后到 Maya UI 就绪后再注册，避免启动期 API 未初始化
    maya.utils.executeDeferred(_install)
except ImportError:
    pass
