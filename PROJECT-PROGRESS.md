# 项目进度总览

更新：2026-10-21。最近FPGA／HDMI实板及CSI采集结果均来自10月20日；本次只整理文档，没有重新核验设备运行状态。

**项目已具备固定CSI窗口的板端推理能力，并完成一次三窗新推理到HDMI的有界闭环。当前首要阻塞是候选跨启动偶发HP2异常；真实CSI接入现有模型、板端实时PC发布及双路长期联合演示尚未完成。** 不用历史83/100估计代替新架构验收。

架构按[ADR_49](ADR/ADR_49.md)：PS＋NPU感知，PS绘制本地骨架帧，PL读帧并输出HDMI，PC独立3D展示；未来正式主链停用VPU／RTSP，旧演示保留。

## 已完成内容与验收范围

| 模块 | 已完成 | 当前边界与资料 |
|---|---|---|
| 预处理与混合推理核心 | 固定输入预处理、CPU算子注册和NPU执行链已验证；共享FP16候选按现行数值门禁获阶段认可 | 模型／RAW、数学、SDK及NPU分配保持；范围见[ADR_48](ADR/ADR_48.md)、[核心说明](software/core/README.md) |
| 独立共享模型稳定性 | 10月15日完成30分钟、62,945次串行推理，数值与内存／句柄观察通过 | 有D41时延长尾；该历史配置没有叠加HDMI，不能替代当前联合长期验收。[阶段记录](ADR/ADR_48.md#2026-10-15后续独立实板与30分钟验证) |
| HDMI构建与显示 | 原厂适配工具链、实际bit／BOOT、静态色条、DDR图案、历史骨架、换帧及STOP释放已有验证；r24实际布线与资源审计完成 | 原AI两个最小周期例外保留；首次reader故障D44与跨启动D45未关闭。[工程入口](FPGA/hdmi_candidate/INTEGRATION.md)、[资源审计](FPGA/hdmi_candidate/R24-RESOURCE-AUDIT.md) |
| 新推理到HDMI | r13在一次健康启动中通过四档DMA，再完成3次新推理、3帧采纳、数值检查和现场切换确认 | 每帧约5秒观察，证明短时闭环；不保证每次健康启动之后均长期稳定。[成功方法与证据](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md#31-r13成功运行的实际方法与证据) |
| 启动故障诊断 | 正确SW6清零观测器已确认；r23增加启动历史，r24补PL互联DDR就绪门；r25在SDK前仍复现并回原BOOT | r26仅完成离线PS映射分析和定向方案，尚无新观测RTL／bit／BOOT。[工程师交接](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md) |
| PC骨架传输与3D回放 | 本机C++→TCP→WebSocket→Three.js链路完成；60份历史真实结果按17／43帧分段回放 | 不是板端实时发布或新推理；未做HDMI与PC双路联合验收。[实现与验证](software/pc_viewer/README.md) |
| 真实CSI采集 | 10月20日MT7922在5.745GHz／20MHz完成20秒300Hz受控发包，RT-AC86U收到真实三链CSI并导出原始事件 | 仅一个独立接收节点；独立均匀300Hz、逐帧关联及模型输入适配未验收，model_ready=false。[最新采集结果与恢复记录](tools/nexmon/README.md) |
| 旧VPU／RTSP演示 | 原预采CSI有界网络演示和相关代码、失败证据保留 | 属于历史分支，不再作为新展示主链的必做路径。[历史演示](software/demo/README.md) |

各项成果按发生时配置分别认定；历史回放、一次新推理、启动可靠性和连续长期互不替代。完整阶段记录见[Done.md](Done.md)。

## 主要难点与下一步顺序

- **D45启动稳定性优先。** PS出口异常返回的来源、PS／PL复位释放先后及更早总线活动尚未区分；不能把PL复位有连接、CSR清零或单次Open成功当成修复。
- **D46真实输入适配是另一独立缺口。** 单节点三链不等于三接收节点；64点原始CSI尚未完成物理30子载波映射、标定及同步输入契约，不能直接送入现有模型。
- **D44、D29／D41及联合长期仍保留。** 首次reader失败根因、严格实时和长尾需分别验证；健康启动后的短时显示不等于长期稳定。

详细事实集中在[DIFFICULTIES.md](DIFFICULTIES.md)。可行路线、前置条件和完成标准集中在[ToDoLists.md](ToDoLists.md)：恢复后先做D45被动启动观测；真实CSI质量／契约可独立分析；启动稳定性解决后再回归推理与显示、接入PC，长期验证须用户单独批准。

## 当前状态与执行边界

本轮仅整理文档。FPGA／HDMI故障实施继续暂停；不删减模块，不自动启动离线实现、仿真、构建、部署、BOOT写入／重启或后台续作。此前PS侧诊断授权记录保留，但不解除最新暂停；旧包额度不恢复。旧DATA独立暂停，FAT不修，不接入Vivado MCP。

最后一次FPGA实板核验为r25关闭后的原BOOT运行、启动文件恢复、SDK身份符合及设备无占用，见[最终审计](tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/final-audit.json)。这是历史结果，不能代替接手时的实时核验。CSI分支的路由器／笔记本／主机恢复状态以[采集入口](tools/nexmon/README.md)的最新实测为准。

## 资料与恢复入口

| 用途 | 唯一维护入口 |
|---|---|
| 当前阶段、完成范围与暂停边界 | 本页；执行规则见[Agents.md](Agents.md) |
| 下一步实施顺序及验收条件 | [ToDoLists.md](ToDoLists.md) |
| 稳定问题、已尝试方法及未知项 | [DIFFICULTIES.md](DIFFICULTIES.md) |
| 历史成果与原始结果 | [Done.md](Done.md)，各实验原始归档不回写 |
| HDMI接手、实际DCP／源码／BOOT及复核命令 | [工程师交接](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md)、[恢复入口](FPGA/hdmi_candidate/RESUME.md) |
| 本轮故障恢复状态及下一技术方案 | [r26 state.json](tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/state.json)、[r26 PLAN.md](tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/PLAN.md) |
| 真实CSI、PC展示与模型数值契约 | [Nexmon](tools/nexmon/README.md)、[PC观察台](software/pc_viewer/README.md)、[ADR_48](ADR/ADR_48.md) |
| 设备／SDK身份与原厂工具路线 | [HDMI交接第7节](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md#7-实际工程与产物定位)、[REFERENCES.md](REFERENCES.md) |

旧待办和历史计划只保留当时事实，不构成当前授权。历史原值优先读对应归档／Git历史；不通过重复构建、测试或新增文档数量累加完成度。
