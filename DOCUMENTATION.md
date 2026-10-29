# 全部 Markdown 文档目录

整理日期：2026-10-29。当前工作区共 **554 份 Markdown**，本目录逐份列出位置、用途和历史属性，包含被 Git 忽略的本机记录、模型说明与交付快照。仅排除 `.git`、虚拟环境和依赖缓存；压缩包内部文件不重复展开。清单对应当前工作区，不代表 Git 克隆自带全部本机资产。

先读[最终项目进度](PROJECT-PROGRESS.md)、[困难最终处置](DIFFICULTIES.md)和[部署／恢复入口](FPGA/hdmi_candidate/RESUME.md)。当前核心见 [src/README](software/pose180_pipeline/src/README.md)。根目录与模块 README 维护当前入口；带日期、包名、PLAN／NEXT 的资料按当时阶段理解，目录名本身不构成执行授权。

## 本次内容同步复核

2026-10-29 再次对全部 554 份 Markdown 做全文状态／路径扫描，并核对现行入口及命中的阶段说明。已补齐自采模型后续实板结果、取消／冻结范围、旧工程版本定位和提交稿的最新演示配置，修复 39 处已知迁移链接或归档路径。历史报告、交付快照和厂商原文保持各自范围，不改写成当前测试结果。

50 轮学习率对照仅有 10 月 27 日启动快照，最终状态未核验，见[训练说明](tools/pose180/STATUS.md)。这项未知已明确记录，不继续沿用“当前正在运行”。本次没有连接设备、训练服务器或重跑测试；核验范围及逐份分类见[本机核验结果](.local/documentation-final-20261029/validation.json)。

## 文档职责

| 文档 | 唯一维护职责 |
|---|---|
| [PROJECT-PROGRESS](PROJECT-PROGRESS.md) | 最终选择、完成程度、项目演进及未验收边界 |
| [DIFFICULTIES](DIFFICULTIES.md) | 全部 53 项 difficulty 的最终处置；已解决表示工程收口，逐项区分修复、替代、缓解和范围收口 |
| [ToDoLists](ToDoLists.md) | 后续可选验证、保留限制与冻结范围 |
| [RESUME](FPGA/hdmi_candidate/RESUME.md) | 最后设备观察、现存部署目录、启动／停止／恢复与备份 |
| [TechDetails](ADR/TechDetails.md) | 当前模块、数据流、接口与所有权；早期 VPU／RTSP 详录另标历史 |
| [ADR 索引](ADR/README.md) | 决策顺序与适用范围，不替代当前版本选择 |
| [Done](Done.md)／[REFERENCES](REFERENCES.md) | 已完成成果与资料理解，保留各自日期和原始结论 |
| [Agents](Agents.md) | 执行规则与授权边界，不用问题跟踪收口扩大操作权限 |

## 引用与归档

当前入口的链接按现存文件核验；历史文档中仍有指向旧附件、旧工作区或冻结快照原位置的引用。未找到的附件不凭空重建、不以新结果替换，也不统一归因于本次清理。下面每份文档的“遗留引用”只表示当前本机找不到的链接目标数量，包含 JSON、日志、源码和 Markdown，不是新增技术故障数量。

- 历史原值和交付包内文档保留；源码迁移后的当前技术说明使用新路径。交付快照与项目侧更新后的说明可能不同，本次没有重打包演示归档。
- 10 月 29 日按用户要求删除的旧采集与部署范围见[清理记录](.local/project-cleanup-20261029-r1/summary.json)。必要远端记录保存在[证据包](.local/project-cleanup-20261029-r1/board-evidence.tar.gz)，不保证每个历史链接都能在其中找到。
- 本次扫描清单与逐条缺失引用见[本机核验结果](.local/documentation-final-20261029/validation.json)。被冻结的旧 Markdown 中相对于原目录的链接不批量重写；正文保留的失败与未验收结论不变。
- “本机”表示当前文件未纳入 Git，交接时需连同对应资产保存；“现行入口”也可能包含明确标记的历史章节。

## 分类导航

| 分类 | 文档数 |
|---|---:|
| 总览、规则与根目录历史 | 10 |
| 当前主工程：说明、接口与分阶段验证 | 28 |
| 部署入口与交付快照 | 18 |
| 架构决策与技术说明 | 54 |
| FPGA、HDMI、构建与诊断 | 63 |
| 模型说明与候选历史 | 7 |
| 提交稿与历史选材 | 2 |
| 工具、采集、训练与模型部署 | 40 |
| 共享核心、旧链与独立支线 | 15 |
| 早期 pose-v1 开发与排查 | 164 |
| 历次原始证据报告 | 59 |
| 本机验证与运行记录 | 66 |
| 冻结的文档历史快照 | 18 |
| 厂商资料（保持原文） | 6 |
| 其它历史工程与日志说明 | 4 |

## 逐份目录

各分类可展开；可用编辑器搜索文件名、问题编号、日期或包名。

<details>
<summary>总览、规则与根目录历史（10 份）</summary>

- [Agents.md](Agents.md) — 项目执行规范（现行入口）
- [ARCHITECTURE-DISCUSSION-20261015.md](ARCHITECTURE-DISCUSSION-20261015.md) — 架构讨论记录与 HDMI 后续实施范围（历史／专题说明；遗留引用 17）
- [DIFFICULTIES.md](DIFFICULTIES.md) — 项目困难与最终处置（现行入口；遗留引用 17）
- [DOCUMENTATION.md](DOCUMENTATION.md) — 全部 Markdown 文档目录（现行入口）
- [Done.md](Done.md) — 已完成工作记录（分阶段记录；遗留引用 144）
- [PROJECT-PROGRESS-before-hdmi-20261017.md](PROJECT-PROGRESS-before-hdmi-20261017.md) — 项目进度总览（历史／专题说明；遗留引用 13）
- [PROJECT-PROGRESS.md](PROJECT-PROGRESS.md) — 项目最终进度（现行入口）
- [README.md](README.md) — Wi-Fi 人体三维姿态演示工程（现行入口）
- [REFERENCES.md](REFERENCES.md) — 比赛开发资料索引与理解记录（分阶段记录；遗留引用 179）
- [ToDoLists.md](ToDoLists.md) — 交付后的后续事项与保留限制（现行入口）

</details>

<details>
<summary>当前主工程：说明、接口与分阶段验证（28 份）</summary>

- [software/pose180_pipeline/board/README.md](software/pose180_pipeline/board/README.md) — 源码已按模块归位（模块／兼容说明）
- [software/pose180_pipeline/control/autostart/README.md](software/pose180_pipeline/control/autostart/README.md) — 四路 CSI 路由器开机服务（模块／兼容说明）
- [software/pose180_pipeline/control/README.md](software/pose180_pipeline/control/README.md) — 启停、输入准备与运行管理（现行入口）
- [software/pose180_pipeline/evidence/20261025/README.md](software/pose180_pipeline/evidence/20261025/README.md) — 2026-10-25阶段归档（历史实测／证据）
- [software/pose180_pipeline/host/README.md](software/pose180_pipeline/host/README.md) — 180-query PC 观察与主机验证（现行入口）
- [software/pose180_pipeline/README.md](software/pose180_pipeline/README.md) — 180-query 演示工程与核心源码（现行入口）
- [software/pose180_pipeline/resident/ADAPTIVE-CSI.md](software/pose180_pipeline/resident/ADAPTIVE-CSI.md) — 实时 CSI 的容错组窗与后台对齐（分阶段记录）
- [software/pose180_pipeline/resident/autostart/README.md](software/pose180_pipeline/resident/autostart/README.md) — 路由器服务源码位置（分阶段记录）
- [software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md](software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md) — 自适应 CSI 输入接入与连续性实板验证（分阶段记录）
- [software/pose180_pipeline/resident/DATASET-DEMO.md](software/pose180_pipeline/resident/DATASET-DEMO.md) — 官方数据集开发验证与视频演示（分阶段记录）
- [software/pose180_pipeline/resident/DATASET-PLAYLIST.md](software/pose180_pipeline/resident/DATASET-PLAYLIST.md) — 三片段顺序演示（2026-10-29）（现行入口）
- [software/pose180_pipeline/resident/DEMO-INPUTS.md](software/pose180_pipeline/resident/DEMO-INPUTS.md) — 双输入演示与源码阅读入口（现行入口）
- [software/pose180_pipeline/resident/FINAL-REVIEW.md](software/pose180_pipeline/resident/FINAL-REVIEW.md) — 核心源码最终审查与双输入整理（分阶段记录）
- [software/pose180_pipeline/resident/KINECT-BOARD-TEST-20261028.md](software/pose180_pipeline/resident/KINECT-BOARD-TEST-20261028.md) — 两模型 TopK=1 安全核心测试（分阶段记录）
- [software/pose180_pipeline/resident/LONG-VALIDATION.md](software/pose180_pipeline/resident/LONG-VALIDATION.md) — r4：自主源端与30分钟联合验证结果（分阶段记录）
- [software/pose180_pipeline/resident/PHASE-CONTINUITY.md](software/pose180_pipeline/resident/PHASE-CONTINUITY.md) — 时间分支连续性修正与离线推理对照（分阶段记录）
- [software/pose180_pipeline/resident/PHASE-PREPROCESS-AUDIT.md](software/pose180_pipeline/resident/PHASE-PREPROCESS-AUDIT.md) — 姿态预处理的相位跳变诊断（分阶段记录）
- [software/pose180_pipeline/resident/PHASE-TRACKING.md](software/pose180_pipeline/resident/PHASE-TRACKING.md) — r8／r9：时间网格跟踪、启动见证与实板复验（分阶段记录）
- [software/pose180_pipeline/resident/PRESENTATION-20261026.md](software/pose180_pipeline/resident/PRESENTATION-20261026.md) — 展示精简、防闪现复验与 PS／PL 滤波测时（分阶段记录）
- [software/pose180_pipeline/resident/README.md](software/pose180_pipeline/resident/README.md) — 常驻演示核心与真实CSI→推理→HDMI（分阶段记录）
- [software/pose180_pipeline/resident/STARTUP-PACKAGE.md](software/pose180_pipeline/resident/STARTUP-PACKAGE.md) — 演示启动包与历史验证（分阶段记录）
- [software/pose180_pipeline/resident/STUTTER-VALIDATION.md](software/pose180_pipeline/resident/STUTTER-VALIDATION.md) — r5：卡顿优化、PC观察与联合长测（分阶段记录）
- [software/pose180_pipeline/resident/TOP3-VALIDATION.md](software/pose180_pipeline/resident/TOP3-VALIDATION.md) — r45复验与Top-3置信度筛选（分阶段记录）
- [software/pose180_pipeline/resident/TX-LEASE.md](software/pose180_pipeline/resident/TX-LEASE.md) — r6：TX持续任务与定期续期（分阶段记录）
- [software/pose180_pipeline/resident/WINDOW-RECOVERY.md](software/pose180_pipeline/resident/WINDOW-RECOVERY.md) — r7：共同窗口诊断与更早软恢复（分阶段记录）
- [software/pose180_pipeline/RESULTS.md](software/pose180_pipeline/RESULTS.md) — 2026-10-25：180-query实测、归档修正与HDMI启动停止（模块／兼容说明）
- [software/pose180_pipeline/src/README.md](software/pose180_pipeline/src/README.md) — 当前核心源码（现行入口）
- [software/pose180_pipeline/tests/README.md](software/pose180_pipeline/tests/README.md) — 离线测试位置（现行入口）

</details>

<details>
<summary>部署入口与交付快照（18 份）</summary>

- [Deliverables/hardware/HDMI_Complete_20261026/board-validation/README.md](Deliverables/hardware/HDMI_Complete_20261026/board-validation/README.md) — HDMI 工程与 HP2 启动复现验证（2026-10-26）（交付时快照；本机）
- [Deliverables/hardware/HDMI_Complete_20261026/README.md](Deliverables/hardware/HDMI_Complete_20261026/README.md) — HDMI 完整源码工程（r26 读帧连接基线）（交付时快照；本机）
- [Deliverables/hardware/HDMI_HP2_r30_Actual_Source_20261026/README.md](Deliverables/hardware/HDMI_HP2_r30_Actual_Source_20261026/README.md) — r30 实际源码工程（供官方检查，2026-10-26）（交付时快照；本机）
- [Deliverables/hardware/HDMI_HP2_r30_Actual_Source_20261026/waveforms/HDMI_HP2_REAL_r30/README.md](Deliverables/hardware/HDMI_HP2_r30_Actual_Source_20261026/waveforms/HDMI_HP2_REAL_r30/README.md) — HDMI／HP2 实板连续波形（2026-10-22，r30）（交付时快照；本机）
- [Deliverables/hardware/HDMI_HP2_r30_BD_Lite_20261026/README.md](Deliverables/hardware/HDMI_HP2_r30_BD_Lite_20261026/README.md) — r30 启动异常：精简 BD／源码／波形查看包（交付时快照；本机）
- [Deliverables/hardware/HDMI_HP2_r30_BD_Lite_20261026/waveforms/HDMI_HP2_REAL_r30/README.md](Deliverables/hardware/HDMI_HP2_r30_BD_Lite_20261026/waveforms/HDMI_HP2_REAL_r30/README.md) — HDMI／HP2 实板连续波形（2026-10-22，r30）（交付时快照；本机）
- [Deliverables/hardware/HDMI_HP2_r30_BD_Review_20261026/README.md](Deliverables/hardware/HDMI_HP2_r30_BD_Review_20261026/README.md) — r30 实际连接 BD 查看工程（交付时快照；本机）
- [Deliverables/hardware/HDMI_HP2_r30_Vivado_20261026/README.md](Deliverables/hardware/HDMI_HP2_r30_Vivado_20261026/README.md) — HDMI / HP2 r30 Vivado工程文件（交付时快照；本机）
- [Deliverables/history/software/pose180-demo-deploy-20261029-r2-DEPLOY.md](Deliverables/history/software/pose180-demo-deploy-20261029-r2-DEPLOY.md) — 部署与演示步骤（交付时快照；本机）
- [Deliverables/history/software/pose180-three-clips-20261029-r1-DEPLOY.md](Deliverables/history/software/pose180-three-clips-20261029-r1-DEPLOY.md) — 部署与演示步骤（交付时快照；本机）
- [Deliverables/history/software/pose180-three-clips-20261029-r2-DEPLOY.md](Deliverables/history/software/pose180-three-clips-20261029-r2-DEPLOY.md) — 部署与演示步骤（交付时快照；本机）
- [Deliverables/pose180-three-clips-20261029-r3-DEPLOY.md](Deliverables/pose180-three-clips-20261029-r3-DEPLOY.md) — 部署与演示步骤（现行入口；本机）
- [Deliverables/pose180-three-clips-20261029-r3/DATASET-PLAYLIST.md](Deliverables/pose180-three-clips-20261029-r3/DATASET-PLAYLIST.md) — 三片段顺序演示（2026-10-29）（交付时快照；本机；遗留引用 2）
- [Deliverables/pose180-three-clips-20261029-r3/DEMO-INPUTS.md](Deliverables/pose180-three-clips-20261029-r3/DEMO-INPUTS.md) — 双输入演示与源码阅读入口（交付时快照；本机；遗留引用 1）
- [Deliverables/pose180-three-clips-20261029-r3/DEPLOY.md](Deliverables/pose180-three-clips-20261029-r3/DEPLOY.md) — 部署与演示步骤（交付时快照；本机）
- [Deliverables/pose180-three-clips-20261029-r3/FINAL-REVIEW.md](Deliverables/pose180-three-clips-20261029-r3/FINAL-REVIEW.md) — 核心源码最终审查与双输入整理（交付时快照；本机；遗留引用 6）
- [Deliverables/pose180-three-clips-20261029-r3/README.md](Deliverables/pose180-three-clips-20261029-r3/README.md) — pose180-three-clips-20261029-r3（交付时快照；本机）
- [Deliverables/pose180-three-clips-20261029-r3/STARTUP-GUIDE.md](Deliverables/pose180-three-clips-20261029-r3/STARTUP-GUIDE.md) — 演示启动包与历史验证（交付时快照；本机；遗留引用 7）

