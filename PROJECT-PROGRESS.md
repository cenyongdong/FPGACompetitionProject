# 项目进度总览

最后实际验证：2026-10-18。**r9离线候选与Host计划已通过，用户已回板边，具体新启动包待确认；D45未解决。** 用户2026-10-18明确恢复离线诊断，本轮不接入Vivado MCP。r8从固定r7 native physopt检查点继续，bootstrap104.141秒、route709.532秒、reports301.297秒，工具及各阶段门通过；最终正式门因setup WNS−0.664ns／TNS−55.878ns／379失败端点拒绝，hold+0.029ns。最差抽样为原frame_to_ps视频路径，HDMI next_addr→araddr/CE另有−0.368ns／16逻辑级。原r7父exit1及本轮首bootstrap路径映射失败保留，均未改写为通过。

r9缩短reader的4KiB边界谓词，1048576组合及24组状态机比较通过；完整新综合、约束、布局／物理优化、布线和独立报告已完成。正式55项复核通过，setup +0.030ns、hold +0.023ns、TNS／THS=0，HDMI命令CE最小+0.315ns；2768位观测约束与原厂DRC配置0 Error通过。原两项AI最小周期例外保持，raw_timing_pass仍false，无新增例外。实际bit、Procise ICAP、仅PL变化的BOOT及离线包已生成并验核；候选BOOT SHA256 a0fe608bb4890f941238b1557f2202987116d1e25669f220fcb4b84fec11fb00。原route父exit1、首次默认DRC拒绝和bit哈希超时均保留，补充消费／独立复核不改写原失败。尚未上板，D45未证修复。

用户已回到板边，现场可用；本轮只读SSH核验原BOOT／六SDK／九启动文件符合、FPGA operating、无设备占用，未初始化SDK或执行DMA／推理／HDMI START／BOOT写入／重启。旧DATA仍暂停，旧包启动额度已用完；新的具体BOOT／重启执行包待确认。D45根因未证，全链未打通。 [r8完整结果](tools/pose-v1/evidence/hdmi-live-20261018-r8/REPORT.md)、[r9报告](tools/pose-v1/evidence/hdmi-live-20261018-r9/REPORT.md)、[实际恢复状态](tools/pose-v1/evidence/hdmi-live-20261017-r3/continuation-state.json)。

## 当前阶段与验证边界

| 项目 | 当前结果与适用范围 |
|---|---|
| RT-AC86U CSI采集准备 | 2026-10-17 本地 Nexmon 固件／模块／ARM64 工具实际编译、模块字节复核、14 项解析验证、上游 C 对照及合成回环通过；隔离镜像／卷和离线包已保留。用户先买一台原厂样机，等待到货后身份／ABI门检和无线实测，未连接路由器或改模型／SDK／BOOT；不代表三个接收节点或实时推理通过。[入口与边界](tools/nexmon/README.md)、[实机方案](tools/nexmon/DEPLOYMENT-PLAN.md)。 |
| HDMI内存与图案 | 两块实际SDK UDMA帧各4,147,200字节全写全读一致。首次START出现reader fault=2而停止；原因未明。用户明确要求重测后，新进程两幅四色分区依次显示且稳定，错误0；首次失败保留，不称首次启动可靠性修复。 |
| HDMI骨架与生命周期 | 三份此前已验收的真实板端输出，FRAME 1000000→1000001→1000002，各约8秒，全部PL采纳、错误0；用户确认画面可见。板端实际RGB565与本机渲染逐位一致。STOP时reader忙，取得新响应和匹配停止ID、idle且在途位清零后释放双帧。 |
| 模型实时联动 | r9完整离线构建／正式报告／封装通过，尚未启动新候选；D45阻塞未解除，新推理→HDMI全链待验。 |
| 原共享模型能力 | 10月15日在当时配置下三窗及30分钟62,945次串行推理数值/内存观察通过；D41时延长尾仍未解。该历史结果不替代当前HDMI候选AI路径验证。 |
| 软件与硬件分工 | PS沿用原骨架投影绘图并适配RGB565；PL完成读帧、扫描与HDMI输出。本轮没有把骨架绘图算法迁移到PL，也没有实现PC高质量3D或骨架网络协议。 |
| 保护与运行状态 | 用户已回板边，10月18日只读身份复核通过；旧DATA暂停。新候选启动／负载包待确认，尚未改BOOT或重启。 |

