# Maya Scene Guard

Maya 场景卫生治理：恶意 `script` 节点防护 + 配置驱动的回调注册。

针对在团队内通过场景文件交叉传播的 Maya 病毒（`vaccine_gene` / `breed_gene` /
`fuckVirus_gene` / `CgAbBlastPanelOptChangeCallback` 一类）。核心思路不是「崩了再查」，
而是在读文件前就断掉执行路径。

## 三道防线

| 阶段 | 时机 | 做什么 |
|---|---|---|
| 执行前阻断 | `kBeforeOpen` | 关闭 `executeScriptNodes`，恶意代码在读场景阶段根本不会运行 |
| 内存清理 | `kAfterOpen` | 按「名字黑名单 + 代码特征」双判据删除恶意 `script` 节点；kill 可疑 `scriptJob`；清理 unknown 节点与插件 |
| 落盘隔离 | `kAfterOpen` | 扫描用户脚本目录，非白名单脚本**改名隔离而非删除**，保留回滚余地 |

清理链跑完后，注册器在 `finally` 里恢复 `executeScriptNodes`——
即使某个动作抛错，也不会把用户环境留在「禁用」态。

## 安装

```
<userAppDir>/scripts/
├─ userSetup.py          # 本仓库的 userSetup.py
├─ scene_guard.yaml      # 站点配置（可选）
└─ scene_guard/          # 包本体
```

或者把 `scene_guard/` 放进 `PYTHONPATH`，自行调用：

```python
import scene_guard
scene_guard.install()                              # 用内置默认配置
scene_guard.install(config_path='/path/to/scene_guard.yaml')

scene_guard.registered()   # 查看已注册回调
scene_guard.uninstall()    # 全部反注册（开发期反复 reload 用）
```

重复 `install()` 是安全的：回调 ID 以 `事件.函数名` 记账，已注册的会跳过，不会叠加。

## 配置驱动

配置里声明「事件 → 动作名列表」，注册器按事件类型分派到三类通道：
OpenMaya 场景消息（打开前 / 打开后 / 保存前）、`scriptJob` 事件、定时器消息。

```yaml
before_open:
  - disable_script_node_execution
after_open:
  - kill_virus_script_nodes
  - clear_script_jobs
  - clear_unknown_plugins
  - quarantine_user_scripts
before_save:
  - backup_before_save
timer:
  my_reminder: 30          # 每 30 分钟
```

完整可配项见 `scene_guard.yaml` 与 `scene_guard/config.py` 的 `DEFAULTS`。
自定义动作：

```python
from scene_guard.callbacks import register_action
register_action('my_action', my_func)   # 之后即可在配置里按名字引用
```

## 接入内部系统

包内只有两处旁路依赖，都可注入，核心逻辑不感知实现：

```python
import scene_guard

# 上报：默认写 logging，换成内部埋点系统
scene_guard.set_reporter(
    lambda name, remark='', level=20, metadata=None: my_eventlog.publish(
        name, level=level, remark=remark, metadata=metadata))

# 配置：默认读内置 DEFAULTS + YAML，换成配置中心
scene_guard.set_config(my_config_center.get('maya_scene_guard'))
```

这也是本包能脱离任何管线环境运行的原因：清理逻辑只依赖 `maya.cmds` 和标准库。

## ⚠️ 重要：`unknown_plugin_whitelist` 不要留空

`clear_unknown_plugins` 会移除 unknown 插件的 `requires` 条目。
**抹掉之后存盘，依赖该插件的节点会永久丢失，且没有任何提示**——
典型的例子是相机遮幅这类显示插件，制作发现时已经没法恢复。

所以凡是「插件可能没装，但节点必须留着」的插件，都要进白名单。
宁可留一条 `requires`，也不要做静默破坏。

反过来，白名单内的 `script` 节点若检出危险代码，仍然会被清掉——
白名单保护的是身份，不是内容。

## 其他注意事项

- **`clear_script_nodes` 默认不挂载**。它会删掉白名单之外的全部 `script` 节点，
  对使用自定义 `scriptNode` 的项目是破坏性的。只在确认过白名单后开启。
- **`quarantine_user_scripts` 会碰用户的脚本目录**。先确认 `user_script_keep`
  覆盖了你所有常驻脚本，否则会被改名隔离（去掉 `.quarantined` 后缀即可恢复）。
- **`executeScriptNodes` 是 Maya 全局设置**。如果你用别的工具也在改它，注意冲突。
- 只用 `maya.cmds`，不依赖 pymel（Maya 2023+ 已不默认安装 pymel）。
- 优先用 OpenMaya API 2.0，不可用时回落到 1.0。
- 兼容 Python 2.7 / 3.x（Maya 2020 及以前是 Python 2）。

## 测试

`import scene_guard` 本身不碰 Maya API —— config / reporter 两个旁路可在任何
Python 环境下导入与测试，只有真正注册回调时才需要 Maya：

```
python tests/test_sidecars.py      # 或 python -m pytest tests/
```

## 可观测

每次清理都带场景路径与被清对象清单上报，失败记告警。
接上埋点后，感染面、复发率、高发工程都可以统计——
而不是「清完就不知道清了什么」。

## License

MIT