</details>

<details>
<summary>架构决策与技术说明（54 份）</summary>

- [ADR/ADR_00.md](ADR/ADR_00.md) — ADR_00：首版采用 PS 主导的 CSI 回放、混合推理与双路显示架构（决策记录（按适用范围））
- [ADR/ADR_01.md](ADR/ADR_01.md) — ADR_01：以已验证PS/NPU异构方案完成首版闭环，深度性能优化后置（决策记录（按适用范围）；遗留引用 3）
- [ADR/ADR_02.md](ADR/ADR_02.md) — ADR_02：VPU连续内存分配与同进程常驻编码策略（决策记录（按适用范围）；遗留引用 3）
- [ADR/ADR_03.md](ADR/ADR_03.md) — ADR_03：平台、启动介质与可追溯构建（决策记录（按适用范围））
- [ADR/ADR_04.md](ADR/ADR_04.md) — ADR_04：固定部署基线、独立参考与训练旁支隔离（决策记录（按适用范围））
- [ADR/ADR_05.md](ADR/ADR_05.md) — ADR_05：受限CPU适配、融合追溯与每帧完成协议（决策记录（按适用范围））
- [ADR/ADR_06.md](ADR/ADR_06.md) — ADR_06：可解释性能测量与隔离应用接口（决策记录（按适用范围））
- [ADR/ADR_07.md](ADR/ADR_07.md) — ADR_07：视频格式、驱动描述与传输时序的分阶段验证（决策记录（按适用范围））
- [ADR/ADR_08.md](ADR/ADR_08.md) — ADR_08：高内聚模块与在线编码AU桥（决策记录（按适用范围））
- [ADR/ADR_09.md](ADR/ADR_09.md) — ADR_09：在线门检的启动协同与完整来源覆盖（决策记录（按适用范围））
- [ADR/ADR_10.md](ADR/ADR_10.md) — ADR_10：慢客户端发送错误与有界TCP候选（决策记录（按适用范围））
- [ADR/ADR_11.md](ADR/ADR_11.md) — ADR_11：完整CSI网络输入与受保护视频输出的模块接入（决策记录（按适用范围））
- [ADR/ADR_12.md](ADR/ADR_12.md) — ADR_12：TCP与视频并行下输出回归失配的有界取证（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_13.md](ADR/ADR_13.md) — ADR_13：保存优先门检与单次规整恢复验证（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_14.md](ADR/ADR_14.md) — ADR_14：整机单时钟计量与传输、样本身份分离（决策记录（按适用范围））
- [ADR/ADR_15.md](ADR/ADR_15.md) — ADR_15：独立显示子进程与有界拥有值IPC（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_16.md](ADR/ADR_16.md) — ADR 16：前向尖峰定位与有界计量扩展（决策记录（按适用范围））
- [ADR/ADR_17.md](ADR/ADR_17.md) — ADR 17：异构与视频并行时的周期性数据块异常（决策记录（按适用范围）；遗留引用 3）
- [ADR/ADR_18.md](ADR/ADR_18.md) — ADR_18：103次有界计量与独立画面参考（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_19.md](ADR/ADR_19.md) — ADR_19：Host复制快照、元数据校验与生产组完成检查（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_20.md](ADR/ADR_20.md) — ADR_20：有限姿态输出失配与独立取证落盘（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_21.md](ADR/ADR_21.md) — ADR_21：192生产完成观测与连续SDK搬运残留判别（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_22.md](ADR/ADR_22.md) — ADR_22：SDK 拥有双源搬运隔离与编码并发判别（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_23.md](ADR/ADR_23.md) — ADR_23：真实模型复制对象、类型和拥有字节对齐取证（决策记录（按适用范围）；遗留引用 3）
- [ADR/ADR_24.md](ADR/ADR_24.md) — ADR_24：真实类型与动态写入的独立 SDK 搬运对照（决策记录（按适用范围）；遗留引用 3）
- [ADR/ADR_25.md](ADR/ADR_25.md) — ADR_25：公开 PL DDR 分配容量与较高来源位置对照（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_26.md](ADR/ADR_26.md) — ADR_26：真实混合模型移除视频负载的独立对照（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_27.md](ADR/ADR_27.md) — ADR_27：同一程序的模型／合成编码负载对照（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_28.md](ADR/ADR_28.md) — ADR_28：单次编码上下文跨三窗／103生命周期（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_29.md](ADR/ADR_29.md) — ADR_29：单次常驻上下文接入真实拥有骨架画面（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_30.md](ADR/ADR_30.md) — ADR_30：公开 Tensor::read 直写自有 Host 输入暂存（决策记录（按适用范围）；遗留引用 2）
- [ADR/ADR_31.md](ADR/ADR_31.md) — ADR_31：公开read输入桥回接显示子进程、TCP与owned AU（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_32.md](ADR/ADR_32.md) — ADR_32：发送端时钟精度与有界吞吐余量验证（决策记录（按适用范围））
- [ADR/ADR_33.md](ADR/ADR_33.md) — ADR_33：公开read路径的有限姿态失配与最终门检取证缺口（决策记录（按适用范围））
- [ADR/ADR_34.md](ADR/ADR_34.md) — ADR_34：原Gather与ZG上游公开边界观察（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_35.md](ADR/ADR_35.md) — ADR_35：192首次复制返回与CPU使用前Host字节边界（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_36.md](ADR/ADR_36.md) — ADR_36：匹配 AXI 读路径责任边界与独立双模式对照（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_37.md](ADR/ADR_37.md) — ADR_37：真实 NPU 生产者完成契约与最小视图可执行性（决策记录（按适用范围））
- [ADR/ADR_38.md](ADR/ADR_38.md) — ADR_38：真实融合组参数、受限独立参考与模拟部署（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_39.md](ADR/ADR_39.md) — ADR_39：独立19成员物理生产者的部署门与固定四调用（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_40.md](ADR/ADR_40.md) — ADR_40：同身份独立生产者与VPU对照、公开ioctl观察（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_41.md](ADR/ADR_41.md) — ADR_41：reset前分段观察与准备后绝对时隙门检（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_42.md](ADR/ADR_42.md) — ADR_42：独立NPU生产者的SDK自有高地址布局（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_43.md](ADR/ADR_43.md) — ADR_43：单调用公开输出租约与失败后两轮源读证据（决策记录（按适用范围）；遗留引用 1）
- [ADR/ADR_44.md](ADR/ADR_44.md) — ADR_44：调用目录预建与一次性拥有令牌（决策记录（按适用范围））
- [ADR/ADR_45.md](ADR/ADR_45.md) — ADR_45：暂停坏块定位，整合端到端演示（决策记录（按适用范围））
- [ADR/ADR_46.md](ADR/ADR_46.md) — ADR_46：执行规范、进度、难点与历史过程分开维护（决策记录（按适用范围））
- [ADR/ADR_47.md](ADR/ADR_47.md) — ADR_47：正式核心目录与保持行为的可读性重构（决策记录（按适用范围）；遗留引用 8）
- [ADR/ADR_48.md](ADR/ADR_48.md) — ADR_48：共享细化 FP16 候选的有界数值门检（决策记录（按适用范围）；遗留引用 6）
- [ADR/ADR_49.md](ADR/ADR_49.md) — ADR_49：PS／NPU感知、PL HDMI与PC独立3D展示（决策记录（按适用范围））
- [ADR/ADR_50.md](ADR/ADR_50.md) — ADR_50：端到端演示优先、有界缓存与分级自动恢复（决策记录（按适用范围））
- [ADR/ADR_ToBeDiscussed.md](ADR/ADR_ToBeDiscussed.md) — ADR_ToBeDiscussed（历史／专题说明）
- [ADR/README.md](ADR/README.md) — 架构决策与难点归档（现行入口）
- [ADR/TechDetails.md](ADR/TechDetails.md) — Wi-Fi 人体三维姿态项目技术实现汇报（现行入口）

</details>

<details>
<summary>FPGA、HDMI、构建与诊断（63 份）</summary>

