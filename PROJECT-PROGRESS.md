# 项目进度总览

FPGA／HDMI当前状态（2026-10-19）：**按用户最新要求，仅更新串口开发记录，板端排查与开发任务暂停，等待明确继续；无后台续作。** 本轮HDMI交接没有连接板卡或执行命令。独立RT-AC86U采集任务按用户明确恢复要求完成，状态见下表，不解除上述暂停。

最后实际板端验证：2026-10-19，r21已执行关闭。**已纠正按键映射并验证观测器复位：sys_rst的F8实际是PL_KEY1／SW6，按后0/2/2→0/0/0；不是PL_KEY2／SW7。** SDK库加载／一次Open／空闲／Close分段均健康，D45本次未复现，根因仍未定位。HDMI长期验证未开展，仍须用户单独批准。[本轮方案与实际结果](tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/PLAN.md)。

原BOOT运行与文件均已恢复，boot_id=b62764f3-133c-4981-8e76-4440a9973365；六SDK／九启动文件符合、FPGA operating、owner为空。用户现已拔网线，仅COM7串口通信；串口只读查询验证同一启动号，登录已退出且端口释放。r21及此前包均已关闭，启动／回退／按键／Open额度不恢复；旧DATA独立暂停。[机器恢复入口](tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/state.json)。

r13新三窗推理→HDMI及现场确认保持已通过；连续推理到HDMI长期验证尚未开始，须用户单独批准。旧DATA暂停，FAT不修，本任务不接入Vivado MCP。

HDMI开发结构与处理过程集中在[INTEGRATION.md](FPGA/hdmi_candidate/INTEGRATION.md)，阶段成果见[Done.md](Done.md)，难点和解决方法见[DIFFICULTIES.md](DIFFICULTIES.md)。

## 当前通信方式与限制

- 板卡与主机网线已断开，当前仅使用**COM7，115200 baud，8N1，无硬件流控，DTR／RTS关闭**。串口登录及只读命令已验证；最后会话已退出登录并释放端口，恢复后先核对串口设备身份和占用情况。
- 串口可用于命令、寄存器和小量日志；本机EDA／交叉编译不依赖板端网络。优先复用板端已有r9和诊断程序；大文件传输、批量原值回传会变慢，现有SSH／SFTP和TCP实时CSI／PC骨架通道目前不可用。不得把串口接通记作这些网络路径已验证。
- 后续是否恢复网口或采用其它传输方式待实际需要再处理；本次不修改通信协议或网络配置。恢复任务须用户明确唤醒，串口可用不增加BOOT／重启／按键／SDK重试授权。

## 当前阶段与验证边界

| 项目 | 当前结果与适用范围 |
|---|---|
| RT-AC86U CSI采集 | 手机配合实测完成；手机热点＋PC客户端最终10秒发2,999包（299.90 Hz），接收16秒12,606个真实CSI包、三链各4,202包且内核丢包0；仍有重复身份／背景帧，稳定300 Hz独立CSI未验收。已导出单节点原始事件供适配，模型／协议不变；原驱动、无线和本机联网恢复，采集／认证关闭。[状态与数据](tools/nexmon/README.md)。 |
| HDMI内存与图案 | 两块实际SDK UDMA帧各4,147,200字节全写全读一致。首次START出现reader fault=2而停止；原因未明。用户明确要求重测后，新进程两幅四色分区依次显示且稳定，错误0；首次失败保留，不称首次启动可靠性修复。 |
| HDMI骨架与生命周期 | 三份此前已验收的真实板端输出，FRAME 1000000→1000001→1000002，各约8秒，全部PL采纳、错误0；用户确认画面可见。板端实际RGB565与本机渲染逐位一致。STOP时reader忙，取得新响应和匹配停止ID、idle且在途位清零后释放双帧。 |
| 模型实时联动 | r13新三窗数值、渲染、HDMI采纳、STOP与释放及现场确认通过；已回原BOOT，包关闭。跨启动偶发故障及严格实时／长期仍未验收。 |
| 原共享模型能力 | 10月15日在当时配置下三窗及30分钟62,945次串行推理数值/内存观察通过；D41时延长尾仍未解。该历史结果不替代当前HDMI候选AI路径验证。 |
| 软件与硬件分工 | PS沿用原骨架投影绘图并适配RGB565；PL完成读帧、扫描与HDMI输出，未将骨架绘图算法迁移到PL。PC独立分支见下一行。 |
| PC骨架网络／3D回放 | 已扩展至60个不同的历史真实选中结果，按原源序列拆为17／43帧；默认43帧约21秒，支持片段切换、原时序及循环。15,360字节TCP／WebSocket一致、11项检查通过；新浏览器自动化复核受工具超时限制，已提供独立数据动画。无上板／新推理／HDMI改动。[实现与验证](software/pc_viewer/README.md)。 |
| 保护与运行状态 | 原BOOT运行与启动文件已恢复；SDK／模型／协议保持，设备无占用，启动包授权关闭。旧DATA暂停。 |

