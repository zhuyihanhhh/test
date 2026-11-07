# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CJK = '微软雅黑'
MONO = 'Consolas'

doc = Document()

for sec in doc.sections:
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.8)


def style_font(name, font=CJK, size=None, color=None, bold=None):
    st = doc.styles[name]
    st.font.name = font
    if size:
        st.font.size = Pt(size)
    if color:
        st.font.color.rgb = RGBColor(*color)
    if bold is not None:
        st.font.bold = bold
    st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), font)


style_font('Normal', size=10)
style_font('Heading 1', size=15, color=(0x1F, 0x4E, 0x79), bold=True)
style_font('Heading 2', size=12, color=(0x2E, 0x74, 0xB5), bold=True)
style_font('List Bullet', size=10)
doc.styles['Normal'].paragraph_format.line_spacing = 1.2
doc.styles['Normal'].paragraph_format.space_after = Pt(3)


def _fmt(run, size=10, bold=False, italic=False, color=None, mono=False):
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    f = MONO if mono else CJK
    run.font.name = f
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), f)
    if color:
        run.font.color.rgb = RGBColor(*color)


def h1(text):
    p = doc.add_heading(text, level=1)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    return p


def h2(text):
    p = doc.add_heading(text, level=2)
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(3)
    return p


def para(text, **kw):
    align = kw.pop('align', None)
    p = doc.add_paragraph()
    _fmt(p.add_run(text), **kw)
    if align:
        p.alignment = align
    return p


def lead(label, text):
    p = doc.add_paragraph()
    _fmt(p.add_run(label), bold=True)
    _fmt(p.add_run(text))
    p.paragraph_format.space_after = Pt(2)
    return p


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style='List Bullet')
        _fmt(p.add_run(it))
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.15


def fig(text):
    p = doc.add_paragraph()
    _fmt(p.add_run('［ 图位 ］ ' + text), size=9, italic=True, color=(0x8C, 0x8C, 0x8C))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(6)
    return p


def code(text):
    for line in text.split('\n'):
        p = doc.add_paragraph()
        _fmt(p.add_run(line), size=8.5, mono=True)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0


def table(rows, widths=None):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ''
            p = cells[j].paragraphs[0]
            _fmt(p.add_run(str(val)), size=9, bold=(i == 0))
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.05
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths):
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


# ============================ 头部 ============================
p = doc.add_paragraph()
_fmt(p.add_run('朱怡涵'), size=24, bold=True)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)

para('Technical Artist / TD　·　工具与管线方向', size=12, bold=True,
     color=(0x2E, 0x74, 0xB5), align=WD_ALIGN_PARAGRAPH.CENTER)
para('DCC 插件开发　|　美术管线自动化　|　AI × DCC 基础设施',
     size=10, color=(0x59, 0x59, 0x59), align=WD_ALIGN_PARAGRAPH.CENTER)
para('电话 ____________　·　邮箱 ____________　·　GitHub ____________',
     size=9, color=(0x8C, 0x8C, 0x8C), align=WD_ALIGN_PARAGRAPH.CENTER)

h1('概览')
lead('我做什么　', '在游戏美术工具平台做 DCC 插件与管线自动化：'
                   '为 8 款 DCC 做 AI Agent 接入与 Action 工具层、维护年执行 8 万次的资产自动归档管线、'
                   '把反复出现的制作问题做成工具和规范。（2025.03 — 2026.07）')
lead('关键数据　', '270 个 MR（已合并 236）／49 个代码仓库／8+ 款 DCC 接入／'
                   '14+ 款 DCC 工具链／自动化任务执行 80,000+ 次')
lead('技术栈　　', 'Python 2/3、MaxScript、MEL、ExtendScript；'
                   'Maya / 3ds Max / Blender / Substance Painter / Photoshop / MotionBuilder / '
                   'Marmoset / Nuke / Premiere；DCC 插件与宿主适配、Agent Action / JSON Schema 设计、'
                   'MCP、OpenMaya 回调体系（pymel / MSceneMessage / MTimerMessage）、'
                   '插件打包与部署、Deadline 农场、事件驱动服务、MongoDB、SVN / Git')
lead('支持过的项目', 'H74（AVG 蒙太奇管线，主责）、H72、H73、H55、S18、M1、RSVS')

# ============================ 作品 ============================
h1('代表作品')