- [FPGA/ARCHITECTURE-SCORING-ANALYSIS-20261019.md](FPGA/ARCHITECTURE-SCORING-ANALYSIS-20261019.md) — 面向比赛评分的整体架构与PS PL任务划分分析报告（历史／专题说明）
- [FPGA/CSI-PREPROCESS-VITALS-PROPOSAL-20261018.md](FPGA/CSI-PREPROCESS-VITALS-PROPOSAL-20261018.md) — FPGA输入预处理与心率检测可行性分析及顶层技术方案（历史／专题说明）
- [FPGA/FPGA-WORK-SUMMARY-20261016.md](FPGA/FPGA-WORK-SUMMARY-20261016.md) — FPGA／HDMI工作总结与架构讨论交接（历史／专题说明；遗留引用 7）
- [FPGA/hdmi_candidate/AI-CLOCK-GATE.md](FPGA/hdmi_candidate/AI-CLOCK-GATE.md) — 原厂整机实现后的AI时钟门检（历史／专题说明；遗留引用 4）
- [FPGA/hdmi_candidate/AI-HDMI-JOINT-20261023.md](FPGA/hdmi_candidate/AI-HDMI-JOINT-20261023.md) — AI → HDMI 联合测试状态（2026-10-23）（历史／专题说明）
- [FPGA/hdmi_candidate/AI-PATH-DIAGNOSIS-20261017.md](FPGA/hdmi_candidate/AI-PATH-DIAGNOSIS-20261017.md) — HDMI候选AI／PL-DDR路径诊断与原配置对照（历史／专题说明；遗留引用 1）
- [FPGA/hdmi_candidate/baselines/ps_release_r26/README.md](FPGA/hdmi_candidate/baselines/ps_release_r26/README.md) — 隔离前的实际合格构建基线（历史／专题说明）
- [FPGA/hdmi_candidate/BOARD-PLAN.md](FPGA/hdmi_candidate/BOARD-PLAN.md) — HDMI候选实机阶段执行包（历史／专题说明；遗留引用 1）
- [FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md](FPGA/hdmi_candidate/BOARD-RELEASE-20261016.md) — 参考位流定点豁免与受控板测发布（历史／专题说明；遗留引用 8）
- [FPGA/hdmi_candidate/CANDIDATE-AI-MONITOR-V2.md](FPGA/hdmi_candidate/CANDIDATE-AI-MONITOR-V2.md) — AI被动观测候选v2：受控启动与三窗HDMI执行包（历史／专题说明；遗留引用 8）
- [FPGA/hdmi_candidate/CANDIDATE-AI-READ-V3.md](FPGA/hdmi_candidate/CANDIDATE-AI-READ-V3.md) — 六边界读路径观测v3：受控启动执行草案（历史／专题说明；遗留引用 2）
- [FPGA/hdmi_candidate/CANDIDATE-BOARD-READ-R9.md](FPGA/hdmi_candidate/CANDIDATE-BOARD-READ-R9.md) — r9 AI读路径观测候选：现场有界执行包（历史／专题说明；遗留引用 11）
- [FPGA/hdmi_candidate/CANDIDATE-BOARD-TEST-R5.md](FPGA/hdmi_candidate/CANDIDATE-BOARD-TEST-R5.md) — HDMI r5受控启动与静态实屏执行包（历史／专题说明；遗留引用 4）
- [FPGA/hdmi_candidate/diagnostics/ack_transport_r50/README.md](FPGA/hdmi_candidate/diagnostics/ack_transport_r50/README.md) — Synthetic ACK transport comparison（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/ai_read_monitor.README.md](FPGA/hdmi_candidate/diagnostics/ai_read_monitor.README.md) — 六边界被动读路径观测器（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/README.md](FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/README.md) — r45 同位流、同启动有限消费诊断（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/HP2-CYCLETRACE.md](FPGA/hdmi_candidate/diagnostics/HP2-CYCLETRACE.md) — HP2 双窗口实板采样（r30）（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/mmio32_r46/README.md](FPGA/hdmi_candidate/diagnostics/mmio32_r46/README.md) — r46 offline MMIO32 correction（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/README.md](FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/README.md) — Native RGB565 HDMI renderer（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/native_rgb565_r51/README.md](FPGA/hdmi_candidate/diagnostics/native_rgb565_r51/README.md) — r51 static-background overlap（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/native_rgb565_r53/display/README.md](FPGA/hdmi_candidate/diagnostics/native_rgb565_r53/display/README.md) — r53 single-owner begin/poll HDMI output（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/PROTOCOL-CHECKER-REVIEW-20261023.md](FPGA/hdmi_candidate/diagnostics/PROTOCOL-CHECKER-REVIEW-20261023.md) — 官方资料与 AXI 协议检查 IP 的适用性（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/README.md](FPGA/hdmi_candidate/diagnostics/README.md) — AI数据通路被动观测（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/S01-ISOLATION.md](FPGA/hdmi_candidate/diagnostics/S01-ISOLATION.md) — S01源端隔离对照（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/waveforms-20261022/README.md](FPGA/hdmi_candidate/diagnostics/waveforms-20261022/README.md) — HDMI / PS HP2 实测波形与原始记录（历史／专题说明）
- [FPGA/hdmi_candidate/diagnostics/waveforms-r30-20261022/README.md](FPGA/hdmi_candidate/diagnostics/waveforms-r30-20261022/README.md) — HDMI／HP2 实板连续波形（2026-10-22，r30）（历史／专题说明）
- [FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md) — HDMI启动故障工程排查交接（历史／专题说明）
- [FPGA/hdmi_candidate/HDMI-PS-HP2-OFFICIAL-QUESTIONS-20261022.md](FPGA/hdmi_candidate/HDMI-PS-HP2-OFFICIAL-QUESTIONS-20261022.md) — FMQL30TAI HDMI启动异常技术问题报告（历史／专题说明）
- [FPGA/hdmi_candidate/INTEGRATION.md](FPGA/hdmi_candidate/INTEGRATION.md) — HDMI结构、接入过程与验证边界（历史／专题说明）
- [FPGA/hdmi_candidate/IP-CONTRACT-REVIEW.md](FPGA/hdmi_candidate/IP-CONTRACT-REVIEW.md) — 升级后衍生字段差异审查与有限继续条件（历史／专题说明；遗留引用 5）
- [FPGA/hdmi_candidate/IP-REVISION-PLAN.md](FPGA/hdmi_candidate/IP-REVISION-PLAN.md) — 隔离工程IP修订升级的已批准范围与结果（历史／专题说明；遗留引用 3）
- [FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md](FPGA/hdmi_candidate/JFM-COMPATIBILITY-REVIEW.md) — replace_7z030ai_file的真实作用与当前版本边界（历史／专题说明；遗留引用 2）
- [FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md](FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md) — 原厂流程审查与当前实现入口（历史／专题说明；遗留引用 2）
- [FPGA/hdmi_candidate/PAUSE-REPORT-20261018.md](FPGA/hdmi_candidate/PAUSE-REPORT-20261018.md) — 实时推理 → HDMI 阶段进度与暂停报告（历史／专题说明；遗留引用 10）
- [FPGA/hdmi_candidate/PIN-CONTRACT.md](FPGA/hdmi_candidate/PIN-CONTRACT.md) — Lite板HDMI、参考时钟及按键引脚核对（历史／专题说明；遗留引用 1）
- [FPGA/hdmi_candidate/pose_stabilizer/README.md](FPGA/hdmi_candidate/pose_stabilizer/README.md) — 防闪现后处理与精简硬件：离线结果（历史／专题说明）
- [FPGA/hdmi_candidate/probe_free/README.md](FPGA/hdmi_candidate/probe_free/README.md) — 无探针启动位流与可靠性验证（历史／专题说明）
- [FPGA/hdmi_candidate/probe_free_drain/README.md](FPGA/hdmi_candidate/probe_free_drain/README.md) — 去除诊断、保留异常消费的 HDMI 候选（历史／专题说明）
- [FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md](FPGA/hdmi_candidate/PS-ADAPTATION-STATUS.md) — 30TAI自定义PS原生适配阻塞与恢复入口（历史／专题说明；遗留引用 7）
- [FPGA/hdmi_candidate/R24-RESOURCE-AUDIT.md](FPGA/hdmi_candidate/R24-RESOURCE-AUDIT.md) — r24实际布线检查点资源审计（历史／专题说明）
- [FPGA/hdmi_candidate/README.md](FPGA/hdmi_candidate/README.md) — HDMI模块资料入口（历史／专题说明；遗留引用 1）
- [FPGA/hdmi_candidate/RESUME.md](FPGA/hdmi_candidate/RESUME.md) — 当前设备、部署与恢复入口（现行入口）
- [FPGA/hdmi_candidate/ROUTE2-AUDIT.md](FPGA/hdmi_candidate/ROUTE2-AUDIT.md) — 原厂 Vivado＋JFM／Procise 路径二审查（历史／专题说明；遗留引用 3）
- [FPGA/hdmi_candidate/ROUTE2-BUILD-PLAN.md](FPGA/hdmi_candidate/ROUTE2-BUILD-PLAN.md) — 路径二实施配置与顺序（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/build_ai_read_shared.README.md](FPGA/hdmi_candidate/scripts/build_ai_read_shared.README.md) — 三窗推理→HDMI只读路径观测构建器（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/control_ai_read_startup.README.md](FPGA/hdmi_candidate/scripts/control_ai_read_startup.README.md) — read-v3本机启动监督器（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/package_ai_read_offline.README.md](FPGA/hdmi_candidate/scripts/package_ai_read_offline.README.md) — 读路径观测v3离线打包器（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/package_ai_read_postroute.README.md](FPGA/hdmi_candidate/scripts/package_ai_read_postroute.README.md) — r6离线打包薄适配（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/README-ai-read-r7-offline.md](FPGA/hdmi_candidate/scripts/README-ai-read-r7-offline.md) — r7 离线 bit／ICAP／BOOT 适配候选（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/README-hdmi-reader-idle-r7.md](FPGA/hdmi_candidate/scripts/README-hdmi-reader-idle-r7.md) — HDMI reader r7 isolated full flow（历史／专题说明）
- [FPGA/hdmi_candidate/scripts/review_ai_read_postroute.README.md](FPGA/hdmi_candidate/scripts/review_ai_read_postroute.README.md) — r6独立正式报告门（历史／专题说明）
- [FPGA/hdmi_candidate/sim/tb_generated_axi3_stream.README.md](FPGA/hdmi_candidate/sim/tb_generated_axi3_stream.README.md) — 有限AXI3连续读测试台（历史／专题说明）
- [FPGA/hdmi_candidate/software/AI-READ-MONITOR.md](FPGA/hdmi_candidate/software/AI-READ-MONITOR.md) — 独立AI读路径观测适配与固定DMA探针（历史／专题说明）
- [FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md](FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md) — 实时推理到HDMI启动稳定性暂停汇报（历史／专题说明）
- [FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md](FPGA/hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md) — HDMI修复接入整机与实板验证（历史／专题说明；遗留引用 4）
- [FPGA/hdmi_candidate/TIME-REPORT-20261018.md](FPGA/hdmi_candidate/TIME-REPORT-20261018.md) — 上一轮任务耗时复盘（历史／专题说明；遗留引用 8）
- [FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md](FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md) — 2019.1迁移评估与2018.3备用环境方案（历史／专题说明；遗留引用 5）
- [FPGA/hdmi_validation/PROPOSAL.md](FPGA/hdmi_validation/PROPOSAL.md) — HDMI 候选修正方案（已批准候选阶段，现按用户要求暂停）（历史／专题说明）
- [FPGA/hdmi_validation/README.md](FPGA/hdmi_validation/README.md) — HDMI 独立诊断与行为验证（历史／专题说明）
- [FPGA/lite_led_chaser/README.md](FPGA/lite_led_chaser/README.md) — 悟净 Lite 流水灯全流程验证（历史／专题说明；遗留引用 1）
- [FPGA/lite_led_ip_bridge/README.md](FPGA/lite_led_ip_bridge/README.md) — 悟净 Lite：真实 xlconcat IP 流水灯源码交接（历史／专题说明；遗留引用 1）
- [FPGA/README.md](FPGA/README.md) — FPGA 工程资料入口（现行入口）
- [FPGA/vitals_acf/README.md](FPGA/vitals_acf/README.md) — 心率自相关 PL 核心（历史／专题说明）

</details>

<details>
<summary>模型说明与候选历史（7 份）</summary>

- [model/piw24_kinect_finetune-e13-20261028-r1/README.md](model/piw24_kinect_finetune-e13-20261028-r1/README.md) — 现场微调 epoch13：Icraft 上板预览候选（历史／专题说明；本机）
- [model/piw24_kinect_scratch-e4-20261028-r1/README.md](model/piw24_kinect_scratch-e4-20261028-r1/README.md) — 随机初始化训练 epoch4：Icraft 上板对照候选（历史／专题说明；本机）
- [model/piw24_noscatter-20261014-r3/README.md](model/piw24_noscatter-20261014-r3/README.md) — 完整去ScatterND ONNX：Icraft3.39.0主机转换（历史／专题说明；本机；遗留引用 1）
- [model/piw24_pose180_scratch130-20261027-r1/README.md](model/piw24_pose180_scratch130-20261027-r1/README.md) — 从零初始化训练 epoch130：180-query 转换候选（历史／专题说明；本机）
- [model/piw24_pose180_shared-20261024-r1/README.md](model/piw24_pose180_shared-20261024-r1/README.md) — 180-query共享FP16候选（历史／专题说明；本机）
- [model/piw24_shared-20261015-r1/README.md](model/piw24_shared-20261015-r1/README.md) — 共享细化 Icraft 产物（历史／专题说明；本机；遗留引用 2）
- [model/README.md](model/README.md) — 模型开发产物（现行入口；本机）

</details>

<details>
<summary>提交稿与历史选材（2 份）</summary>

- [Docs/提交资料/官方数据集演示片段清单.md](Docs/%E6%8F%90%E4%BA%A4%E8%B5%84%E6%96%99/%E5%AE%98%E6%96%B9%E6%95%B0%E6%8D%AE%E9%9B%86%E6%BC%94%E7%A4%BA%E7%89%87%E6%AE%B5%E6%B8%85%E5%8D%95.md) — 官方数据集视频演示片段清单（稿件／历史选材；本机）
- [Docs/提交资料/技术文档_第一部分_首版.md](Docs/%E6%8F%90%E4%BA%A4%E8%B5%84%E6%96%99/%E6%8A%80%E6%9C%AF%E6%96%87%E6%A1%A3_%E7%AC%AC%E4%B8%80%E9%83%A8%E5%88%86_%E9%A6%96%E7%89%88.md) — 第一部分 作品概述（稿件／历史选材；本机）

</details>

<details>
<summary>工具、采集、训练与模型部署（40 份）</summary>

- [tools/boot-diagnostics/20261002/MEDIA-TEST-PLAN.md](tools/boot-diagnostics/20261002/MEDIA-TEST-PLAN.md) — 当前 SD 卡/读卡器全容量检测方案（待批准）（历史／专题说明）
- [tools/boot-diagnostics/20261002/new_reader_20261002_191749/RESULTS.md](tools/boot-diagnostics/20261002/new_reader_20261002_191749/RESULTS.md) — 更换绿联读卡器并重新制作后的只读复核（2026-10-02 19:17）（历史／专题说明）
- [tools/boot-diagnostics/20261002/remade_20261002_164505/RESULTS.md](tools/boot-diagnostics/20261002/remade_20261002_164505/RESULTS.md) — 用户重制 SD 卡后的只读复核（2026-10-02 16:45）（历史／专题说明）
- [tools/boot-diagnostics/20261002/RESULTS.md](tools/boot-diagnostics/20261002/RESULTS.md) — Lite SD 启动只读排查（2026-10-02）（历史／专题说明）
- [tools/boot-diagnostics/20261002/user_h2testw_20261002_193901/RESULTS.md](tools/boot-diagnostics/20261002/user_h2testw_20261002_193901/RESULTS.md) — 用户提供 H2testw 结果的分析（历史／专题说明）
- [tools/csi-planning/ROUTER-CSI-FEASIBILITY-20261014.md](tools/csi-planning/ROUTER-CSI-FEASIBILITY-20261014.md) — 路由器替代采集节点：可行性与模型影响（历史／专题说明）
- [tools/csi-planning/RT-AC86U-NEXMON-AUDIT-20261017.md](tools/csi-planning/RT-AC86U-NEXMON-AUDIT-20261017.md) — RT-AC86U芯片版本与Nexmon部署查证（历史／专题说明）
- [tools/kinect/README.md](tools/kinect/README.md) — Kinect v2 采集与微调准备（历史／专题说明；遗留引用 1）
- [tools/mcp-validation/ip-reuse/ANALYSIS.md](tools/mcp-validation/ip-reuse/ANALYSIS.md) — Vivado 现成 IP → Procise：可行性分析（历史／专题说明）
- [tools/mcp-validation/ip-reuse/PLAN.md](tools/mcp-validation/ip-reuse/PLAN.md) — 真实 xlconcat IP 流水灯：已批准试验方案（历史／专题说明）
- [tools/mcp-validation/ip-reuse/RESULTS.md](tools/mcp-validation/ip-reuse/RESULTS.md) — 真实 xlconcat IP → Procise → Lite 实板验证结果（历史／专题说明；遗留引用 1）
- [tools/mcp-validation/led1324/PLAN.md](tools/mcp-validation/led1324/PLAN.md) — LED1→3→2→4：Vivado / Procise MCP 衔接验证方案（历史／专题说明）
- [tools/mcp-validation/led1324/RESULTS.md](tools/mcp-validation/led1324/RESULTS.md) — LED1→3→2→4：当前聊天 Vivado / Procise MCP 验证（历史／专题说明；遗留引用 1）
- [tools/mcp-validation/PLAN.md](tools/mcp-validation/PLAN.md) — Procise / Vivado MCP 验证方案（首版已批准并完成独立验证）（历史／专题说明）
- [tools/mcp-validation/RESULTS.md](tools/mcp-validation/RESULTS.md) — Procise / Vivado MCP 验证记录（历史／专题说明）
- [tools/nexmon/board/README.md](tools/nexmon/board/README.md) — 路由器直接进入开发板：软件候选（历史／专题说明）
- [tools/nexmon/DEPLOYMENT-PLAN.md](tools/nexmon/DEPLOYMENT-PLAN.md) — RT-AC86U 到货后的部署与 CSI 验证方案（历史／专题说明）
- [tools/nexmon/README.md](tools/nexmon/README.md) — RT-AC86U Nexmon 采集状态与恢复入口（历史／专题说明；遗留引用 3）
- [tools/pose180/deploy/RESULTS.md](tools/pose180/deploy/RESULTS.md) — 180-query转换、板端验证与高压测试（历史／专题说明）
- [tools/pose180/PLAN.md](tools/pose180/PLAN.md) — 180-query、无TopK、共享joint decoder修改方案（历史／专题说明）
- [tools/pose180/results/analysis-epoch50-counts-r1/REPORT.md](tools/pose180/results/analysis-epoch50-counts-r1/REPORT.md) — 第50轮：高分候选数量与人数分组分析（历史／专题说明）
- [tools/pose180/results/comparison-100-vs180-epoch50-epoch59/REPORT.md](tools/pose180/results/comparison-100-vs180-epoch50-epoch59/REPORT.md) — 第59轮、50轮180-query与原100-query三组对比（历史／专题说明）
- [tools/pose180/results/comparison-100-vs180-epoch50/REPORT.md](tools/pose180/results/comparison-100-vs180-epoch50/REPORT.md) — 原epoch442的100-query与迁移第50轮180-query对比（历史／专题说明）
- [tools/pose180/results/final-delivery-20261023-r1/comparison/REPORT.md](tools/pose180/results/final-delivery-20261023-r1/comparison/REPORT.md) — 100轮最终最佳第99轮与epoch442、第59轮对比（历史／专题说明）
- [tools/pose180/STATUS.md](tools/pose180/STATUS.md) — 180-query共享模型：训练状态与恢复入口（历史／专题说明）
- [tools/pose180/TRAINING-ANALYSIS-20261027.md](tools/pose180/TRAINING-ANALYSIS-20261027.md) — 180-query从零训练平台期分析与下一轮方案（历史／专题说明）
- [tools/pose26-diff-nodecay/20261004/PLAN.md](tools/pose26-diff-nodecay/20261004/PLAN.md) — 已批准的分化分支零衰减对照实验（2026-10-04）（历史／专题说明）
- [tools/pose26-diff-nodecay/20261004/README.md](tools/pose26-diff-nodecay/20261004/README.md) — 分化分支关闭衰减：10轮从零对照实验（历史／专题说明）
- [tools/pose26-diff-nodecay/20261004/RESULTS.md](tools/pose26-diff-nodecay/20261004/RESULTS.md) — 分化分支零衰减10轮：完成核验与结果（2026-10-04）（历史／专题说明）
- [tools/pose26-scratch/20261004/PLAN.md](tools/pose26-scratch/20261004/PLAN.md) — 26版500轮全新训练：已批准范围（历史／专题说明）
- [tools/pose26-scratch/20261004/README.md](tools/pose26-scratch/20261004/README.md) — 26版pose-only：全新初始化500轮Adam训练（历史／专题说明）
- [tools/pose26-scratch/20261004/STATUS-20261004-0908.md](tools/pose26-scratch/20261004/STATUS-20261004-0908.md) — 500轮从头实验：2026-10-04 09:08检查结果（历史／专题说明）
- [tools/pose26-transfer/20261003/MONITOR.md](tools/pose26-transfer/20261003/MONITOR.md) — 训练结果定时检查（历史／专题说明）
- [tools/pose26-transfer/20261003/PAPER_AUDIT.md](tools/pose26-transfer/20261003/PAPER_AUDIT.md) — TPAMI 2026 姿态路径核对（历史／专题说明）
- [tools/pose26-transfer/20261003/README.md](tools/pose26-transfer/20261003/README.md) — 2026姿态模型：epoch442迁移实验（历史／专题说明）
- [tools/pose26-transfer/20261003/RESULTS.md](tools/pose26-transfer/20261003/RESULTS.md) — 2026姿态迁移：首轮10轮结果（历史／专题说明）
- [tools/pose26-transfer/20261004/PLAN.md](tools/pose26-transfer/20261004/PLAN.md) — 26版姿态模型后续正式训练方案（待用户确认）（历史／专题说明）
- [tools/procise_mcp/README.md](tools/procise_mcp/README.md) — Procise Lite MCP 首版（历史／专题说明）
- [tools/README.md](tools/README.md) — Windows Icraft 独立依赖（历史／专题说明）
- [tools/sd-image-validation/20261003-expand-root-COMMANDS.md](tools/sd-image-validation/20261003-expand-root-COMMANDS.md) — Lite 新 SD 卡根分区扩容命令（2026-10-03）（历史／专题说明）

