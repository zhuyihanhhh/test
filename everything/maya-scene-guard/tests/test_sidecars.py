# -*- coding: utf-8 -*-
"""不依赖 Maya 的测试：验证 config / reporter 两个旁路可独立工作。

运行：python -m pytest tests/ 或 python tests/test_sidecars.py
"""
from __future__ import absolute_import

import io
import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scene_guard import config, reporter


def test_defaults_loaded():
    config.set_config(None)
    conf = config.load()
    assert 'vaccine_gene' in conf['virus_node_names']
    assert 'disable_script_node_execution' in conf['before_open']


def test_json_override():
    config.set_config(None)
    path = os.path.join(tempfile.mkdtemp(), 'scene_guard.json')
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps({'unknown_plugin_whitelist': ['my_plugin']}))

    conf = config.load(path)
    assert conf['unknown_plugin_whitelist'] == ['my_plugin']
    # 未覆盖的键仍是默认值
    assert 'vaccine_gene' in conf['virus_node_names']


def test_inject_config():
    config.set_config({'script_job_blacklist': ['only_this']})
    assert config.load()['script_job_blacklist'] == ['only_this']
    config.set_config(None)


def test_reporter_injection():
    received = []
    reporter.set_reporter(
        lambda name, remark='', level=logging.INFO, metadata=None:
        received.append((name, metadata)))

    reporter.report('kill_virus_script_nodes', metadata={'nodes': ['a']})
    assert received[0][0] == 'kill_virus_script_nodes'
    assert received[0][1]['status'] == 'success'

    reporter.report('oops', level=logging.WARNING)
    assert received[1][1]['status'] == 'failed'

    reporter.set_reporter(None)


if __name__ == '__main__':
    for name, func in sorted(globals().items()):
        if name.startswith('test_'):
            func()
            print('ok  ' + name)
    print('all passed')