h2('01　DCC Agent 能力层　|　8 款 DCC 接入 + 生产工具 Agent 化')
lead('分工说明', '底层通用通信框架（WebSocket 生命周期、JSON-RPC 协议、主线程队列、'
                 'Qt 面板、单例管理）由平台统一提供；我负责其上的两层——'
                 '各 DCC 的宿主适配层，以及面向 Agent 的 Action 工具层。')
lead('痛点　', 'AI 只能生成脚本、无法在软件内执行，闭环断在最后一步；'
               '而通用框架落到具体软件时，宿主差异（Py2/Py3、主线程模型、UI 框架、脚本语言）'
               '和「Agent 到底该被允许做什么」都必须逐款解决。')
fig('图 1：DCC Agent 能力层分层架构（含分工边界）')

lead('A · 宿主适配层', '每款 DCC 一套 bridge 包：客户端薄封装与 action 自动发现、'
                       '宿主主窗口获取与主线程泵适配、控制面板与会话面板入口、单例注入、'
                       '宿主 API 边界隔离（host_api）使 action 逻辑可脱离 DCC 单测。')
table([
    ['软件', '宿主适配关键难点'],
    ['Maya', '最复杂一款：2020/2022 仍为 Python 2，做双版本兼容（bytes/unicode、PySide/PySide2、urllib）；'
             '修复后台线程创建 QTimer 不触发，改由 executeDeferred 在主线程建泵；新建会话解决对话串扰'],
    ['Substance Painter', '原插件为加密包无法部署，独立拆包为非加密插件'],
    ['Photoshop', '定位并修复注册表注册路径错误，架构迁移至独立 bridge 包'],
    ['3ds Max', 'ms 脚本自动搜索与路径执行，AI 客户端菜单入口注入'],
    ['Blender / MotionBuilder / Marmoset / Premiere', '复用接入模板，验证规范通用性'],
], widths=[4.6, 12.4])

lead('B · Action 工具层', '把 DCC 能力按域封装成 Agent 可调用的工具，'
                          '每个 action 带输入/输出 JSON Schema、用途描述与同步/异步声明：'
                          '诊断（运行时信息）、场景（场景信息、按 URL 下载并导入模型、导出模型）、'
                          '选择集、建模节点、脚本执行（Python / MEL）、会话管理，'
                          '以及业务域工具。导入链路还包含贴图色彩空间修复——'
                          '从材质的 metalness / roughness / normal 上溯定位非色彩贴图并改写色彩空间，'
                          '且只修复落在本次导入资产根目录下的贴图节点。')

lead('C · 深度案例', '把既有的「动捕全流程组装」生产工具 Agent 化，暴露 10 个 action。'
                     '难点不在开接口，而在为 Agent 设计安全边界：')
bullets([
    '读写分离：状态读取、配置上下文准备、方案校验为只读 action；写入类 action 单独区分；',
    '禁止 Agent 凭空造数据：Rig 与场景路径只接受用户明确提供或界面已选中的值，'
    '约束写进 action 描述供 Agent 遵循；',
    '二次确认：组装方案须 confirmed=true 才执行；批量提交永不自动触发，'
    'Agent 只负责填表达式与绑定目标，提交动作留给人；',
    '校验先行：配置草案、提交正则、任务目标 URL 均先对当前作用域校验，'
    '缺匹配或重复匹配直接拒绝，且不覆盖源配置；',
    '长任务体验：组装用异步 action 按变体回传进度；服务端 300 秒截断响应时'
    '保留会话并解锁面板，不误判为 DCC 执行失败。',
])
fig('图 2：生产工具 Agent 化的安全边界设计')

lead('成果　', '8 款 DCC 完成接入，覆盖平台全部支持软件，接入规范沉淀为可复用模板；'
               'Agent 可在 Maya 内完成场景查询、模型导入导出、脚本执行，'
               '并驱动动捕组装这类重流程工具；制作侧用自然语言操作 DCC，脚本门槛大幅降低。')
fig('图 3：AI Agent 驱动 Maya 完成动捕组装的实操截图')

h2('02　A2M 资产自动归档管线　|　年执行 81,073 次 · 主要开发维护者')
lead('痛点　', '资产从项目管理系统（Arcolab）到资产库（Muse）需人工搬运；'
               '且归档会静默失败——农场任务显示完成但资产库实际未入库，错误被吞掉。')