</details>

<details>
<summary>共享核心、旧链与独立支线（15 份）</summary>

- [software/core/INTERFACES.md](software/core/INTERFACES.md) — 正式核心接口与开发指南（历史／专题说明；遗留引用 1）
- [software/core/pose/README.md](software/core/pose/README.md) — 姿态后处理源码位置（历史／专题说明）
- [software/core/README.md](software/core/README.md) — 核心源码入口（历史／专题说明）
- [software/demo/README.md](software/demo/README.md) — Wi-Fi 人体三维姿态端到端演示（历史／专题说明；遗留引用 1）
- [software/engine_timing/README.md](software/engine_timing/README.md) — Engine推理计时诊断（历史／专题说明；遗留引用 2）
- [software/hdmi_demo/README.md](software/hdmi_demo/README.md) — HDMI独立接入应用（历史／专题说明）
- [software/pc_viewer/README.md](software/pc_viewer/README.md) — PC 三维姿态观察台（历史／专题说明）
- [software/pc_viewer/VALIDATION-20261018.md](software/pc_viewer/VALIDATION-20261018.md) — 60份真实历史结果的连续动作回放（历史／专题说明）
- [software/pose_events/README.md](software/pose_events/README.md) — 纯PS离线动作事件原型（历史／专题说明）
- [software/pose_output/README.md](software/pose_output/README.md) — SDK无关骨架网络输出（历史／专题说明）
- [software/pose_v1/PROTOCOL.md](software/pose_v1/PROTOCOL.md) — 原始 CSI 窗口契约 v1（历史／专题说明）
- [software/pose_v1/README.md](software/pose_v1/README.md) — CSI首版：当前实施状态（2026-10-07）（历史／专题说明）
- [software/vitals/HYBRID-20261026.md](software/vitals/HYBRID-20261026.md) — 心率流式模块与可选 PL 后端（历史／专题说明）
- [software/vitals/README.md](software/vitals/README.md) — 独立心率模块（历史／专题说明）
- [software/vitals/VALIDATION-20261019.md](software/vitals/VALIDATION-20261019.md) — 心率PS参考实现离线验证结果（历史／专题说明）

</details>

<details>
<summary>早期 pose-v1 开发与排查（164 份）</summary>