## 未完成与暂停项

D44首次HDMI reader故障根因未明；D45当前候选模型参数上传失败阻塞新推理到HDMI闭环；严格实时、长期、双路并发均未验收。旧DATA首次坏读定位仍按用户要求暂停，D43 FAT来源问题未修。PC展示和骨架传输尚未实施，需按具体任务范围推进；不得从历史“下一步”自动恢复。

新的HDMI入口见[software/hdmi_demo](software/hdmi_demo/README.md)；旧VPU／RTSP演示源码与验证保留。旧首版83/100只是历史管理估计，未据新架构重算，不以新增文件或回放次数累加。完整此前状态已原文保存在[实施前快照](PROJECT-PROGRESS-before-hdmi-20261017.md)，历史完成结果继续适用各自范围；[原FPGA交接](FPGA/FPGA-WORK-SUMMARY-20261016.md)不作为本轮最新状态。

## 基线、连接资料与恢复入口


2026-10-17晚间本轮只读复核见r3/resume-board-readonly，boot_id同原BOOT回退后的9ca535cd；未进行新SDK初始化或DMA／推理。历史回退收尾见r2/fallback-preflight；后续操作前仍须核验实际身份。

| 对象 | 配置/资料入口 |
|---|---|
| 板子 | 悟净Lite/FMQL30TAI/ZG330；SSH root@192.168.126.49，用户已提供认证信息，运行时通过内存输入 |
| 工具链 | Windows Procise2025.1.1 temp/SVN32494、Vivado2018.3（D:/vivado18.3/Vivado/2018.3）已就地030ai补丁、PS前端综合通过，Vivado2019.1保留；FPAI是本机交叉编译容器名，ARM64 GCC9.4/CMake3.24.2；Icraft3.39.0 |
| 设备协议 | axi://zg330aiu?npu=0x40000000&dma=0x80000000；device25122301 / icore FMSHZGV3TECH-AID - 24160628 |
| 模型/启动身份 | [TechDetails](ADR/TechDetails.md)及[演示完成清单](tools/pose-v1/evidence/demo-20261011-r4/completion-review.json)；固定JSON/RAW和BOOT哈希，不在本页重复维护 |
| 当前重构demo | 构建.local/pose-v1-build/demo-refactor-20261013-r1，板端/tmp/wifi-pose-demo-refactor-20261013-r1；3窗口回归通过。[运行说明](software/demo/README.md)、[核心导读](software/core/README.md) |
| 当前恢复点 | [r9报告](tools/pose-v1/evidence/hdmi-live-20261018-r9/REPORT.md)及[状态](tools/pose-v1/evidence/hdmi-live-20261017-r3/continuation-state.json)：离线bit／ICAP／BOOT及完整包已通过；用户已回板边，具体新启动包待批准，原失败保留。 |
| 暂停故障恢复点 | [producer-prepared next-checkpoint](tools/pose-v1/evidence/producer-prepared-20261011-r1/next-checkpoint.json)及[原下一方案](tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md)；未实施，不重跑旧Session |
| 历史工具路径/调用示例 | [迁出的工具资料](ADR/history/20261013/toolchain-runbook.md)、[REFERENCES](REFERENCES.md)；旧D:/FPGACompetitionProject路径为历史来源，不直接替代当前工作区 |
| 文档整理记录 | [ADR_46](ADR/ADR_46.md)、[难点索引](DIFFICULTIES.md)、[历史与迁移清单](ADR/history/20261013/README.md) |

当前重构及已批准CPU107/三窗口验证完成，不继续60窗口或恢复暂停排查。原重启前/tmp已清空，原失败已本机归档；后续不能使用旧句柄或接续已失败Engine。

此前整体暂停交接及只读查询同步的前后原文／SHA见[本次交接修订](tools/pose-v1/evidence/hdmi-live-20261017-r7/documents-place-query-pause-r7-r2/revision.json)。

2026-10-18现场衔接：[r9具体执行包](FPGA/hdmi_candidate/CANDIDATE-BOARD-READ-R9.md)。实际候选、BOOT非PL门、Host计划与当前只读身份均有证据；用户在场不重置旧包已用启动额度。本轮新候选尚未安装／启动，SDK／DMA／新推理及HDMI START未执行。
