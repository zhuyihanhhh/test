# -*- coding: utf-8 -*-
"""场景清理动作。

全部基于 maya.cmds，不依赖 pymel（Maya 2023+ 已不默认安装 pymel）。
每个函数签名兼容 Maya 回调（接受任意位置参数），返回被清理对象的列表。
"""
from __future__ import absolute_import

import glob
import logging
import os
import shutil
import time

from maya import cmds

from scene_guard import config
from scene_guard.reporter import report

# script 节点的脚本内容分别存在这两个属性里，病毒常只写其中一个
_SCRIPT_ATTRS = ('before', 'after')


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _scene_path():
    return cmds.file(query=True, sceneName=True) or ''


def _is_referenced(node):
    try:
        return bool(cmds.referenceQuery(node, isNodeReferenced=True))
    except Exception:
        return False


def _script_body(node):
    chunks = []
    for attr in _SCRIPT_ATTRS:
        try:
            chunks.append(cmds.getAttr('{0}.{1}'.format(node, attr)) or '')
        except Exception:
            pass
    return '\n'.join(chunks)


def _label(node):
    """去掉命名空间与尾部数字，得到用于匹配名单的基础名。"""
    return node.split(':')[-1].rstrip('0123456789')


def _force_delete(node):
    cmds.lockNode(node, lock=False)
    cmds.delete(node)


def _user_script_dirs():
    """用户脚本目录：<userAppDir>/scripts 与 <userAppDir>/<version>/scripts。"""
    try:
        app_dir = cmds.internalVar(userAppDir=True)
    except Exception:
        app_dir = os.environ.get('MAYA_APP_DIR', '')
    if not app_dir:
        return []

    dirs = [os.path.join(app_dir, 'scripts')]
    dirs.extend(glob.glob(os.path.join(app_dir, '*', 'scripts')))
    return [d for d in dirs if os.path.isdir(d)]


# ---------------------------------------------------------------------------
# 第一道防线：读场景前禁止 script 节点自动执行
# ---------------------------------------------------------------------------

def disable_script_node_execution(*args):
    """挂在 kBeforeOpen：病毒代码在读文件阶段根本不会运行。"""
    cmds.optionVar(intValue=('executeScriptNodes', 0))


def restore_script_node_execution(*args):
    """挂在 kAfterOpen 末尾：恢复正常 script 节点的执行能力。

    必须保证即使清理链抛错也被调用，否则用户环境会残留在禁用态，
    回调注册器已用 try/finally 兜住。
    """
    cmds.optionVar(intValue=('executeScriptNodes', 1))


# ---------------------------------------------------------------------------
# 第二道防线：内存中的恶意节点与 scriptJob
# ---------------------------------------------------------------------------

def kill_virus_script_nodes(*args):
    """按「名字黑名单 + 代码特征」双判据删除恶意 script 节点。

    只删命中判据的节点，正常功能节点不受影响。
    """
    conf = config.load()
    names = conf['virus_node_names']
    codes = conf['virus_node_codes']

    cleaned = []
    for node in cmds.ls(type='script') or []:
        if _is_referenced(node):
            continue

        hit_name = _label(node) in names
        if not hit_name:
            body = _script_body(node)
            if not any(code in body for code in codes):
                continue

        try:
            _force_delete(node)
            cleaned.append(node)
        except Exception as exc:
            report('kill_virus_script_nodes', remark=str(exc),
                   level=logging.WARNING,
                   metadata={'path': _scene_path(), 'node': node})

    if cleaned:
        report('kill_virus_script_nodes',
               metadata={'path': _scene_path(), 'nodes': cleaned})
    return cleaned


def clear_script_nodes(*args):
    """清理白名单之外的全部 script 节点（比病毒清理激进，按需挂载）。

    白名单内的节点若命中危险代码特征，仍会被删除。
    """
    conf = config.load()
    whitelist = conf['script_node_whitelist']
    danger = conf['script_node_danger_codes']

    cleaned = []
    for node in cmds.ls(type='script') or []:
        if _is_referenced(node):
            continue

        body = _script_body(node)
        if _label(node) in whitelist and not any(c in body for c in danger):
            continue

        try:
            _force_delete(node)
            cleaned.append(node)
        except Exception as exc:
            report('clear_script_nodes', remark=str(exc),
                   level=logging.WARNING,
                   metadata={'path': _scene_path(), 'node': node})

    if cleaned:
        report('clear_script_nodes',
               metadata={'path': _scene_path(), 'nodes': cleaned})
    return cleaned


def clear_script_jobs(*args):
    """kill 命中黑名单的 scriptJob（病毒常驻的另一种形态）。"""
    blacklist = config.load()['script_job_blacklist']

    cleaned = []
    for job in cmds.scriptJob(listJobs=True) or []:
        if not any(keyword in job for keyword in blacklist):
            continue
        try:
            cmds.scriptJob(kill=int(job.split(':', 1)[0]), force=True)
            cleaned.append(job)
        except Exception as exc:
            report('clear_script_jobs', remark=str(exc),
                   level=logging.WARNING,
                   metadata={'path': _scene_path(), 'script_job': job})

    if cleaned:
        report('clear_script_jobs',
               metadata={'path': _scene_path(), 'script_jobs': cleaned})
    return cleaned