- [tools/pose-v1/APPLICATION-COMMANDS-20261007.md](tools/pose-v1/APPLICATION-COMMANDS-20261007.md) — 首批生产接口与TCP验证命令（历史／专题说明）
- [tools/pose-v1/APPLICATION-RESULTS-20261007.md](tools/pose-v1/APPLICATION-RESULTS-20261007.md) — E1-A生产接口与E1-B TCP回放结果（2026-10-07）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/AXI-READ-NEXT-20261011.md](tools/pose-v1/AXI-READ-NEXT-20261011.md) — 下一阶段：生产者完成契约与证据交接（历史／专题说明）
- [tools/pose-v1/AXI-READ-RESPONSIBILITY-20261011.md](tools/pose-v1/AXI-READ-RESPONSIBILITY-20261011.md) — 并发坏索引责任证据入口（本机审阅版）（历史／专题说明；遗留引用 3）
- [tools/pose-v1/AXI-READ-RESULTS-20261011.md](tools/pose-v1/AXI-READ-RESULTS-20261011.md) — 匹配 AXI／UDMA 读路径审查与双模式内存对照（历史／专题说明；遗留引用 3）
- [tools/pose-v1/BOUNDED-LOAD-PLAN-20261009.md](tools/pose-v1/BOUNDED-LOAD-PLAN-20261009.md) — 103次低日志有限门检实施（历史／专题说明）
- [tools/pose-v1/BOUNDED-LOAD-RESULTS-20261009.md](tools/pose-v1/BOUNDED-LOAD-RESULTS-20261009.md) — 103次入口实施、门检及真实设备源异常取证（历史／专题说明；遗留引用 8）
- [tools/pose-v1/BOUNDED-MEASUREMENT-DESIGN-20261008.md](tools/pose-v1/BOUNDED-MEASUREMENT-DESIGN-20261008.md) — 更长有界计量入口设计（历史／专题说明）
- [tools/pose-v1/COMBINED-READ-NEXT-20261010.md](tools/pose-v1/COMBINED-READ-NEXT-20261010.md) — 当前恢复入口与最小取证方案（历史／专题说明）
- [tools/pose-v1/COMBINED-READ-RESULTS-20261010.md](tools/pose-v1/COMBINED-READ-RESULTS-20261010.md) — 公开read、显示子进程、TCP与RTSP组合结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/CPU-ADAPTER-BUILD-FIX-20261006.md](tools/pose-v1/CPU-ADAPTER-BUILD-FIX-20261006.md) — CPU候选构建：容器Python前提修正（2026-10-06，已批准并应用）（历史／专题说明）
- [tools/pose-v1/CPU-ADAPTER-COMMANDS.md](tools/pose-v1/CPU-ADAPTER-COMMANDS.md) — CPU候选验证：用户执行命令（2026-10-06修正）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/CPU-ADAPTER-COMPILE-FIX-20261006.md](tools/pose-v1/CPU-ADAPTER-COMPILE-FIX-20261006.md) — CPU候选r1编译问题：源码与日志修正（2026-10-06，已批准并应用）（历史／专题说明）
- [tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md](tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md) — CPU算子注册与最小适配：Lite验收结果（2026-10-06）（历史／专题说明；遗留引用 4）
- [tools/pose-v1/CPU-ADAPTER.md](tools/pose-v1/CPU-ADAPTER.md) — CPU算子注册与最小适配：批准范围及源码交付（2026-10-05）（历史／专题说明；遗留引用 1）
- [tools/pose-v1/CRLF-CHECKSUM-FIX.md](tools/pose-v1/CRLF-CHECKSUM-FIX.md) — 校验清单CRLF问题诊断与最小修正方案（2026-10-05，待批准）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/DEMO-RESULTS-20261011.md](tools/pose-v1/DEMO-RESULTS-20261011.md) — 2026-10-11 端到端演示结果（历史／专题说明；遗留引用 8）
- [tools/pose-v1/DISPLAY-PROCESS-NEXT-20261008.md](tools/pose-v1/DISPLAY-PROCESS-NEXT-20261008.md) — 独立显示子进程后的接续方案（历史／专题说明）
- [tools/pose-v1/DISPLAY-PROCESS-RESULTS-20261008.md](tools/pose-v1/DISPLAY-PROCESS-RESULTS-20261008.md) — 独立显示子进程可行性验证结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/ENVIRONMENT-QUERY-20261005.md](tools/pose-v1/ENVIRONMENT-QUERY-20261005.md) — 独立推理门检：用户环境查询结果（2026-10-05）（历史／专题说明；遗留引用 1）
- [tools/pose-v1/F0-INTEGRATION-PREP-20261007.md](tools/pose-v1/F0-INTEGRATION-PREP-20261007.md) — 实际推理画面接入编码的准备（2026-10-07）（历史／专题说明）
- [tools/pose-v1/FINAL-EVIDENCE-NEXT-20261010.md](tools/pose-v1/FINAL-EVIDENCE-NEXT-20261010.md) — 582上游边界最小取证准备（历史／专题说明）
- [tools/pose-v1/FINAL-EVIDENCE-PLAN-20261010.md](tools/pose-v1/FINAL-EVIDENCE-PLAN-20261010.md) — 最终输出门检取证（历史／专题说明）
- [tools/pose-v1/FINAL-EVIDENCE-RESULTS-20261010.md](tools/pose-v1/FINAL-EVIDENCE-RESULTS-20261010.md) — 最终门检完整保存与晚源取证结果（历史／专题说明）
- [tools/pose-v1/FORWARD-DATA-RECOVERY-NEXT-20261009.md](tools/pose-v1/FORWARD-DATA-RECOVERY-NEXT-20261009.md) — 异常数据块的下一有限取证（历史／专题说明）
- [tools/pose-v1/FORWARD-TRACE-R3-RESULTS-20261009.md](tools/pose-v1/FORWARD-TRACE-R3-RESULTS-20261009.md) — 纯计时与异常Host输入取证结果（历史／专题说明；遗留引用 4）
- [tools/pose-v1/FORWARD-TRACE-RESULTS-20261008.md](tools/pose-v1/FORWARD-TRACE-RESULTS-20261008.md) — 前向尖峰诊断首轮结果（历史／专题说明；遗留引用 3）
- [tools/pose-v1/FULL-FLOW-PLAN-20261007.md](tools/pose-v1/FULL-FLOW-PLAN-20261007.md) — 首版全流程接入计划（2026-10-07）（历史／专题说明；遗留引用 1）
- [tools/pose-v1/H0-INTEGRATION-AUDIT-20261007.md](tools/pose-v1/H0-INTEGRATION-AUDIT-20261007.md) — 视频与骨架接入资料核对（H0，2026-10-07）（历史／专题说明）
- [tools/pose-v1/HDMI-STATIC-AUDIT.md](tools/pose-v1/HDMI-STATIC-AUDIT.md) — HDMI配套与720p60静态核对（2026-10-05）（历史／专题说明）
- [tools/pose-v1/HOST-BINDING-REVIEW-20261005.md](tools/pose-v1/HOST-BINDING-REVIEW-20261005.md) — Lite Host参考绑定失败审查（2026-10-05）（历史／专题说明）
- [tools/pose-v1/HOST-REGISTRY-PROBE-PLAN.md](tools/pose-v1/HOST-REGISTRY-PROBE-PLAN.md) — Host注册探针方案（2026-10-05，已批准并执行）（历史／专题说明）
- [tools/pose-v1/HOST-REGISTRY-RESULTS-20261005.md](tools/pose-v1/HOST-REGISTRY-RESULTS-20261005.md) — Lite Host注册探针结果（2026-10-05）（历史／专题说明）
- [tools/pose-v1/HOST-STAGING-FAULT-NEXT-20261009.md](tools/pose-v1/HOST-STAGING-FAULT-NEXT-20261009.md) — 设备源与Host暂存差异后的最小取证准备（历史／专题说明；遗留引用 1）
- [tools/pose-v1/INFERENCE-COMMANDS.md](tools/pose-v1/INFERENCE-COMMANDS.md) — 2024 epoch442 独立混合推理门检：用户执行说明（2026-10-05）（历史／专题说明）
- [tools/pose-v1/INPUT-READ-NEXT-20261010.md](tools/pose-v1/INPUT-READ-NEXT-20261010.md) — 下一接续：公开 read 适配层的组合回归（历史／专题说明）
- [tools/pose-v1/INPUT-READ-RESULTS-20261010.md](tools/pose-v1/INPUT-READ-RESULTS-20261010.md) — 公开 read 输入桥：真实拥有画面有限验证（历史／专题说明；遗留引用 6）
- [tools/pose-v1/INVOCATION-EVIDENCE-INTEGRATION-NEXT-20261009.md](tools/pose-v1/INVOCATION-EVIDENCE-INTEGRATION-NEXT-20261009.md) — 有限输出异常的单帧取证与独立落盘接入契约（历史／专题说明）
- [tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md) — 下一最小定位：192生产完成与连续搬运残留（历史／专题说明）
- [tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md](tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md) — 单帧拥有值与独立落盘接入：本批结果（历史／专题说明；遗留引用 7）
- [tools/pose-v1/LITE-HOST-COMMANDS.md](tools/pose-v1/LITE-HOST-COMMANDS.md) — Lite Host三样本数值参考：用户执行说明（2026-10-05）（历史／专题说明）
- [tools/pose-v1/LIVE-RESULTS-20261008.md](tools/pose-v1/LIVE-RESULTS-20261008.md) — 真实在线串联与网络模块验证结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/MIXED-APPLY-FAILURE-20261006.md](tools/pose-v1/MIXED-APPLY-FAILURE-20261006.md) — apply-r1失败与SSH退出审查（2026-10-06）（历史／专题说明；遗留引用 1）
- [tools/pose-v1/MIXED-BINDING-R2-APPLY-RESULTS.md](tools/pose-v1/MIXED-BINDING-R2-APPLY-RESULTS.md) — 绑定快照r2 apply取证与停止原因（历史／专题说明；遗留引用 3）
- [tools/pose-v1/MIXED-BINDING-R2-BUILD-RESULTS.md](tools/pose-v1/MIXED-BINDING-R2-BUILD-RESULTS.md) — 绑定快照r2构建验收（2026-10-06）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-BINDING-R2-COMMANDS.md](tools/pose-v1/MIXED-BINDING-R2-COMMANDS.md) — 已批准的绑定快照r2执行命令（历史／专题说明）
- [tools/pose-v1/MIXED-BINDING-R2-HOST-RESULTS.md](tools/pose-v1/MIXED-BINDING-R2-HOST-RESULTS.md) — 绑定快照r2 Host回归与离线预检复核（历史／专题说明；遗留引用 3）
- [tools/pose-v1/MIXED-BINDING-R2-MEMORY-RESULTS.md](tools/pose-v1/MIXED-BINDING-R2-MEMORY-RESULTS.md) — 绑定快照r2 SDK内存往返验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-BINDING-R2-OFFLINE-RESULTS.md](tools/pose-v1/MIXED-BINDING-R2-OFFLINE-RESULTS.md) — 绑定快照r2离线门检结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-BINDING-SNAPSHOT-PLAN.md](tools/pose-v1/MIXED-BINDING-SNAPSHOT-PLAN.md) — 绑定追溯最小取证方案（2026-10-06已批准）（历史／专题说明）
- [tools/pose-v1/MIXED-BUILD-REVIEW-20261006.md](tools/pose-v1/MIXED-BUILD-REVIEW-20261006.md) — mixed-r1构建与警告复核（2026-10-06）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-APPLY-RESULTS.md](tools/pose-v1/MIXED-CONTENT-R4-APPLY-RESULTS.md) — r4 apply-only验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-BUILD-RESULTS.md](tools/pose-v1/MIXED-CONTENT-R4-BUILD-RESULTS.md) — r4-final Host内容取证构建验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-COMMANDS.md](tools/pose-v1/MIXED-CONTENT-R4-COMMANDS.md) — 已批准的逐次Host输入内容取证r4命令（历史／专题说明）
- [tools/pose-v1/MIXED-CONTENT-R4-DELIVERY.md](tools/pose-v1/MIXED-CONTENT-R4-DELIVERY.md) — r4逐次输入内容取证源码交付（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-HOST-RESULTS.md](tools/pose-v1/MIXED-CONTENT-R4-HOST-RESULTS.md) — r4 Host回归与内容路径验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-MEMORY-RESULTS.md](tools/pose-v1/MIXED-CONTENT-R4-MEMORY-RESULTS.md) — r4 SDK内存往返验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-OFFLINE-RESULTS.md](tools/pose-v1/MIXED-CONTENT-R4-OFFLINE-RESULTS.md) — r4离线门检验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-CONTENT-R4-ONE-RESULTS.md](tools/pose-v1/MIXED-CONTENT-R4-ONE-RESULTS.md) — r4 308单样本内容取证验收（历史／专题说明；遗留引用 3）
- [tools/pose-v1/MIXED-CONTENT-R4-THREE-FAILURE.md](tools/pose-v1/MIXED-CONTENT-R4-THREE-FAILURE.md) — r4三样本退出1：内容边界分析（历史／专题说明；遗留引用 3）
- [tools/pose-v1/MIXED-CONTENT-R5-READINESS-PLAN.md](tools/pose-v1/MIXED-CONTENT-R5-READINESS-PLAN.md) — r5完成状态与PS/NPU交接取证候选（未批准）（历史／专题说明）
- [tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md](tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md) — 不同输入同输出问题已解决：r6实板工程验收（历史／专题说明；遗留引用 6）
- [tools/pose-v1/MIXED-FRAME-STATE-R6-SOURCE.md](tools/pose-v1/MIXED-FRAME-STATE-R6-SOURCE.md) — 跨帧执行状态修正r6：来源与边界（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-BINDING-FIX-PLAN.md](tools/pose-v1/MIXED-FUSION-BINDING-FIX-PLAN.md) — 正式融合绑定门检修正方案（已批准）（历史／专题说明）
- [tools/pose-v1/MIXED-FUSION-R3-APPLY-RESULTS.md](tools/pose-v1/MIXED-FUSION-R3-APPLY-RESULTS.md) — 正式融合追溯r3 apply验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-R3-BUILD-RESULTS.md](tools/pose-v1/MIXED-FUSION-R3-BUILD-RESULTS.md) — 正式融合追溯r3构建验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-R3-COMMANDS.md](tools/pose-v1/MIXED-FUSION-R3-COMMANDS.md) — 已批准的融合追溯修正r3命令（历史／专题说明）
- [tools/pose-v1/MIXED-FUSION-R3-DELIVERY.md](tools/pose-v1/MIXED-FUSION-R3-DELIVERY.md) — 融合绑定门检修正r3交付（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-R3-HOST-RESULTS.md](tools/pose-v1/MIXED-FUSION-R3-HOST-RESULTS.md) — 正式融合追溯r3 Host回归验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-R3-MEMORY-RESULTS.md](tools/pose-v1/MIXED-FUSION-R3-MEMORY-RESULTS.md) — 正式融合追溯r3 SDK内存往返验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-R3-OFFLINE-RESULTS.md](tools/pose-v1/MIXED-FUSION-R3-OFFLINE-RESULTS.md) — 正式融合追溯r3离线门检验收（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-FUSION-R3-ONE-RESULTS.md](tools/pose-v1/MIXED-FUSION-R3-ONE-RESULTS.md) — r3 308单样本混合计算工程验收（历史／专题说明；遗留引用 4）
- [tools/pose-v1/MIXED-FUSION-R3-THREE-FAILURE.md](tools/pose-v1/MIXED-FUSION-R3-THREE-FAILURE.md) — r3三样本停止：不同输入得到相同输出（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-HOST-RESULTS-20261006.md](tools/pose-v1/MIXED-HOST-RESULTS-20261006.md) — mixed-r1 Host桥回归验收（2026-10-06）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-INPUT-FRESHNESS-DIAGNOSTIC-PLAN.md](tools/pose-v1/MIXED-INPUT-FRESHNESS-DIAGNOSTIC-PLAN.md) — 连续forward输入内容诊断方案（已批准）（历史／专题说明）
- [tools/pose-v1/MIXED-MEMORY-RESULTS-20261006.md](tools/pose-v1/MIXED-MEMORY-RESULTS-20261006.md) — mixed-r1 SDK设备内存往返验收（2026-10-06）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-OFFLINE-RESULTS-20261006.md](tools/pose-v1/MIXED-OFFLINE-RESULTS-20261006.md) — mixed-r1真实参数与PS离线验收（2026-10-06）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/MIXED-VALIDATION-COMMANDS.md](tools/pose-v1/MIXED-VALIDATION-COMMANDS.md) — 混合验证用户执行命令（2026-10-06）（历史／专题说明）
- [tools/pose-v1/MIXED-VALIDATION.md](tools/pose-v1/MIXED-VALIDATION.md) — ONNX参考与PS/NPU混合工程验证（2026-10-06）（历史／专题说明）
- [tools/pose-v1/MODEL-ONLY-NEXT-20261010.md](tools/pose-v1/MODEL-ONLY-NEXT-20261010.md) — 下一最小变量：同一程序的模型／VPU负载对照（历史／专题说明；遗留引用 1）
- [tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md](tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md) — 真实混合模型移除视频负载：本批完成（历史／专题说明；遗留引用 3）
- [tools/pose-v1/MODEL-VPU-NEXT-20261010.md](tools/pose-v1/MODEL-VPU-NEXT-20261010.md) — 下一步：先恢复VPU首次启动条件，再完成长序列对照（历史／专题说明；遗留引用 1）
- [tools/pose-v1/MODEL-VPU-RESULTS-20261010.md](tools/pose-v1/MODEL-VPU-RESULTS-20261010.md) — 同一程序模型／合成VPU对照结果（历史／专题说明；遗留引用 4）
- [tools/pose-v1/MODEL-VPU-RESUME-20261010.md](tools/pose-v1/MODEL-VPU-RESUME-20261010.md) — 同身份模型／VPU对照：待传输恢复（历史／专题说明；遗留引用 3）
- [tools/pose-v1/NEXT-GATE-20261007.md](tools/pose-v1/NEXT-GATE-20261007.md) — E0/N1/P1之后的优先事项（候选方案，未执行）（历史／专题说明）
- [tools/pose-v1/NEXT-GATE.md](tools/pose-v1/NEXT-GATE.md) — 下一步待批准：实际运行FPGA版本查询（历史／专题说明；遗留引用 1）
- [tools/pose-v1/NEXT-PHASE-PLAN-20261006.md](tools/pose-v1/NEXT-PHASE-PLAN-20261006.md) — r6之后：数值扩展、性能基线与正式应用接入计划（历史／专题说明；遗留引用 3）
- [tools/pose-v1/NEXT-VIDEO-PLAN-20261007.md](tools/pose-v1/NEXT-VIDEO-PLAN-20261007.md) — 下一阶段：动态骨架编码、HDMI1080p60与独立RTSP（历史／专题说明）
- [tools/pose-v1/ONLINE-INTEGRATION-NEXT-20261008.md](tools/pose-v1/ONLINE-INTEGRATION-NEXT-20261008.md) — F0-A3真实在线接入入口（历史／专题说明；遗留引用 2）
- [tools/pose-v1/ONNX-REFERENCE-RESULTS-20261006.md](tools/pose-v1/ONNX-REFERENCE-RESULTS-20261006.md) — 三样本ONNX部署参考结果（2026-10-06）（历史／专题说明；遗留引用 1）
- [tools/pose-v1/OWNED-AU-RESULTS-20261008.md](tools/pose-v1/OWNED-AU-RESULTS-20261008.md) — Owned AU桥与网络适配器门检（2026-10-08）（历史／专题说明；遗留引用 5）
- [tools/pose-v1/P2-RESULTS-20261007.md](tools/pose-v1/P2-RESULTS-20261007.md) — Profiling-off单时钟定位与错误消息优化结果（历史／专题说明；遗留引用 7）
- [tools/pose-v1/P2-SINGLE-CLOCK-COMMANDS-20261007.md](tools/pose-v1/P2-SINGLE-CLOCK-COMMANDS-20261007.md) — Profiling-off单时钟候选与lazy-r4验证命令（历史／专题说明）
- [tools/pose-v1/PIPELINE-NEXT-20261008.md](tools/pose-v1/PIPELINE-NEXT-20261008.md) — F0接续门检：启动分配取证→常驻编码器（2026-10-08）（历史／专题说明）
- [tools/pose-v1/PIPELINE-RESULTS-20261008.md](tools/pose-v1/PIPELINE-RESULTS-20261008.md) — 真实推理→骨架→H.264有限接入结果（2026-10-08）（历史／专题说明；遗留引用 3）
- [tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md](tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md) — 下一对照：真实混合引擎运行，移除视频负载（历史／专题说明；遗留引用 1）
- [tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md](tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md) — 公开分配器与较高来源位置对照：本批完成（历史／专题说明；遗留引用 4）
- [tools/pose-v1/PRESAVED-RESULTS-20261008.md](tools/pose-v1/PRESAVED-RESULTS-20261008.md) — 保存优先与一次规整恢复验证结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md](tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md) — 下一诊断：隔离高地址失败后的公开源读证据（历史／专题说明）
- [tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md](tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md) — 独立高地址生产者：有限前帧数据复用失配（历史／专题说明；遗留引用 9）
- [tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md](tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md) — 下一阶段：闭合真实融合组参考，再选择动态读事务观察（历史／专题说明）
- [tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md](tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md) — 生产者完成契约、最小视图与官方部署日志核验（历史／专题说明；遗留引用 5）
- [tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md) — 下一方案：受控SDK双源搬运一致性，先隔离NPU（历史／专题说明）
- [tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md](tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md) — 192公开生产计数诊断结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md](tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md) — 下一诊断：同身份有／无VPU的独立生产者对照（历史／专题说明）
- [tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md](tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md) — 独立真实19成员生产者：部署与四调用结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md](tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md) — 下一控制变量：独立生产者的公开SDK地址布局（历史／专题说明）
- [tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md](tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md) — reset前分段观察与绝对时隙门检结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md](tools/pose-v1/PRODUCER-PREPARED-NEXT-20261011.md) — 下一最小边界：保留首次Host目的张量，失败时公开CPTR快照（历史／专题说明）
- [tools/pose-v1/PRODUCER-PREPARED-RESULTS-20261011.md](tools/pose-v1/PRODUCER-PREPARED-RESULTS-20261011.md) — 目录预建与首次错误/晚源对照结果（历史／专题说明；遗留引用 3）
- [tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md](tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md) — 下一门检：独立真实生产者，先部署再固定四调用（历史／专题说明）
- [tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md](tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md) — 真实生产者参考与mock部署结果（历史／专题说明；遗留引用 4）
- [tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md](tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md) — 下一最小调整：放行前准备调用目录，保留失败源读（历史／专题说明）
- [tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md](tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md) — 单调用输出租约：归还通过，物理晚源读未触发（历史／专题说明；遗留引用 6）
- [tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md](tools/pose-v1/PRODUCER-VPU-NEXT-20261011.md) — 下一诊断：分解reset前空档并守住绝对时隙（历史／专题说明）
- [tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md](tools/pose-v1/PRODUCER-VPU-RESULTS-20261011.md) — 独立真实生产者与VPU对照结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/PROJECT-STATUS-AND-NEXT-20261008.md](tools/pose-v1/PROJECT-STATUS-AND-NEXT-20261008.md) — 当前项目进度与后续方案（2026-10-08）（历史／专题说明；遗留引用 2）
- [tools/pose-v1/READ-PHASE-NEXT-20261011.md](tools/pose-v1/READ-PHASE-NEXT-20261011.md) — 下一阶段：匹配AXI读取实现与共享暂存责任（历史／专题说明）
- [tools/pose-v1/READ-PHASE-RESULTS-20261011.md](tools/pose-v1/READ-PHASE-RESULTS-20261011.md) — 首次复制返回与CPU使用前Host快照：本轮结果（历史／专题说明；遗留引用 3）
- [tools/pose-v1/README.md](tools/pose-v1/README.md) — 首版实施工具与证据（历史／专题说明；遗留引用 24）
- [tools/pose-v1/REFERENCE-NEXT-PLAN.md](tools/pose-v1/REFERENCE-NEXT-PLAN.md) — 数值参考执行路线与依赖预览方案（2026-10-05，B已批准，ORT预览待批准）（历史／专题说明）
- [tools/pose-v1/RENDER-COMMANDS-20261007.md](tools/pose-v1/RENDER-COMMANDS-20261007.md) — 渲染与只读视频核对命令（历史／专题说明）
- [tools/pose-v1/RENDER-RESULTS-20261007.md](tools/pose-v1/RENDER-RESULTS-20261007.md) — E1-C骨架渲染与V0配套核对结果（2026-10-07）（历史／专题说明；遗留引用 6）
- [tools/pose-v1/RESIDENT-RESULTS-20261008.md](tools/pose-v1/RESIDENT-RESULTS-20261008.md) — 同进程有限常驻工作者结果（2026-10-08）（历史／专题说明；遗留引用 5）
- [tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md](tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md) — 下一单因素：常驻上下文中的真实拥有画面（历史／专题说明；遗留引用 1）
- [tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md](tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md) — 单次常驻生命周期结果（2026-10-10）（历史／专题说明；遗留引用 5）
- [tools/pose-v1/RESULTS-300.md](tools/pose-v1/RESULTS-300.md) — 300份真实CSI门检与25122301运行身份核验（2026-10-04）（历史／专题说明；遗留引用 10）
- [tools/pose-v1/RESUME-20261006.md](tools/pose-v1/RESUME-20261006.md) — 唤醒恢复入口（2026-10-06）（历史／专题说明；遗留引用 3）
- [tools/pose-v1/RESUME-PICTURE-20261010.md](tools/pose-v1/RESUME-PICTURE-20261010.md) — 真实拥有画面阶段：用户暂停恢复入口（历史／专题说明；遗留引用 9）
- [tools/pose-v1/RESUME-VIDEO-20261007.md](tools/pose-v1/RESUME-VIDEO-20261007.md) — 视频任务暂停与恢复入口（2026-10-07）（历史／专题说明；遗留引用 5）
- [tools/pose-v1/RTSP-RESULTS-20261007.md](tools/pose-v1/RTSP-RESULTS-20261007.md) — 独立RTSP传输、重连与直接播放器结果（2026-10-07）（历史／专题说明；遗留引用 4）
- [tools/pose-v1/RUNTIME-COMMANDS-20261007.md](tools/pose-v1/RUNTIME-COMMANDS-20261007.md) — E0/N1/P1 r2执行与复现命令（2026-10-07）（历史／专题说明）
- [tools/pose-v1/RUNTIME-RESULTS-20261007.md](tools/pose-v1/RUNTIME-RESULTS-20261007.md) — E0/N1/P1运行核心、扩展数值与性能基线结果（2026-10-07）（历史／专题说明；遗留引用 9）
- [tools/pose-v1/SCRATCH-COPY-NEXT-20261010.md](tools/pose-v1/SCRATCH-COPY-NEXT-20261010.md) — 下一定位：真实模型张量与连续复制对象身份（历史／专题说明；遗留引用 1）
- [tools/pose-v1/SCRATCH-COPY-RESULTS-20261010.md](tools/pose-v1/SCRATCH-COPY-RESULTS-20261010.md) — 受控 SDK 双源搬运与编码并发结果（历史／专题说明；遗留引用 4）
- [tools/pose-v1/SDK-MAPPING-AUDIT-20261009.md](tools/pose-v1/SDK-MAPPING-AUDIT-20261009.md) — ARM SDK搬运、同步和映射边界核查（历史／专题说明；遗留引用 1）
- [tools/pose-v1/shared-output-gate/README.md](tools/pose-v1/shared-output-gate/README.md) — 共享细化输出门检（历史／专题说明；遗留引用 2）
- [tools/pose-v1/SOURCE-COVERAGE-PLAN-20261009.md](tools/pose-v1/SOURCE-COVERAGE-PLAN-20261009.md) — 异常读回保留后的有限覆盖与纯计时（历史／专题说明）
- [tools/pose-v1/SOURCE-COVERAGE-RESULTS-20261009.md](tools/pose-v1/SOURCE-COVERAGE-RESULTS-20261009.md) — 异常读回保留后的有限覆盖与纯计时结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/SOURCE-READBACK-R4-RESULTS-20261009.md](tools/pose-v1/SOURCE-READBACK-R4-RESULTS-20261009.md) — r4错误后源读回：实施与有限回归结果（历史／专题说明；遗留引用 6）
- [tools/pose-v1/STAGE-GUARD-NEXT-20261009.md](tools/pose-v1/STAGE-GUARD-NEXT-20261009.md) — 本批后的推进准备（历史／专题说明；遗留引用 1）
- [tools/pose-v1/STAGE-GUARD-PLAN-20261009.md](tools/pose-v1/STAGE-GUARD-PLAN-20261009.md) — 原复制快照与582完成检查：本批执行契约（历史／专题说明）
- [tools/pose-v1/STAGE-GUARD-RESULTS-20261009.md](tools/pose-v1/STAGE-GUARD-RESULTS-20261009.md) — Host快照与582完成检查：实现和有界回归结果（历史／专题说明；遗留引用 5）
- [tools/pose-v1/STARTUP-GUARD-PLAN-20261009.md](tools/pose-v1/STARTUP-GUARD-PLAN-20261009.md) — 三次独立启动回归与SDK映射核查执行契约（历史／专题说明）
- [tools/pose-v1/STARTUP-GUARD-RESULTS-20261009.md](tools/pose-v1/STARTUP-GUARD-RESULTS-20261009.md) — 独立启动回归与有限输出失配结果（历史／专题说明；遗留引用 4）
- [tools/pose-v1/STATUS.md](tools/pose-v1/STATUS.md) — 首版当前状态（2026-10-07，数值验收与P2更新）（历史／专题说明；遗留引用 28）
- [tools/pose-v1/SYSTEM-TIMING-NEXT-20261008.md](tools/pose-v1/SYSTEM-TIMING-NEXT-20261008.md) — 整机计量后的最小修正方案（历史／专题说明）
- [tools/pose-v1/SYSTEM-TIMING-RESULTS-20261008.md](tools/pose-v1/SYSTEM-TIMING-RESULTS-20261008.md) — 有界整机单时钟计量结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/TCP-INTEGRATION-RESULTS-20261008.md](tools/pose-v1/TCP-INTEGRATION-RESULTS-20261008.md) — Guarded接入与完整CSI网络链路验证结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/TCP-RECOVERY-NEXT-20261008.md](tools/pose-v1/TCP-RECOVERY-NEXT-20261008.md) — 首启动恢复与输出失配取证准备（历史／专题说明；遗留引用 2）
- [tools/pose-v1/TENSOR-IDENTITY-NEXT-20261010.md](tools/pose-v1/TENSOR-IDENTITY-NEXT-20261010.md) — 下一定位：真实类型和动态模式 SDK scratch 对照（历史／专题说明；遗留引用 1）
- [tools/pose-v1/TENSOR-IDENTITY-RESULTS-20261010.md](tools/pose-v1/TENSOR-IDENTITY-RESULTS-20261010.md) — 真实模型复制对象与类型取证结果（历史／专题说明；遗留引用 2）
- [tools/pose-v1/TYPED-SCRATCH-NEXT-20261010.md](tools/pose-v1/TYPED-SCRATCH-NEXT-20261010.md) — 下一独立对照：SDK拥有来源的地址位置（历史／专题说明；遗留引用 1）
- [tools/pose-v1/TYPED-SCRATCH-RESULTS-20261010.md](tools/pose-v1/TYPED-SCRATCH-RESULTS-20261010.md) — 真实类型／动态模式／VPU并发独立对照结果（历史／专题说明；遗留引用 3）
- [tools/pose-v1/UPSTREAM-BOUNDARY-NEXT-20261011.md](tools/pose-v1/UPSTREAM-BOUNDARY-NEXT-20261011.md) — 下一阶段：首次read／Host暂存边界定位（历史／专题说明）
- [tools/pose-v1/UPSTREAM-BOUNDARY-RESULTS-20261011.md](tools/pose-v1/UPSTREAM-BOUNDARY-RESULTS-20261011.md) — 原Gather及ZG上游公开边界：本轮结果（历史／专题说明；遗留引用 4）
- [tools/pose-v1/V0-VIDEO-PAIRING-20261007.md](tools/pose-v1/V0-VIDEO-PAIRING-20261007.md) — V0视频配套核对：已确认部分与待确认接口（历史／专题说明；遗留引用 4）
- [tools/pose-v1/VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md](tools/pose-v1/VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md) — 真实骨架编码故障修正与重复验证（2026-10-07）（历史／专题说明；遗留引用 5）
- [tools/pose-v1/VIDEO-SEQUENCE-RESULTS-20261007.md](tools/pose-v1/VIDEO-SEQUENCE-RESULTS-20261007.md) — 真实骨架视频与HDMI配套首批：VPU异常停止，HDMI未写入（历史／专题说明；遗留引用 2）
- [tools/pose-v1/VPU-COMMANDS-20261007.md](tools/pose-v1/VPU-COMMANDS-20261007.md) — 独立H.264有限测试：位置、产物与停止边界（历史／专题说明）
- [tools/pose-v1/VPU-RESULTS-20261007.md](tools/pose-v1/VPU-RESULTS-20261007.md) — V2独立H.264文件编码与主机审查完成（历史／专题说明；遗留引用 7）
- [tools/pose-v1/VPU-STARTUP-RESULTS-20261008.md](tools/pose-v1/VPU-STARTUP-RESULTS-20261008.md) — VPU连续内存取证与启动最小修正（2026-10-08）（历史／专题说明；遗留引用 6）
- [tools/pose-v1/WHOLE-SYSTEM-NEXT-20261008.md](tools/pose-v1/WHOLE-SYSTEM-NEXT-20261008.md) — 完整网络窗口接入之后的门检顺序（历史／专题说明）
- [tools/pose-v1/WINDOWS-HOST-ENV-CHECK.md](tools/pose-v1/WINDOWS-HOST-ENV-CHECK.md) — Windows Host工具定位与用户环境查询（2026-10-05）（历史／专题说明；遗留引用 4）

