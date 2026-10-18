# 项目进度总览

最后实际验证：2026-10-18；本次文档同步未重新连接板卡。**任务已整体暂停，等待用户明确唤醒。** 三窗新推理到HDMI已通过，D45跨启动故障仍未解决；r20无SDK健康基线按一次PL_KEY2后，初始五寄存器仍为ABI=0x41495201、长度104、status/request/response=0/2/2，未观察到归零。不能由此认定按键从未复位或已定位启动根因。[最新暂停汇报](FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md)。

截至r20最终审计，原BOOT运行与文件均恢复，boot_id=0078c99b-70f2-40d8-9445-0bb5002df570；六SDK／九启动文件符合、FPGA operating、owner为空，本批连接／串口／工具结束。r20关闭、剩余额度0。暂停包含离线见证实现、仿真、构建、部署与板测，无后台续作；独立复位见证尚未实现。暂停时现场无仪器；仪器后续到位不自动恢复。[机器恢复入口](tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/pause-state.json)。

r13新三窗推理→HDMI及现场确认保持已通过；连续推理到HDMI长期验证尚未开始，须用户单独批准。旧DATA暂停，FAT不修，本任务不接入Vivado MCP。

HDMI开发结构与处理过程集中在[INTEGRATION.md](FPGA/hdmi_candidate/INTEGRATION.md)，阶段成果见[Done.md](Done.md)，难点和解决方法见[DIFFICULTIES.md](DIFFICULTIES.md)。

## 当前阶段与验证边界

| 项目 | 当前结果与适用范围 |
|---|---|
| RT-AC86U CSI采集准备 | 2026-10-17 本地 Nexmon 固件／模块／ARM64 工具实际编译、模块字节复核、14 项解析验证、上游 C 对照及合成回环通过；隔离镜像／卷和离线包已保留。用户先买一台原厂样机，等待到货后身份／ABI门检和无线实测，未连接路由器或改模型／SDK／BOOT；不代表三个接收节点或实时推理通过。[入口与边界](tools/nexmon/README.md)、[实机方案](tools/nexmon/DEPLOYMENT-PLAN.md)。 |
| HDMI内存与图案 | 两块实际SDK UDMA帧各4,147,200字节全写全读一致。首次START出现reader fault=2而停止；原因未明。用户明确要求重测后，新进程两幅四色分区依次显示且稳定，错误0；首次失败保留，不称首次启动可靠性修复。 |
| HDMI骨架与生命周期 | 三份此前已验收的真实板端输出，FRAME 1000000→1000001→1000002，各约8秒，全部PL采纳、错误0；用户确认画面可见。板端实际RGB565与本机渲染逐位一致。STOP时reader忙，取得新响应和匹配停止ID、idle且在途位清零后释放双帧。 |
| 模型实时联动 | r13新三窗数值、渲染、HDMI采纳、STOP与释放及现场确认通过；已回原BOOT，包关闭。跨启动偶发故障及严格实时／长期仍未验收。 |
| 原共享模型能力 | 10月15日在当时配置下三窗及30分钟62,945次串行推理数值/内存观察通过；D41时延长尾仍未解。该历史结果不替代当前HDMI候选AI路径验证。 |
| 软件与硬件分工 | PS沿用原骨架投影绘图并适配RGB565；PL完成读帧、扫描与HDMI输出，未将骨架绘图算法迁移到PL。PC独立分支见下一行。 |
| PC骨架网络／3D回放 | 已扩展至60个不同的历史真实选中结果，按原源序列拆为17／43帧；默认43帧约21秒，支持片段切换、原时序及循环。15,360字节TCP／WebSocket一致、11项检查通过；新浏览器自动化复核受工具超时限制，已提供独立数据动画。无上板／新推理／HDMI改动。[实现与验证](software/pc_viewer/README.md)。 |
| 保护与运行状态 | 原BOOT运行与启动文件已恢复；SDK／模型／协议保持，设备无占用，启动包授权关闭。旧DATA暂停。 |

## 未完成与暂停项

D44首次HDMI reader故障根因未明；D45偶发HP2返回异常仍待定位，本轮有界新推理到HDMI已通过；严格实时、长期、双路并发均未验收。旧DATA首次坏读定位仍按用户要求暂停，D43 FAT来源问题未修。PC历史真实结果的本地TCP／3D回放已完成，板端实时发布与联合验收仍待实施；不得从历史“下一步”自动恢复。

新的HDMI入口见[software/hdmi_demo](software/hdmi_demo/README.md)；旧VPU／RTSP演示源码与验证保留。旧首版83/100只是历史管理估计，未据新架构重算，不以新增文件或回放次数累加。完整此前状态已原文保存在[实施前快照](PROJECT-PROGRESS-before-hdmi-20261017.md)，历史完成结果继续适用各自范围；[原FPGA交接](FPGA/FPGA-WORK-SUMMARY-20261016.md)不作为本轮最新状态。

## 基线、连接资料与恢复入口


2026-10-18最新运行状态见r20最终只读核验；已回原BOOT。历史r2／r3／r9启动记录只代表各自当时状态；后续操作前重新核验实际身份。

| 对象 | 配置/资料入口 |
|---|---|
| 板子 | 悟净Lite/FMQL30TAI/ZG330；SSH root@192.168.126.49，用户已提供认证信息，运行时通过内存输入 |
| 工具链 | Windows Procise2025.1.1 temp/SVN32494、Vivado2018.3（D:/vivado18.3/Vivado/2018.3）已就地030ai补丁、PS前端综合通过，Vivado2019.1保留；FPAI是本机交叉编译容器名，ARM64 GCC9.4/CMake3.24.2；Icraft3.39.0 |
| 设备协议 | axi://zg330aiu?npu=0x40000000&dma=0x80000000；device25122301 / icore FMSHZGV3TECH-AID - 24160628 |
| 模型/启动身份 | [TechDetails](ADR/TechDetails.md)及[原演示结果](tools/pose-v1/DEMO-RESULTS-20261011.md)；固定JSON/RAW和BOOT哈希，不在本页重复维护 |
| 历史VPU重构demo | 构建.local/pose-v1-build/demo-refactor-20261013-r1，板端/tmp/wifi-pose-demo-refactor-20261013-r1；3窗口回归通过。[运行说明](software/demo/README.md)、[核心导读](software/core/README.md) |
| 当前恢复点 | [暂停汇报](FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md)、[pause-state.json](tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/pause-state.json)及[最终原BOOT审计](tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/final-audit.json)；待用户唤醒。 |
| 暂停故障恢复点 | [原下一方案](tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md)；旧next-checkpoint.json已不在当前树，该调查仍独立暂停，不重跑旧Session |
| 历史工具路径/调用示例 | [迁出的工具资料](ADR/history/20261013/toolchain-runbook.md)、[REFERENCES](REFERENCES.md)；旧D:/FPGACompetitionProject路径为历史来源，不直接替代当前工作区 |
| 文档整理记录 | [ADR_46](ADR/ADR_46.md)、[难点索引](DIFFICULTIES.md)、[历史与迁移清单](ADR/history/20261013/README.md) |

历史重构及其CPU107／三窗口回归完成，不从历史完成记录自动追加负载或恢复暂停排查。原重启前/tmp已清空，原失败已本机归档；后续不能使用旧句柄或接续已失败Engine。

本次HDMI文档整理前原文及修订说明见[文档迁移记录](tools/pose-v1/evidence/hdmi-documents-20261018-r1/revision.json)，不回写历史完成清单。