lead('方案　', '做成一条配置驱动、幂等可重入的归档管线：任务版本状态变更触发 → '
               'Deadline 农场异步执行 → 目录映射与分类树按需创建 → 文件收集（HTTP / 版本库 sync / 分卷压缩）'
               '→ 资产发布或增量更新 → 链接回写 Arcolab。目录映射、分类结构、稿件分级全部配置下发。')
fig('图 4：A2M 资产自动归档主流程（含幂等跳过与异常分支）')
lead('大文件流水线', '灯光类大体量资产原先「压完再传」会长时间占满农场节点，'
                     '改造为压缩-上传流水线：父 Job 建资产并提前回写占位 → 边压分卷边提交 Upload 子 Job'
                     '（附件追加写规避并发竞争，sidecar 落盘支持断点续传）→ Merge Job 依赖全部子 Job 做收尾，'
                     '父 Job 不阻塞等待。')
fig('图 5：A2M 大文件压缩-上传流水线（Deadline 父子 Job 依赖）')
lead('攻坚　', '静默失败治理（报错回传 + 失败重发）；供应商空间上线后批量修正存量资产链接；'
               '定位上游接口返回 NoneType 的大量报错并在管线侧加兜底；'
               '靠「musePath 已回写即跳过」+ 提前回写占位，解决重触发产生重复资产与重复子 Job。')
lead('成果　', '年度自动归档 81,073 次，归档环节基本零人工介入；支撑供应商归档场景全量上线；'
               '新项目接入只需加配置，无需改代码。')
fig('图 6：Muse 资产页归档结果 / Deadline 农场 Job 依赖关系截图')

h2('03　DCC 云盘启动方案　|　方案提出到落地全链路负责')
lead('痛点　', '制作机单盘被 SVN 工程占满，分支部署与多项目并行受限。')
lead('方案　', '云盘挂载承载工程数据，DCC 启动器直接从云盘读取环境与工具。'
               '启动脚本支持云盘 ID 与挂载路径参数；由子盘改母盘 ID 查询以适配权限模型；'
               '解决多套环境变量加载差异，采用 cmd + post_command 启动；'
               '自动添加 Windows Defender 排除项保障读写性能。')
lead('成果　', '已落地 Maya 2020/2022/2023、3ds Max 2019/2022、Nuke、MotionBuilder、Blender；'
               '本地磁盘压力缓解，形成可复制的云盘 + DCC 启动标准链路，并完成静默挂载专项验证。')
fig('图 7：云盘挂载 → DCC 启动链路')

h2('04　Maya 场景卫生治理　|　配置驱动的启动回调体系 + 病毒防线')
lead('痛点　', 'Maya 长期高发崩溃，表现分散（闪退 / 卡死）、难以复现，只能逐例排查；'
               '根因是场景文件被注入恶意 script 节点，并随文件在团队间交叉传播。')
lead('回调体系', '在 Maya 启动注入层做配置驱动的回调注册：配置里声明「事件 → 模块 → 函数」，'
                 '按事件类型分派到 scriptJob、OpenMaya 场景消息（打开前 / 打开后 / 保存前）'
                 '与定时器消息三类通道；所有回调 ID 以「事件.函数名」记账，'
                 '支持重复注册检测与按需反注册，避免热重载时回调叠加。')
lead('病毒防线', '不止于「删节点」，而是分三道：')
bullets([
    '执行前阻断：打开文件前的回调把 script 节点自动执行开关关掉，'
    '病毒代码在读场景阶段根本不会运行；打开完成后再恢复，不影响正常 script 节点；',
    '内存清理：按「名字黑名单 + 代码特征」双判据定位病毒节点（含 base64 解码等特征），'
    '跳过 reference 节点、解锁后删除；同时按黑名单清理残留的 scriptJob；',
    '落盘隔离：扫描用户 Maya 脚本目录，把非预期的注入脚本改名隔离而非直接删除，保留回滚余地。',
])
lead('工程取舍', '清理链全部带白名单：未知节点 / 未知插件的清理必须放过相机遮幅等关键插件，'
                 '否则抹掉 requires 条目后存盘，相机绑定里的遮幅会永久丢失且无任何提示——'
                 '宁可留条目也不做静默破坏；白名单内的节点若检出危险代码仍会被清掉。')
lead('可观测　', '每次清理都带场景路径与被清节点清单埋点上报，失败记告警，'
                 '使感染面、复发率可统计，而不是「清完就不知道了」。')