</details>

<details>
<summary>历次原始证据报告（59 份）</summary>

- [tools/nexmon/evidence/device-20261019-r1/REPORT.md](tools/nexmon/evidence/device-20261019-r1/REPORT.md) — RT-AC86U Nexmon 实机部署与 CSI 验证（历史实测／证据；本机；遗留引用 2）
- [tools/nexmon/evidence/dual-router-20261022-r1/REPORT.md](tools/nexmon/evidence/dual-router-20261022-r1/REPORT.md) — 双RT-AC86U专用发射、300Hz与相位验证（历史实测／证据；本机）
- [tools/nexmon/evidence/fourth-router-20261025-r1/REPORT.md](tools/nexmon/evidence/fourth-router-20261025-r1/REPORT.md) — 第四台RT-AC86U基础CSI接收验证（历史实测／证据；本机；遗留引用 1）
- [tools/nexmon/evidence/intel-phase-20261023-r1/REPORT.md](tools/nexmon/evidence/intel-phase-20261023-r1/REPORT.md) — 论文原始与对齐CSI的只读相位核查（历史实测／证据；本机）
- [tools/nexmon/evidence/multirx-20261025-r1/REPORT.md](tools/nexmon/evidence/multirx-20261025-r1/REPORT.md) — RT-AC86U四机：1发3收及300Hz同事件对齐验证（历史实测／证据；本机）
- [tools/nexmon/evidence/preparation-20261017-r1/REPORT.md](tools/nexmon/evidence/preparation-20261017-r1/REPORT.md) — Nexmon 环境准备与离线验证报告（历史实测／证据）
- [tools/nexmon/evidence/second-router-20261022-r1/REPORT.md](tools/nexmon/evidence/second-router-20261022-r1/REPORT.md) — 第二台RT-AC86U实机兼容与基础CSI接收验证（历史实测／证据；本机；遗留引用 1）
- [tools/nexmon/evidence/third-router-20261023-r1/REPORT.md](tools/nexmon/evidence/third-router-20261023-r1/REPORT.md) — 第三台RT-AC86U基础接收验证（历史实测／证据；本机；遗留引用 1）
- [tools/nexmon/evidence/third300-20261023-r1/REPORT.md](tools/nexmon/evidence/third300-20261023-r1/REPORT.md) — 第三台RT-AC86U的300Hz采样验证（历史实测／证据；本机；遗留引用 3）
- [tools/pose-output/evidence/pc-replay-20261018-r1/REPORT.md](tools/pose-output/evidence/pc-replay-20261018-r1/REPORT.md) — 已保存真实板端结果的TCP与PC 3D回放（历史实测／证据）
- [tools/pose-v1/evidence/ai-hdmi-cold-consumed-20261024-r43/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-cold-consumed-20261024-r43/RESULTS.md) — r43：单次冷启动对照，目标异常未出现（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-consumed-joint-20261024-r41/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-consumed-joint-20261024-r41/RESULTS.md) — r41：同启动异常消费后联合验证，目标事件未出现（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-consumed-joint-20261024-r42/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-consumed-joint-20261024-r42/RESULTS.md) — r42：重复温重启取样，目标异常未出现（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-drain-joint-20261024-r39/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-drain-joint-20261024-r39/RESULTS.md) — r39：启动消费位流下的 AI→HDMI 联合验证（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-joint-20261023-r36/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-joint-20261023-r36/RESULTS.md) — AI → HDMI 联合测试状态（2026-10-23）（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-startup-control-20261024-r44/PLAN.md](tools/pose-v1/evidence/ai-hdmi-startup-control-20261024-r44/PLAN.md) — r44：已授权的启动前置状态有界对照（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-startup-control-20261024-r44/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-startup-control-20261024-r44/RESULTS.md) — r44：无消费版本复现异常，消费版本本次健康、消费0拍（历史实测／证据；本机）
- [tools/pose-v1/evidence/ai-hdmi-timing-20261024-r40/RESULTS.md](tools/pose-v1/evidence/ai-hdmi-timing-20261024-r40/RESULTS.md) — r40：AI→HDMI 90帧有界联动与换帧计时诊断（历史实测／证据；本机）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/REPORT.md](tools/pose-v1/evidence/architecture-output-20261017-r1/REPORT.md) — 新双路展示架构讨论归档（历史实测／证据）
- [tools/pose-v1/evidence/hdmi-ack-transport-20261024-r50/RESULTS.md](tools/pose-v1/evidence/hdmi-ack-transport-20261024-r50/RESULTS.md) — r50：普通网络归档确认耗时对照（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-boot-witness-20261019-r23/PLAN.md](tools/pose-v1/evidence/hdmi-boot-witness-20261019-r23/PLAN.md) — r23离线结果与待批准板测包（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24/PLAN.md](tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24/PLAN.md) — r24：HP2复位协调实现与单次实板结果（包已关闭）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-library-first-20261018-r18/PLAN.md](tools/pose-v1/evidence/hdmi-library-first-20261018-r18/PLAN.md) — r18 单次加载顺序对照（执行完成，已回原BOOT、关闭）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-library-first-20261018-r18/REPORT.md](tools/pose-v1/evidence/hdmi-library-first-20261018-r18/REPORT.md) — r18 加载顺序与PL按键对照结果（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-library-reset-20261019-r22/PLAN.md](tools/pose-v1/evidence/hdmi-library-reset-20261019-r22/PLAN.md) — r22：SDK先加载与故障下SW6复位对照（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-long-git-20261024-r52/RESULTS.md](tools/pose-v1/evidence/hdmi-long-git-20261024-r52/RESULTS.md) — r52：真实启动异常消费后的有限推理/HDMI联动（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-long-native-20261024-r48/PLAN.md](tools/pose-v1/evidence/hdmi-long-native-20261024-r48/PLAN.md) — r48：原生RGB565接回原30Hz长链路（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-long-native-20261024-r48/RESULTS.md](tools/pose-v1/evidence/hdmi-long-native-20261024-r48/RESULTS.md) — r48：原生 RGB565 接入后的首次长测尝试（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-long-native-20261024-r49/PLAN.md](tools/pose-v1/evidence/hdmi-long-native-20261024-r49/PLAN.md) — r49：主机管道权限修正后的单次长测（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-long-native-20261024-r49/RESULTS.md](tools/pose-v1/evidence/hdmi-long-native-20261024-r49/RESULTS.md) — r49：原生RGB565实际联动与30Hz吞吐卡点（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md](tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md) — r53 单 SDK 线程推理与 HDMI 流水调度（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r32/RESULTS.md](tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r32/RESULTS.md) — HP2 原生协议检查实板结果（2026-10-23，r32）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r32/waveforms/cycletrace/README.md](tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r32/waveforms/cycletrace/README.md) — HP2 实板连续波形（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r33/RESULTS.md](tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r33/RESULTS.md) — HP2 再次实板捕获结果（r33，2026-10-23）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r33/waveforms/cycletrace/README.md](tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r33/waveforms/cycletrace/README.md) — HP2 实板连续波形（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/PLAN.md](tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/PLAN.md) — r26 PS／PL释放顺序取证结果（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-readframe-20261023-r34/RESULTS.md](tools/pose-v1/evidence/hdmi-readframe-20261023-r34/RESULTS.md) — HDMI 有限读帧实板结果（r34，2026-10-23）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-render-overlap-20261024-r51/RESULTS.md](tools/pose-v1/evidence/hdmi-render-overlap-20261024-r51/RESULTS.md) — r51：静态底图准备与归档确认重叠（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-render-speed-20261024-r47/RESULTS.md](tools/pose-v1/evidence/hdmi-render-speed-20261024-r47/RESULTS.md) — r47：直接 RGB565 渲染优化（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-reset-ab-20261018-r15/REPORT.md](tools/pose-v1/evidence/hdmi-reset-ab-20261018-r15/REPORT.md) — r15 纯CSR启动样本与回退（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/PLAN.md](tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/PLAN.md) — r20 单次PL按键清零校准（执行完成，已回原BOOT、关闭）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/REPORT.md](tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/REPORT.md) — r20 无SDK按键清零校准结果（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/PLAN.md](tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/PLAN.md) — r21：纠正按键后的r9复位／启动分段对照（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-reset-values-20261018-r19/PLAN.md](tools/pose-v1/evidence/hdmi-reset-values-20261018-r19/PLAN.md) — r19 单次补充复位取证（执行完成、已回原BOOT、关闭）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-reset-values-20261018-r19/REPORT.md](tools/pose-v1/evidence/hdmi-reset-values-20261018-r19/REPORT.md) — r19 单次补充取证结果（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-software-init-20261018-r16/PLAN.md](tools/pose-v1/evidence/hdmi-software-init-20261018-r16/PLAN.md) — r16 同一启动中的SDK库加载／Open对照（待补充批准）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-software-init-20261018-r16/REPORT.md](tools/pose-v1/evidence/hdmi-software-init-20261018-r16/REPORT.md) — r16 原位库加载／Open分段结果（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-startup-20261018-r14/PLAN.md](tools/pose-v1/evidence/hdmi-startup-20261018-r14/PLAN.md) — r14 启动诊断：复用 r9，区分 BOOT 与 Device::Open（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-startup-20261018-r14/REPORT.md](tools/pose-v1/evidence/hdmi-startup-20261018-r14/REPORT.md) — r14：首次捕获故障启动的 Open 前异常（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-startup-combined-20261018-r17/PLAN.md](tools/pose-v1/evidence/hdmi-startup-combined-20261018-r17/PLAN.md) — r17 合并的跨启动诊断（已批准、执行完成、已关闭）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-startup-combined-20261018-r17/REPORT.md](tools/pose-v1/evidence/hdmi-startup-combined-20261018-r17/REPORT.md) — r17 跨启动分段观测结果（历史实测／证据；本机）
- [tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/PLAN.md](tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/PLAN.md) — r25：同r24位流的无按键启动对照（首例异常，包已关闭）（历史实测／证据；本机）
- [tools/pose-v1/evidence/hp2-bounded-drain-20261024-r38/RESULTS.md](tools/pose-v1/evidence/hp2-bounded-drain-20261024-r38/RESULTS.md) — r38：启动异常返回的有界消费实板验证（历史实测／证据；本机）
- [tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md](tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md) — r45：同启动有限消费诊断的物理验收与首次板测（历史实测／证据；本机）
- [tools/pose-v1/evidence/hp2-mmio32-20261024-r46/PLAN.md](tools/pose-v1/evidence/hp2-mmio32-20261024-r46/PLAN.md) — r46：原生单次 MMIO32 修正与有界板测（历史实测／证据；本机）
- [tools/pose-v1/evidence/hp2-mmio32-20261024-r46/RESULTS.md](tools/pose-v1/evidence/hp2-mmio32-20261024-r46/RESULTS.md) — r46 实板结果：真实异常已消费，显示验证未通过（历史实测／证据；本机）
- [tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/RESULTS.md](tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/RESULTS.md) — r37 启动协议诊断：实板异常、源码对照与恢复结果（历史实测／证据；本机；遗留引用 9）
- [tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/waveforms/cycletrace/README.md](tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/waveforms/cycletrace/README.md) — HP2 实板连续波形（历史实测／证据；本机）
- [tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/waveforms/README.md](tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/waveforms/README.md) — HP2 启动异常 r37：原生协议检查实板数据（历史实测／证据；本机）