# ---------------------------------------------------------------------------
# unknown 节点与插件
# ---------------------------------------------------------------------------

def clear_unknown_nodes(*args):
    whitelist = config.load()['unknown_node_whitelist']

    cleaned = []
    for node in cmds.ls(type='unknown') or []:
        if _is_referenced(node) or _label(node) in whitelist:
            continue
        try:
            _force_delete(node)
            cleaned.append(node)
        except Exception as exc:
            report('clear_unknown_nodes', remark=str(exc),
                   level=logging.WARNING,
                   metadata={'path': _scene_path(), 'node': node})

    if cleaned:
        report('clear_unknown_nodes',
               metadata={'path': _scene_path(), 'nodes': cleaned})
    return cleaned


def clear_unknown_dag_nodes(*args):
    """只清理名字命中模式的 unknownDag 节点，默认模式表为空即不动。"""
    patterns = config.load()['unknown_dag_name_patterns']
    if not patterns:
        return []

    cleaned = []
    for node in cmds.ls(type='unknownDag') or []:
        if not any(p in node for p in patterns):
            continue
        try:
            _force_delete(node)
            cleaned.append(node)
        except Exception as exc:
            report('clear_unknown_dag_nodes', remark=str(exc),
                   level=logging.WARNING,
                   metadata={'path': _scene_path(), 'node': node})

    if cleaned:
        report('clear_unknown_dag_nodes',
               metadata={'path': _scene_path(), 'nodes': cleaned})
    return cleaned


def clear_unknown_plugins(*args):
    """移除 unknown 插件的 requires 条目。

    白名单里的插件必须放过：抹掉 requires 后存盘，依赖该插件的节点
    （例如相机遮幅一类的显示插件）会永久丢失且没有任何提示。
    """
    whitelist = config.load()['unknown_plugin_whitelist']
    unknown = cmds.unknownPlugin(query=True, list=True) or []
    if not unknown:
        return []

    in_use = cmds.pluginInfo(query=True, pluginsInUse=True) or []
    cleaned = []
    for plugin in unknown:
        if plugin in whitelist:
            continue

        if plugin in in_use:
            try:
                cmds.unloadPlugin(plugin, force=True)
            except Exception as exc:
                report('clear_unknown_plugins', remark=str(exc),
                       level=logging.WARNING,
                       metadata={'path': _scene_path(), 'plugin': plugin})

        try:
            cmds.unknownPlugin(plugin, remove=True)
            cleaned.append(plugin)
        except Exception as exc:
            report('clear_unknown_plugins', remark=str(exc),
                   level=logging.WARNING,
                   metadata={'path': _scene_path(), 'plugin': plugin})

    if cleaned:
        report('clear_unknown_plugins',
               metadata={'path': _scene_path(), 'plugins': cleaned})
    return cleaned


# ---------------------------------------------------------------------------
# 第三道防线：落盘的注入脚本
# ---------------------------------------------------------------------------

def quarantine_user_scripts(*args):
    """隔离用户脚本目录里的非预期脚本。

    改名而不是删除，保留回滚余地（误判时去掉后缀即可恢复）。
    """
    conf = config.load()
    keep = set(conf['user_script_keep'])
    suffix = conf['quarantine_suffix']

    cleaned = []
    for directory in _user_script_dirs():
        for path in glob.glob(os.path.join(directory, '*.py')) + \
                glob.glob(os.path.join(directory, '*.pyc')):
            name = os.path.basename(path)
            if name in keep or name.replace('.pyc', '.py') in keep:
                continue
            if path.endswith(suffix):
                continue

            target = path + suffix
            try:
                if os.path.exists(target):
                    os.remove(target)
                os.rename(path, target)
                cleaned.append(path)
            except Exception as exc:
                report('quarantine_user_scripts', remark=str(exc),
                       level=logging.WARNING, metadata={'file': path})

    if cleaned:
        report('quarantine_user_scripts', metadata={'files': cleaned})
    return cleaned


# ---------------------------------------------------------------------------
# 附带能力：保存前备份
# ---------------------------------------------------------------------------

def backup_before_save(*args):
    """挂在 kBeforeSave：把保存前的文件拷到 <场景目录>/backupSave/<时间戳>/。"""
    current = _scene_path()
    if not current or not os.path.isfile(current):
        return None

    folder = os.path.join(os.path.dirname(current),
                          config.load()['backup_dir_name'],
                          time.strftime('%Y%m%d%H%M%S'))
    try:
        if not os.path.isdir(folder):
            os.makedirs(folder)
        target = os.path.join(folder, os.path.basename(current))
        shutil.copy(current, target)
        return target
    except Exception as exc:
        report('backup_before_save', remark=str(exc),
               level=logging.WARNING, metadata={'path': current})
        return None
