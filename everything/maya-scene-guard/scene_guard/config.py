# -*- coding: utf-8 -*-
"""配置旁路。

默认配置内置于此，核心逻辑只读 load() 的结果。
站点化差异（内部插件白名单、项目特有脚本等）走 YAML / JSON 覆盖，
或在启动时 set_config() 直接注入，不需要改代码。
"""
from __future__ import absolute_import

import copy
import io
import json
import os

from scene_guard.reporter import LOGGER

# ---------------------------------------------------------------------------
# 默认配置
# ---------------------------------------------------------------------------
DEFAULTS = {
    # --- 恶意 script 节点判据 ---------------------------------------------
    # 名字命中即删（公开已知的 Maya 场景病毒家族）
    'virus_node_names': [
        'vaccine_gene',
        'breed_gene',
        'fuckVirus_gene',
        'maya_secure_system',
        'maya_secure_system_scriptNode',
    ],
    # 节点脚本内容命中任一特征即删
    'virus_node_codes': [
        'import base64',
        'vaccine_gene',
        'breed_gene',
        'fuckVirus',
        'maya_secure_system',
        'MayaSecureSystem',
        'CgAbBlastPanelOptChangeCallback',
    ],

    # --- 常规 script 节点清理（比病毒清理更激进，默认不挂载） --------------
    # 白名单内的节点放过，但若命中 danger_codes 仍会被删
    'script_node_whitelist': [
        'uiConfigurationScriptNode',
        'sceneConfigurationScriptNode',
        '_sceneConfigurationScriptNode',
        'xgenGlobals',
    ],
    'script_node_danger_codes': [
        'write',
        'import base64',
        'CgAbBlastPanelOptChangeCallback',
    ],

    # --- 可疑 scriptJob ----------------------------------------------------
    'script_job_blacklist': [
        'vaccine',
        'daxunhuan',
        'PuTianTongQing',
        '()',
    ],

    # --- unknown 节点 / 插件清理 -------------------------------------------
    'unknown_node_whitelist': [],
    'unknown_dag_name_patterns': [],
    # 这些插件即使未加载也保留 requires 条目：抹掉后存盘会静默丢数据
    'unknown_plugin_whitelist': [
        'stereoCamera',
    ],

    # --- 用户脚本目录隔离 ---------------------------------------------------
    'user_script_keep': [
        'userSetup.py',
        'userSetup.mel',
    ],
    'quarantine_suffix': '.quarantined',

    # --- 保存前备份 ---------------------------------------------------------
    'backup_dir_name': 'backupSave',

    # --- 回调挂载表：事件 -> 函数名列表 -------------------------------------
    # 函数名解析自 scene_guard.cleanup，也可用 register_action() 扩展
    'before_open': [
        'disable_script_node_execution',
    ],
    'after_open': [
        'kill_virus_script_nodes',
        'clear_script_jobs',
        'clear_unknown_nodes',
        'clear_unknown_dag_nodes',
        'clear_unknown_plugins',
        'quarantine_user_scripts',
    ],
    'before_save': [],
    # scriptJob 事件名 -> 函数名列表，例如 {'SceneOpened': ['log_scene_opened']}
    'script_jobs': {},
    # 函数名 -> 间隔分钟数
    'timer': {},
}


_config = None


def set_config(data):
    """直接注入配置字典（与默认配置浅合并）。传 None 则清空，回到默认。"""
    global _config
    if data is None:
        _config = None
        return
    merged = copy.deepcopy(DEFAULTS)
    merged.update(data)
    _config = merged


def load(path=None):
    """读取配置：已注入则直接返回；给了 path 则读文件覆盖默认值。"""
    global _config
    if _config is not None:
        return _config

    merged = copy.deepcopy(DEFAULTS)
    if path:
        data = _read_file(path)
        if data:
            merged.update(data)
    _config = merged
    return _config


def _read_file(path):
    if not os.path.isfile(path):
        LOGGER.warning('scene_guard config not found: %s', path)
        return None

    with io.open(path, 'r', encoding='utf-8') as handle:
        text = handle.read()

    if path.lower().endswith('.json'):
        return json.loads(text)

    try:
        import yaml
    except ImportError:
        LOGGER.warning(
            'PyYAML unavailable, cannot read %s (use .json instead)', path)
        return None
    return yaml.safe_load(text)