</details>

<details>
<summary>本机验证与运行记录（66 份）</summary>

- [.local/ai-hdmi-drain-joint-20261024-r39/source/diagnostics/README.md](.local/ai-hdmi-drain-joint-20261024-r39/source/diagnostics/README.md) — README（历史实测／证据；本机；遗留引用 1）
- [.local/ai-hdmi-joint-20261023-r35/source/diagnostics/README.md](.local/ai-hdmi-joint-20261023-r35/source/diagnostics/README.md) — README（历史实测／证据；本机；遗留引用 1）
- [.local/ai-hdmi-joint-20261023-r36/repro-source/diagnostics/README.md](.local/ai-hdmi-joint-20261023-r36/repro-source/diagnostics/README.md) — README（历史实测／证据；本机；遗留引用 1）
- [.local/engine-timing-test-fixtures/synthetic-2d7301ac0d82414eb642d72e9cb3d517/analysis/report.md](.local/engine-timing-test-fixtures/synthetic-2d7301ac0d82414eb642d72e9cb3d517/analysis/report.md) — Engine计时分析（历史实测／证据；本机）
- [.local/engine-timing-test-fixtures/synthetic-bcb42a333fb749a39320906dd0bf74d7/analysis/report.md](.local/engine-timing-test-fixtures/synthetic-bcb42a333fb749a39320906dd0bf74d7/analysis/report.md) — Engine计时分析（历史实测／证据；本机）
- [.local/hdmi-ack-transport-20261024-r50/README.md](.local/hdmi-ack-transport-20261024-r50/README.md) — Synthetic ACK transport comparison（历史实测／证据；本机）
- [.local/hdmi-complete-verify-r2/README.md](.local/hdmi-complete-verify-r2/README.md) — HDMI 完整源码工程（r26 读帧连接基线）（历史实测／证据；本机）
- [.local/hdmi-complete-verify/README.md](.local/hdmi-complete-verify/README.md) — HDMI 完整源码工程（r26 读帧连接基线）（历史实测／证据；本机）
- [.local/hdmi-live-20261017-r3/execute_read_v3.README.md](.local/hdmi-live-20261017-r3/execute_read_v3.README.md) — read-v3显式逐步执行入口（历史实测／证据；本机）
- [.local/hdmi-live-20261017-r3/prepare_remote_read_v3.README.md](.local/hdmi-live-20261017-r3/prepare_remote_read_v3.README.md) — read-v3逐阶段源码生成器（历史实测／证据；本机）
- [.local/hdmi-main-docs-20261024/Done.md](.local/hdmi-main-docs-20261024/Done.md) — 已完成工作记录（历史实测／证据；本机；遗留引用 426）
- [.local/hdmi-main-docs-20261024/PROJECT-PROGRESS.md](.local/hdmi-main-docs-20261024/PROJECT-PROGRESS.md) — 项目进度总览（历史实测／证据；本机；遗留引用 35）
- [.local/hdmi-pipeline-20261024-r53/display/README.md](.local/hdmi-pipeline-20261024-r53/display/README.md) — r53 single-owner begin/poll HDMI output（历史实测／证据；本机）
- [.local/hdmi-render-speed-20261024-r47/native-render/README.md](.local/hdmi-render-speed-20261024-r47/native-render/README.md) — Native RGB565 HDMI renderer（历史实测／证据；本机）
- [.local/hdmi-render-speed-20261024-r47/renderer/CHANGES.md](.local/hdmi-render-speed-20261024-r47/renderer/CHANGES.md) — r47 static background cache（历史实测／证据；本机）
- [.local/hdmi-s01-isolation-20261022-r28/HDMI-PS-HP2-OFFICIAL-QUESTIONS-20261022.md](.local/hdmi-s01-isolation-20261022-r28/HDMI-PS-HP2-OFFICIAL-QUESTIONS-20261022.md) — FMQL30TAI HDMI启动异常技术问题报告（历史实测／证据；本机）
- [.local/hdmi-s01-soak-20261022-r29/HDMI-PS-HP2-OFFICIAL-QUESTIONS-20261022.md](.local/hdmi-s01-soak-20261022-r29/HDMI-PS-HP2-OFFICIAL-QUESTIONS-20261022.md) — FMQL30TAI HDMI启动异常技术问题报告（历史实测／证据；本机）
- [.local/hp2-deferred-consume-20261024-r45/deploy/INTERFACE.md](.local/hp2-deferred-consume-20261024-r45/deploy/INTERFACE.md) — r45 board controller interface（历史实测／证据；本机）
- [.local/hp2-deferred-consume-20261024-r45/gates/INPUT-CONTRACT.md](.local/hp2-deferred-consume-20261024-r45/gates/INPUT-CONTRACT.md) — r45 deferred consumption: collector and pure gate（历史实测／证据；本机）
- [.local/hp2-deferred-consume-20261024-r45/source/diagnostics/README.md](.local/hp2-deferred-consume-20261024-r45/source/diagnostics/README.md) — README（历史实测／证据；本机；遗留引用 1）
- [.local/hp2-mmio32-20261024-r46/README.md](.local/hp2-mmio32-20261024-r46/README.md) — r46 offline MMIO32 correction（历史实测／证据；本机）
- [.local/kinect-calibrated-20261028-r1/COMPARISON.md](.local/kinect-calibrated-20261028-r1/COMPARISON.md) — 现场 Kinect／CSI 两组限时训练结果（历史实测／证据；本机）
- [.local/kinect-csi-direct-20261028-r5/COLLECTION.md](.local/kinect-csi-direct-20261028-r5/COLLECTION.md) — Kinect／CSI 长时动作原始数据（历史实测／证据；本机）
- [.local/kinect-csi-direct-20261028-r6/COLLECTION.md](.local/kinect-csi-direct-20261028-r6/COLLECTION.md) — 含坐姿的新增长时采集（历史实测／证据；本机）
- [.local/kinect-pairing-20261028-r1/PAIRING.md](.local/kinect-pairing-20261028-r1/PAIRING.md) — CSI—Kinect 接收时刻配对（历史实测／证据；本机）
- [.local/nexmon-rtac86u-20261017-r1/nexmon_csi/README.md](.local/nexmon-rtac86u-20261017-r1/nexmon_csi/README.md) — Nexmon Channel State Information Extractor（历史实测／证据；本机）
- [.local/nexmon-rtac86u-20261017-r1/nexmon_csi/utils/makecsiparams/README.md](.local/nexmon-rtac86u-20261017-r1/nexmon_csi/utils/makecsiparams/README.md) — README（历史实测／证据；本机）
- [.local/nexmon-tx-router-20261022-r1/derivative-source-r2/README.md](.local/nexmon-tx-router-20261022-r1/derivative-source-r2/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/nexmon-tx-router-20261022-r1/derivative-source/README.md](.local/nexmon-tx-router-20261022-r1/derivative-source/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/nexmon-tx-router-20261022-r1/source-archive/nexmon_tx_task-main/README.md](.local/nexmon-tx-router-20261022-r1/source-archive/nexmon_tx_task-main/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/pose-v1-build/demo-core-check-20261014-r1/demo/README.md](.local/pose-v1-build/demo-core-check-20261014-r1/demo/README.md) — Wi-Fi 人体三维姿态端到端演示（历史实测／证据；本机；遗留引用 6）
- [.local/pose-v1-build/demo-refactor-20261013-r1/demo/README.md](.local/pose-v1-build/demo-refactor-20261013-r1/demo/README.md) — Wi-Fi 人体三维姿态端到端演示（历史实测／证据；本机；遗留引用 3）
- [.local/pose180-final-core-20261029-r1/source-unpacked/software/core/README.md](.local/pose180-final-core-20261029-r1/source-unpacked/software/core/README.md) — 正式运行核心（历史实测／证据；本机；遗留引用 5）
- [.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/DEMO-INPUTS.md](.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/DEMO-INPUTS.md) — 双输入演示与源码阅读入口（历史实测／证据；本机）
- [.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/FINAL-REVIEW.md](.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/FINAL-REVIEW.md) — 核心源码最终审查与双输入归档（历史实测／证据；本机）
- [.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/KINECT-BOARD-TEST-20261028.md](.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/KINECT-BOARD-TEST-20261028.md) — 两模型 TopK=1 安全核心测试（历史实测／证据；本机）
- [.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md](.local/pose180-final-core-20261029-r1/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机；遗留引用 4）
- [.local/pose180-final-core-20261029-r1/source-unpacked/SOURCE-README.md](.local/pose180-final-core-20261029-r1/source-unpacked/SOURCE-README.md) — 核心源码归档（历史实测／证据；本机）
- [.local/pose180-hdmi-20261025-r2/README.md](.local/pose180-hdmi-20261025-r2/README.md) — pose180 HDMI 新包：已关闭（历史实测／证据；本机）
- [.local/pose180-kinect-board-test-20261028-r1/README.md](.local/pose180-kinect-board-test-20261028-r1/README.md) — 自采模型有限测试（已结束）及原始模型恢复（历史实测／证据；本机）
- [.local/pose180-original-longrun-20261028-r1/README.md](.local/pose180-original-longrun-20261028-r1/README.md) — 原始epoch99长时测试：持续运行（历史实测／证据；本机）
- [.local/pose180-resident-continuous-20261025-r6/firmware-test/derivative/README.md](.local/pose180-resident-continuous-20261025-r6/firmware-test/derivative/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/pose180-resident-continuous-20261025-r6/firmware-test/final-down-status/derivative/README.md](.local/pose180-resident-continuous-20261025-r6/firmware-test/final-down-status/derivative/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/pose180-resident-continuous-20261025-r6/firmware-test/final/derivative/README.md](.local/pose180-resident-continuous-20261025-r6/firmware-test/final/derivative/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/pose180-resident-continuous-20261025-r6/firmware/derivative-source/README.md](.local/pose180-resident-continuous-20261025-r6/firmware/derivative-source/README.md) — Nexmon Scheduled Transmission（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r1/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md](.local/pose180-top1-no-threshold-20261028-r1/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r1/unpacked/pose180-top1-no-threshold-20261028-r1/README.md](.local/pose180-top1-no-threshold-20261028-r1/unpacked/pose180-top1-no-threshold-20261028-r1/README.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r2/source-unpacked/software/core/README.md](.local/pose180-top1-no-threshold-20261028-r2/source-unpacked/software/core/README.md) — 正式运行核心（历史实测／证据；本机；遗留引用 5）
- [.local/pose180-top1-no-threshold-20261028-r2/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md](.local/pose180-top1-no-threshold-20261028-r2/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r2/unpacked/pose180-top1-no-threshold-20261028-r2/README.md](.local/pose180-top1-no-threshold-20261028-r2/unpacked/pose180-top1-no-threshold-20261028-r2/README.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r3/release-before-pre-hardware-check/README.md](.local/pose180-top1-no-threshold-20261028-r3/release-before-pre-hardware-check/README.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r3/source-unpacked/software/core/README.md](.local/pose180-top1-no-threshold-20261028-r3/source-unpacked/software/core/README.md) — 正式运行核心（历史实测／证据；本机；遗留引用 5）
- [.local/pose180-top1-no-threshold-20261028-r3/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md](.local/pose180-top1-no-threshold-20261028-r3/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r3/unpacked/pose180-top1-no-threshold-20261028-r3/README.md](.local/pose180-top1-no-threshold-20261028-r3/unpacked/pose180-top1-no-threshold-20261028-r3/README.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r4/source-unpacked/software/core/README.md](.local/pose180-top1-no-threshold-20261028-r4/source-unpacked/software/core/README.md) — 正式运行核心（历史实测／证据；本机；遗留引用 5）
- [.local/pose180-top1-no-threshold-20261028-r4/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md](.local/pose180-top1-no-threshold-20261028-r4/source-unpacked/software/pose180_pipeline/resident/STARTUP-PACKAGE.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/pose180-top1-no-threshold-20261028-r4/unpacked/pose180-top1-no-threshold-20261028-r4/README.md](.local/pose180-top1-no-threshold-20261028-r4/unpacked/pose180-top1-no-threshold-20261028-r4/README.md) — TopK=1、无置信度阈值启动包（历史实测／证据；本机）
- [.local/procise-mcp-venv/Lib/site-packages/httpcore2-2.13.1.dist-info/licenses/LICENSE.md](.local/procise-mcp-venv/Lib/site-packages/httpcore2-2.13.1.dist-info/licenses/LICENSE.md) — LICENSE（历史实测／证据；本机）
- [.local/procise-mcp-venv/Lib/site-packages/httpx2-2.13.1.dist-info/licenses/LICENSE.md](.local/procise-mcp-venv/Lib/site-packages/httpx2-2.13.1.dist-info/licenses/LICENSE.md) — LICENSE（历史实测／证据；本机）
- [.local/procise-mcp-venv/Lib/site-packages/idna-3.20.dist-info/licenses/LICENSE.md](.local/procise-mcp-venv/Lib/site-packages/idna-3.20.dist-info/licenses/LICENSE.md) — LICENSE（历史实测／证据；本机）
- [.local/procise-mcp-venv/Lib/site-packages/starlette-1.7.0.dist-info/licenses/LICENSE.md](.local/procise-mcp-venv/Lib/site-packages/starlette-1.7.0.dist-info/licenses/LICENSE.md) — LICENSE（历史实测／证据；本机）
- [.local/procise-mcp-venv/Lib/site-packages/uvicorn-0.54.0.dist-info/licenses/LICENSE.md](.local/procise-mcp-venv/Lib/site-packages/uvicorn-0.54.0.dist-info/licenses/LICENSE.md) — LICENSE（历史实测／证据；本机）
- [.local/procise-mcp-venv/Lib/site-packages/win32comext/mapi/NOTICE.md](.local/procise-mcp-venv/Lib/site-packages/win32comext/mapi/NOTICE.md) — Licensing（历史实测／证据；本机；遗留引用 1）
- [.local/r30-relocated/README.md](.local/r30-relocated/README.md) — r30 实际源码工程（供官方检查，2026-10-26）（历史实测／证据；本机）
- [.local/r30-relocated/waveforms/HDMI_HP2_REAL_r30/README.md](.local/r30-relocated/waveforms/HDMI_HP2_REAL_r30/README.md) — HDMI／HP2 实板连续波形（2026-10-22，r30）（历史实测／证据；本机）
- [.local/router-autostart-20261025-r1/HANDOFF.md](.local/router-autostart-20261025-r1/HANDOFF.md) — READY — router autostart verified（历史实测／证据；本机）