## 未完成与独立暂停项

D44首次HDMI reader故障根因未明；D45偶发HP2返回异常仍待定位，本轮有界新推理到HDMI已通过；严格实时、长期、双路并发均未验收。旧DATA首次坏读定位仍按用户要求暂停，D43 FAT来源问题未修。PC历史真实结果的本地TCP／3D回放已完成，板端实时发布与联合验收仍待实施；不得从历史“下一步”自动恢复。

新的HDMI入口见[software/hdmi_demo](software/hdmi_demo/README.md)；旧VPU／RTSP演示源码与验证保留。旧首版83/100只是历史管理估计，未据新架构重算，不以新增文件或回放次数累加。完整此前状态已原文保存在[实施前快照](PROJECT-PROGRESS-before-hdmi-20261017.md)，历史完成结果继续适用各自范围；[原FPGA交接](FPGA/FPGA-WORK-SUMMARY-20261016.md)不作为本轮最新状态。

## 基线、连接资料与恢复入口


2026-10-19最新完整运行身份见r21最终审计，串口只读启动号核验一致；已回原BOOT。历史r2／r3／r9启动记录只代表各自当时状态；后续操作前重新核验实际身份。

| 对象 | 配置/资料入口 |
|---|---|
| 板子 | 悟净Lite/FMQL30TAI/ZG330；当前串口配置见上。历史SSH地址root@192.168.126.49目前不使用；如恢复网络先重新核验，认证信息仅在运行时内存使用 |
| 工具链 | Windows Procise2025.1.1 temp/SVN32494、Vivado2018.3（D:/vivado18.3/Vivado/2018.3）已就地030ai补丁、PS前端综合通过，Vivado2019.1保留；FPAI是本机交叉编译容器名，ARM64 GCC9.4/CMake3.24.2；Icraft3.39.0 |
| 设备协议 | axi://zg330aiu?npu=0x40000000&dma=0x80000000；device25122301 / icore FMSHZGV3TECH-AID - 24160628 |
| 模型/启动身份 | [TechDetails](ADR/TechDetails.md)及[原演示结果](tools/pose-v1/DEMO-RESULTS-20261011.md)；固定JSON/RAW和BOOT哈希，不在本页重复维护 |
| 历史VPU重构demo | 构建.local/pose-v1-build/demo-refactor-20261013-r1，板端/tmp/wifi-pose-demo-refactor-20261013-r1；3窗口回归通过。[运行说明](software/demo/README.md)、[核心导读](software/core/README.md) |
| 当前恢复点 | [r21状态](tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/state.json)及[最终原BOOT审计](tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/final-audit.json)；当前仅更新文档，任务暂停；新启动另需具体包。 |
| 暂停故障恢复点 | [原下一方案](tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md)；旧next-checkpoint.json已不在当前树，该调查仍独立暂停，不重跑旧Session |
| 历史工具路径/调用示例 | [迁出的工具资料](ADR/history/20261013/toolchain-runbook.md)、[REFERENCES](REFERENCES.md)；旧D:/FPGACompetitionProject路径为历史来源，不直接替代当前工作区 |
| 文档整理记录 | [ADR_46](ADR/ADR_46.md)、[难点索引](DIFFICULTIES.md)、[历史与迁移清单](ADR/history/20261013/README.md) |

历史重构及其CPU107／三窗口回归完成，不从历史完成记录自动追加负载或恢复暂停排查。原重启前/tmp已清空，原失败已本机归档；后续不能使用旧句柄或接续已失败Engine。

本次HDMI文档整理前原文及修订说明见[文档迁移记录](tools/pose-v1/evidence/hdmi-documents-20261018-r1/revision.json)，不回写历史完成清单。
