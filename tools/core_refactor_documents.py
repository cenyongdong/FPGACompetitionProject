"""Record the completed source migration and actual validation, preserving history."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, text):
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    native = json.loads((E / 'native-20261013-r1.review.json').read_text(encoding='utf-8'))
    build = json.loads((E / 'build-review.json').read_text(encoding='utf-8'))
    cpu = json.loads((E / 'board/cpu.acceptance.json').read_text(encoding='utf-8'))
    short = json.loads((E / 'board/short.review.json').read_text(encoding='utf-8'))
    assert native['status'] == 'native_regressions_passed' and cpu['status'] == 'cpu107_current_core_passed'
    assert short['status'] == 'end_to_end_demo_passed' and short['input_windows'] == 3
    adr = ROOT / 'ADR/ADR_47.md'
    assert not adr.exists(), 'Preserve prior decision'
    snapshot = E / 'original-documents'
    before = snapshot / 'REFERENCES.md'
    if not before.exists():
        shutil.copyfile(ROOT / 'REFERENCES.md', before)

    write(adr, '''# ADR_47：正式核心目录与保持行为的可读性重构

日期：2026-10-13。用户批准当前演示完整主链重构、等价拆分长函数、新建正式核心并保留原源码；明确由代理执行本机/FPAI、Lite CPU107及三窗口回归。本轮不执行60窗口，不恢复旧DATA坏读排查。

## 问题与决策

当前演示依赖的生产模块、历史检查器与故障实验原先混放在pose_v1；实际编译来源还依赖版本文件到构建别名的导出映射，直接整理同名旧模块容易改错对象。按sensor_protocol.cpp的四空格、同行花括号、中文步骤注释和逻辑间空行整理，迁入software/core六个功能目录；旧路径与旧内容保留，当前demo只编译新核心。

迁入21份CPP、31份HPP和1份Python。52份C++核心去注释后逐token一致，预处理/CPU/Gather/NPU/公开SDK读/诊断/帧协议/模型RAW/SDK/BOOT保持。应用参数解析提取demo_options；三个视频线程入口独立封装，原局部变量、异常捕获、线程启动与join顺序保持。Python展开连写步骤，补充职责注释；构建分为导出、SDK身份、厂商暂存和编译，原检查器只调整构建链接。

旧锁126份源码逐项核验；926份历史源码/脚本原字节保持。新锁追加三份原检查器来源，逐项锁定新核心并继续导出原编译别名。新锁不是旧源码逐位未变的声明，迁移前锁、原demo副本、路径/哈希映射和文档修订分别归档。

## 实施中发现与处理

当前D盘工作区没有原.local环境和参考；Docker/WSL及既有FPAI起初停止。仅启动既有工具运行时，没有安装或改变配置。git worktree核验定位到仍存在的dea3工作区，原NumPy2.2.5/Python3.10.21环境和CPU107/三窗口参考逐字节复制至新验证目录，旧工作区不写入。默认Python的fixture准备因NumPy版本不符在生成任何包或用例之前拒绝；未绕过版本门禁、未安装替代环境。

早期格式化的逐token门检发现三冒号空格会改变词法边界，先纠正生成器再进入编译；原源码始终未改。ARM的一条私有need(std::string)未使用警告，用相同编译选项对旧CPU适配源码重现，保留原重载并记录依据，未放宽其他检查。

## 实际验证

| 阶段 | 结果与范围 |
|---|---|
| 静态 | 原锁126、冻结926、52份核心C++逐token通过；生产目标仅用新核心，测试正文保持 |
| 本机 | 11组SDK无关检查器通过：TCP、AU、Host失败、阶段、调用证据、生产者计数、存储身份、读边界、显示IPC、预处理、渲染 |
| 独立字节对照 | 308/309/310的CSI记录新旧逐字节；预处理同时逐位旧实现及原参考；RGB/RGB565/NV12/NV21颜色及骨架画面逐字节 |
| FPAI | 56条命令成功，3个演示程序及11个回归程序ARM构建；15份SDK头与189份厂商文件匹配；仅旧基线同源unused-function警告 |
| Lite CPU | 原107例、12条注册、22输出、59600 FP32逐位通过，272.58892371秒，在原300秒预算内；Host-only，无NPU前向/规整 |
| Lite三窗口 | 3接收/3消费/3完整输出、0覆盖、3不同姿态；全部CSI、预处理、分数和姿态逐位308/309/310原参考；2Hz输入，354编码/294主机GUI解码 |
| 视频与清理 | 全3真实姿态来源和42关节通过；完整原H264354帧解码；正常drain/LAST、两STREAMOFF、join先于Engine销毁、进程与端口回收通过 |
| 最终身份 | BOOT/SDK库与开始相同、FPGA operating、内核日志相同，规整0、无重启/CMA/BOOT/模型/SDK修改；全部本批认证连接与播放器结束 |

本轮构建：.local/pose-v1-build/demo-refactor-20261013-r1；新板端目录/tmp/wifi-pose-demo-refactor-20261013-r1。CPU与三窗口分别保存原始回传tar、完整值、日志和SHA，未续用失败Session。

## 边界与证据

这是重构后的固定功能/数值/三窗口视频回归，不是旧DATA根因修复，不是60窗口重验、严格5Hz、长期、永久首次启动或HDMI验收。272.59秒CPU结果不构成延长300秒预算的许可。原警告不代表新增数学问题，但后续编译仍需核对实际SDK签名与身份。

[核心导读](../software/core/README.md)、[演示说明](../software/demo/README.md)、[完整证据](../tools/pose-v1/evidence/core-refactor-20261013-r1/README.md)、[迁移映射](../tools/pose-v1/evidence/core-refactor-20261013-r1/source-migration.json)、[静态](../tools/pose-v1/evidence/core-refactor-20261013-r1/static-review.json)、[本机](../tools/pose-v1/evidence/core-refactor-20261013-r1/native-20261013-r1.review.json)、[构建](../tools/pose-v1/evidence/core-refactor-20261013-r1/build-review.json)、[CPU107](../tools/pose-v1/evidence/core-refactor-20261013-r1/board/cpu.acceptance.json)、[三窗口](../tools/pose-v1/evidence/core-refactor-20261013-r1/board/short.review.json)、[视频](../tools/pose-v1/evidence/core-refactor-20261013-r1/board/short.video-review.json)。
''')

    path = ROOT / 'PROJECT-PROGRESS.md'
    text = path.read_text(encoding='utf-8')
    text = text.replace('文档整理日期：2026-10-13。最近一次实际板端验证：2026-10-11；本次仅整理文档，未构建、连接或运行板子。',
                        '更新日期：2026-10-13。最近一次实际板端验证：2026-10-13；当前正式核心重构、本机/FPAI、Lite CPU107和三窗口回归已完成。')
    text = text.replace('- software/demo整合、板测、主机实际实时显示及ADR/TechDetails技术报告已完成，当前无后台工作。',
                        '- 当前demo已切换software/core六个功能目录；旧pose_v1与历史测试保持。重构后的11组本机、ARM构建、CPU107/59600 FP32及3窗口全数值/354编码/294 GUI解码通过；规整0，资源回收完成，当前无后台项目工作。[ADR_47](ADR/ADR_47.md)／[证据](tools/pose-v1/evidence/core-refactor-20261013-r1/README.md)。')
    text = text.replace('最近成功演示的数据', '2026-10-11完整演示的数据（历史范围）')
    text = text.replace('以下为2026-10-11已核基线，不表示2026-10-13重新查询过设备。使用前应核验实际身份。',
                        '2026-10-13本轮重新核对BOOT/SDK/模型/内核与FPGA operating；固定身份保持。后续使用前仍应核验实际身份。2026-10-11完整演示及重启记录保留各自范围。')
    text = text.replace('| 已验证demo | 构建.local/pose-v1-build/demo-20261011-r5，成功板端目录/tmp/wifi-pose-demo-20261011-r4；[运行说明](software/demo/README.md) |',
                        '| 当前重构demo | 构建.local/pose-v1-build/demo-refactor-20261013-r1，板端/tmp/wifi-pose-demo-refactor-20261013-r1；3窗口回归通过。[运行说明](software/demo/README.md)、[核心导读](software/core/README.md) |')
    text = text.replace('当前只交付整理结果，不自动板测或恢复暂停排查。',
                        '当前重构及已批准CPU107/三窗口验证完成，不继续60窗口或恢复暂停排查。')
    write(path, text)

    path = ROOT / 'ADR/TechDetails.md'
    text = path.read_text(encoding='utf-8').replace('更新日期：2026-10-11。', '更新日期：2026-10-13。', 1)
    text = text.replace('## 1. 系统组成与数据流', '''## 当前源码入口及重构回归

当前演示只使用[正式核心](../software/core/README.md)中的input/inference/diagnostics/display/video/stream，应用编排仍在software/demo。原pose_v1文件及测试保留作历史依据；新旧文件/导出别名/哈希见[迁移映射](../tools/pose-v1/evidence/core-refactor-20261013-r1/source-migration.json)。公共接口、数学、协议、SDK与固定模型保持。

2026-10-13实际完成11组本机检查、旧实现/原参考字节对照及ARM构建；Lite CPU107的22输出/59600 FP32逐位通过。新三窗口308/309/310全CSI/预处理/分数/姿态逐位旧参考，354编码、294主机GUI解码，全3来源及42关节核验；正常drain/LAST、两STREAMOFF和所有权回收通过，规整0、BOOT/SDK/内核相同。具体范围见[ADR_47](ADR_47.md)。下文2026-10-11三/60窗口数据仍是原独立演示证据，不累加成新的样本精度或吞吐验收。

## 1. 系统组成与数据流''', 1)
    migration = json.loads((E / 'source-migration.json').read_text(encoding='utf-8'))
    aliases = {row.get('build_alias'): row['destination'] for row in migration['files'] if row.get('build_alias')}
    def current_link(match):
        return '../' + aliases.get(match.group(1), 'software/pose_v1/' + match.group(0).split('software/pose_v1/', 1)[1])
    text = re.sub(r'\.\./software/pose_v1/(?:src|include)/([\w.]+)', current_link, text)
    write(path, text)

    path = ROOT / 'DIFFICULTIES.md'
    text = path.read_text(encoding='utf-8')
    marker='## 维护与追溯'
    text = text.replace(marker, '''## 本轮源码迁移与环境核验

| 编号 | 现象与影响 | 处理与证据 | 剩余边界 |
|---|---|---|---|
| D31 | 新工作区缺旧.local参考/环境，版本文件导出别名容易改错核心；FPAI起初停止 | 核验git worktree，恢复原NumPy2.2.5及原CPU107/三窗口参考；启动既有FPAI，不安装。新核心52份C++逐token、926冻结文件、11本机、CPU107和三窗口通过。[ADR_47](ADR/ADR_47.md) | 旧缓存不是永久来源保证；后续先核路径与身份，不能将默认Python版本或导出名当基线 |

''' + marker, 1)
    text = text.replace('本轮没有设备操作、修复或新验收；暂停状态和83/100管理估计保持。',
                        '2026-10-13重构回归有实际CPU107和三窗口设备验证；旧DATA问题未修且继续暂停，83/100管理估计保持。原文档整理阶段“无设备操作”只适用于其历史范围。')
    write(path, text)

    path = ROOT / 'Done.md'
    text = path.read_text(encoding='utf-8')
    entry='''## 2026-10-13：正式核心可读性重构及回归完成

### 工程内容总结

按sensor_protocol.cpp规范将当前演示实际依赖的21 CPP/31 HPP/1 Python迁入software/core六个目录，展开连写逻辑、补中文职责与步骤注释。独立参数解析及视频线程入口，分层构建/验证；旧126锁、926历史源码/脚本、测试正文和完整失败证据保持。当前demo链接新核心，源码/文档迁移前后身份另存，不回写原报告。

代理实际执行11组本机既有检查器、CSI/预处理/像素新旧逐位对照、56步FPAI构建。ARM15头/189厂商身份匹配；一条私有重载未使用警告在旧源码重现。Lite CPU107/12注册/22输出/59600 FP32逐位，272.59秒未延长原300秒预算；三窗口2Hz全部输入、预处理、分数和姿态逐位原参考，354编码/294 GUI解码，全3来源/42关节及完整原码流核验通过。正常drain-LAST/两STREAMOFF、join后Engine销毁、进程/端口回收、BOOTSDK内核同，规整0，无重启或配置更改。

### 对后续开发的参考

[核心导读](software/core/README.md)给出数据流、最小接口、线程/所有权与阅读顺序；新构建标签demo-refactor-20261013-r1。旧工作区原环境和参考经身份核对恢复，仅复制需要的数据，旧目录不写入。维护当前源码从software/core进入；历史文件供旧包追溯，单目标不能混编。[ADR_47](ADR/ADR_47.md)／[验证与完整证据](tools/pose-v1/evidence/core-refactor-20261013-r1/README.md)。本轮不运行60窗口，旧DATA排查继续暂停；严格5Hz、长期、永久首启动及HDMI仍未验收，83/100保持。

'''
    text = text.replace('# 已完成工作记录\n\n', '# 已完成工作记录\n\n' + entry, 1)
    write(path, text)

    path = ROOT / 'ADR/README.md'
    text = path.read_text(encoding='utf-8')
    row='| [ADR_46](ADR_46.md) | 执行规范、进度、难点与历史过程分开维护 | 文档职责 |'
    text = text.replace(row, row + '\n| [ADR_47](ADR_47.md) | 正式核心目录、可读性重构与CPU107/三窗口回归 | 源码迁移与等价性 |', 1)
    write(path, text)

    path = ROOT / 'REFERENCES.md'
    text = path.read_text(encoding='utf-8')
    text = text.replace('# 比赛开发资料索引与理解记录\n\n', '# 比赛开发资料索引与理解记录\n\n2026-10-13当前源码：[正式核心导读](software/core/README.md)、[重构ADR_47](ADR/ADR_47.md)、[本机/CPU107/三窗口实际证据](tools/pose-v1/evidence/core-refactor-20261013-r1/README.md)。旧源码、协议、SDK及模型保持；以下历史阶段结果保留各自范围，旧DATA排查仍暂停。\n\n', 1)
    write(path, text)

    path = ROOT / 'software/demo/README.md'
    text = path.read_text(encoding='utf-8')
    marker='''## 2026-10-13正式核心重构版本

当前入口使用[software/core](../core/README.md)六个功能目录，旧pose_v1和历史检查器保留。参数解析独立为demo_options，视频网络/绘图/编码线程入口分别封装；公开接口和原运行行为保持。构建仍导出锁定别名，但当前锁显式引用新核心；原锁和路径/哈希映射见[ADR_47](../../ADR/ADR_47.md)。

实际完成：11组本机、ARM构建、Lite CPU107/22输出/59600 FP32逐位，以及三窗口全部原始输入/预处理/分数/姿态逐位旧参考。354编码/294 GUI解码、全3来源/42关节、drain/LAST和回收通过，规整0，身份与内核同。[完整证据](../../tools/pose-v1/evidence/core-refactor-20261013-r1/README.md)。本轮没有60窗口执行；下方2026-10-11旧命令和结果保留为历史。

当前已验证构建为`.local/pose-v1-build/demo-refactor-20261013-r1`，板端为`/tmp/wifi-pose-demo-refactor-20261013-r1`；已完成的运行目录不得再次使用。默认模型来源重新核验为`D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/result/icraft_2024`，配对SHA保持原固定值。

本机执行位置是当前仓库根目录`D:/FPGACompetitionProject`。本轮实际核验的回放环境位于旧受管工作区`C:/Users/cenyongdong/.codex/worktrees/dea3/FPGACompetitionProject/.local/pose-v1-conda/python.exe`，Python3.10.21/NumPy2.2.5/h5py3.16.0；仅使用该既有环境，旧工作区不写入。播放器仍用既有WIFI-densepose。Docker/FPAI及原SDK必须可用，不安装替代版本。

可复核静态身份：`python software/demo/verify_core.py static`。`verify_core.py native --tag`和`build.py --tag`的tag必须是新的唯一值，分别生成本机字节对照与ARM构建，成功退出才通过，任何错误停止并保留日志。

`validate_board.py`用于本轮已批准的一次CPU107→三窗口顺序验证：参数`--build`指定核验通过的构建，`--evidence`指定不存在的证据目录，`--cpu-package/--reference`指定原身份输入和数值参考，`--model-dir`指定同SHA模型，`--viewer-python`指定现有播放器。此入口在身份/Host协议/CPU完整输出门检后才放行三窗口，密码由遮罩窗口在内存中输入，预期CPU及short报告、完整tar/值/日志和清理证据。失败/超时/身份变化立即停止，不自动重试；再次实板运行须先按项目约束确认新阶段与新远端目录，不能重复本轮已完成路径。

## 2026-10-11原演示说明（历史范围）

'''
    text = text.replace('# Wi-Fi 人体三维姿态端到端演示\n\n', '# Wi-Fi 人体三维姿态端到端演示\n\n' + marker, 1)
    write(path, text)

    revisions = []
    for before in sorted(snapshot.rglob('*')):
        if before.is_file():
            relative = before.relative_to(snapshot).as_posix()
            revisions.append({'path': relative, 'before_sha256': sha(before), 'after_sha256': sha(ROOT / relative),
                              'original_snapshot': before.relative_to(ROOT).as_posix()})
    write(E / 'document-revisions.json', json.dumps({'date': '2026-10-13', 'historical_manifests_not_rewritten': True,
                                                  'files': revisions}, indent=2) + '\n')
    print('Current documentation and ADR_47 updated; historical evidence untouched')


if __name__ == '__main__':
    main()