</details>

<details>
<summary>冻结的文档历史快照（18 份）</summary>

- [ADR/history/20261013/adr-index-before.md](ADR/history/20261013/adr-index-before.md) — 整理前历史文档快照（冻结快照）
- [ADR/history/20261013/cpu-sdk.md](ADR/history/20261013/cpu-sdk.md) — CPU适配、SDK审计与初期部署的实施历史（冻结快照）
- [ADR/history/20261013/demo.md](ADR/history/20261013/demo.md) — 端到端演示的实施与验收历史（冻结快照）
- [ADR/history/20261013/difficulties-before.md](ADR/history/20261013/difficulties-before.md) — 整理前历史文档快照（冻结快照；遗留引用 18）
- [ADR/history/20261013/mixed-inference.md](ADR/history/20261013/mixed-inference.md) — 正式混合推理接入与帧状态的实施历史（冻结快照）
- [ADR/history/20261013/platform-tools.md](ADR/history/20261013/platform-tools.md) — 平台、启动介质与本机工具的历史（冻结快照）
- [ADR/history/20261013/progress-before.md](ADR/history/20261013/progress-before.md) — 整理前历史文档快照（冻结快照；遗留引用 53）
- [ADR/history/20261013/read-diagnostics.md](ADR/history/20261013/read-diagnostics.md) — NPU生产者与首次读取异常的取证历史（冻结快照）
- [ADR/history/20261013/README.md](ADR/history/20261013/README.md) — 2026-10-13 文档迁存索引（冻结快照）
- [ADR/history/20261013/toolchain-runbook.md](ADR/history/20261013/toolchain-runbook.md) — 本机工具路径与调用方法（历史资料）（冻结快照）
- [ADR/history/20261013/training.md](ADR/history/20261013/training.md) — 训练旁支与检查任务的历史（冻结快照）
- [ADR/history/20261013/video-lifecycle.md](ADR/history/20261013/video-lifecycle.md) — 视频、常驻生命周期与计量的实施历史（冻结快照）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/ADR/README.md](tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/ADR/README.md) — 架构决策与难点归档（冻结快照；遗留引用 56）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/ARCHITECTURE-DISCUSSION-20261015.md](tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/ARCHITECTURE-DISCUSSION-20261015.md) — 架构讨论记录与 HDMI 后续实施范围（冻结快照；遗留引用 30）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/Done.md](tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/Done.md) — 已完成工作记录（冻结快照；遗留引用 382）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/FPGA/README.md](tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/FPGA/README.md) — FPGA工程资料入口（冻结快照；遗留引用 5）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/PROJECT-PROGRESS.md](tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/PROJECT-PROGRESS.md) — 项目进度总览（冻结快照；遗留引用 44）
- [tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/REFERENCES.md](tools/pose-v1/evidence/architecture-output-20261017-r1/before-document-edit/REFERENCES.md) — 比赛开发资料索引与理解记录（冻结快照；遗留引用 424）

</details>

<details>
<summary>厂商资料（保持原文）（6 份）</summary>

- [Docs/26嵌赛开发/fpai_demo_app/deps/modelzoo_utils/C++_API_reference.md](Docs/26%E5%B5%8C%E8%B5%9B%E5%BC%80%E5%8F%91/fpai_demo_app/deps/modelzoo_utils/C%2B%2B_API_reference.md) — C++ API reference（第三方原文；本机；遗留引用 27）
- [Docs/26嵌赛开发/fpai_demo_app/deps/modelzoo_utils/include/C++_API_reference.md](Docs/26%E5%B5%8C%E8%B5%9B%E5%BC%80%E5%8F%91/fpai_demo_app/deps/modelzoo_utils/include/C%2B%2B_API_reference.md) — C++ API reference（第三方原文；本机；遗留引用 1）
- [Docs/26嵌赛开发/fpai_demo_app/deps/modelzoo_utils/include/readme.md](Docs/26%E5%B5%8C%E8%B5%9B%E5%BC%80%E5%8F%91/fpai_demo_app/deps/modelzoo_utils/include/readme.md) — Modelzoo_utils（第三方原文；本机；遗留引用 1）
- [Docs/26嵌赛开发/fpai_demo_app/deps/modelzoo_utils/pyrtutils/Python_API_reference.md](Docs/26%E5%B5%8C%E8%B5%9B%E5%BC%80%E5%8F%91/fpai_demo_app/deps/modelzoo_utils/pyrtutils/Python_API_reference.md) — Python API reference（第三方原文；本机；遗留引用 2）
- [Docs/26嵌赛开发/fpai_demo_app/deps/modelzoo_utils/readme.md](Docs/26%E5%B5%8C%E8%B5%9B%E5%BC%80%E5%8F%91/fpai_demo_app/deps/modelzoo_utils/readme.md) — Modelzoo_utils（第三方原文；本机）
- [Docs/26嵌赛开发/fpai_demo_app/examples/1_single_input+ai/PLin+SingleNet+HDMI/README.md](Docs/26%E5%B5%8C%E8%B5%9B%E5%BC%80%E5%8F%91/fpai_demo_app/examples/1_single_input%2Bai/PLin%2BSingleNet%2BHDMI/README.md) — PLin+SingleNet+VPU（第三方原文；本机）

</details>

<details>
<summary>其它历史工程与日志说明（4 份）</summary>

- [demo_v1/diagnostics/README.md](demo_v1/diagnostics/README.md) — README（历史／专题说明）
- [demo_v1/README.md](demo_v1/README.md) — demo_v1：论文CSI → Lite融合推理 → 主机实时3D（历史／专题说明）
- [demo_v1/RESULTS.md](demo_v1/RESULTS.md) — demo_v1 实测与恢复入口（历史／专题说明）
- [Logs/README.md](Logs/README.md) — 项目日志（历史／专题说明）

</details>