lead('同体系能力', '复用同一套回调注册：保存前自动备份到时间戳目录、久未保存提醒、'
                   'namespace 清理、reference 失败编辑清理、关键插件缺失兜底加载并暴露告警。')
lead('成果　', '阻断场景文件交叉感染，崩溃类工单显著下降，制作侧无需感知；'
               '问题从「逐例排查」变为「自动免疫」，并通过配置下发到全量制作机。')
fig('图 8：Maya 回调注册机制与病毒三道防线')

h2('05　渲染农场节点分布式清理定时任务')
lead('痛点　', '农场节点 Temp 与任务缓存持续堆积，需人工逐台清理，易遗漏导致渲染失败。')
lead('方案　', '利用农场 Whitelist 参数把清理作业定向分发到 16 个活跃节点，'
               '定时任务每日凌晨触发，实现「用农场清理农场」；清理策略以 YAML 配置驱动。')
lead('成果　', '节点维护零人工介入，缓存堆积导致的渲染异常被消除。')
fig('图 9：渲染农场节点分布式清理定时任务')

h2('06　事件驱动工具：任务通知机器人 与 批量更名 Action')
lead('痛点　', '平台无法自动感知任务分配、延期与到期状态，需制片人工逐条核查；'
               '且不支持按规则批量修改任务单名称。')
lead('方案　', '通知机器人：状态变更自动推送群消息，支持用户组接收与两分钟窗口消息合并'
               '（MongoDB 暂存聚合）；每日扫描延期任务、缺父单号提醒、按环节自定义字段'
               '（1500 行配置重构精简）；富文本卡片推送 + 5 天到期预警 + web 端展示。'
               '　更名 Action：表单配置规则 + 批量触发，用通知回显结果绕开表单刷新限制。')
lead('成果　', '约 5 周产出 10+ 个 MR；制片的人工核查被自动通知替代，'
               '并修复误通知、重复发送等多项缺陷。另以群机器人实现导演审核列表自动创建与每日通知。')
fig('图 10：富文本卡片通知样式 / web 端展示')

h2('07　AVG 蒙太奇管线支持与工具化　|　H74 · 日常支持主责')
lead('范围　', '2025.08 起全面接手：SVN 冲突清理、客户端崩溃排查、Vatag 标注冲突修复、'
               'Gray 分支双制作验证部署、AI 表情工具对接测试（含日语生成）、'
               'Dialog 全量迁移保障、蒙太奇性能检测工具推进、制作版本统计报表工具开发。')
lead('代表案例', 'Vatag 冲突导致无法标注 → 定位为损坏文件被强行提交，修复方案沉淀为标准 SOP；'
                 '角色异常动作 → 定位蒙太奇残留轨道根因并指导批量修正；'
                 'Dialog 路径不规范 → 输出清单，迁移前完成核对，避免丢数据。')
lead('方法　', '每个被记录的问题都尝试从「一次性修复」升级为「可复用 SOP 或工具」，'
               '支持工作本身就是工具需求的来源。')

h2('08　Maya 检查项规范体系与技术沉淀')
lead('内容　', '梳理 67 项 Maya 场景 / 资产检查项并持续落地（已完成 19+），'
               '为自动化检查工具提供规范依据；另产出云盘静默挂载、分支拉取配置、'
               'Icon 渲染材质赋予、Marmoset 启动脚本等部署文档。')
lead('价值　', '质量校验前移到制作侧自检，减少管线返工；'
               '年度 293 篇工作日志使问题可追溯、方案可复用，降低 TD 重复答疑成本。')

# ============================ 规划 ============================
h1('技术方向规划')
bullets([
    'MCP 体系完善：推进剩余 DCC 接入，探索 AI Agent 直接完成美术任务的完整闭环；',
    '归档管线自愈：完善失败监控与自动重试机制；',
    '云盘方案标准化：静默挂载、自动更新、跨项目配置标准化；',
    '管线工具化：把高频人工处理流程进一步工具化，压缩人工介入成本。',
])

doc.add_paragraph().paragraph_format.space_after = Pt(6)
para('※ 已脱敏：隐去内部仓库链接、合并请求编号、文档链接与同事姓名，细节可面谈展开。',
     size=8.5, italic=True, color=(0x8C, 0x8C, 0x8C))

doc.save('作品集-朱怡涵-TA工具向.docx')
print('saved')
