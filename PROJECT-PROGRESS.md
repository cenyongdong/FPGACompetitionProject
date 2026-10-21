# 项目进度总览

更新：2026-10-21。r26已取得符合既定时序／DRC范围的实际bit／BOOT；第1次无SDK被动启动复现异常，停止后续候选并安全回原BOOT，包关闭、余额0。D45未解决；当前缺匹配的PS／HP2复位资料，用户将向比赛官方咨询。

**项目已具备固定CSI窗口的板端推理能力，并完成一次三窗新推理到HDMI的有界闭环。当前首要阻塞是候选跨启动偶发HP2异常；真实CSI接入现有模型、板端实时PC发布及双路长期联合演示尚未完成。** 不用历史83/100估计代替新架构验收。

架构按[ADR_49](ADR/ADR_49.md)：PS＋NPU感知，PS绘制本地骨架帧，PL读帧并输出HDMI，PC独立3D展示；未来正式主链停用VPU／RTSP，旧演示保留。

## 已完成内容与验收范围

| 模块 | 已完成 | 当前边界与资料 |
|---|---|---|
| 预处理与混合推理核心 | 固定输入预处理、CPU算子注册和NPU执行链已验证；共享FP16候选按现行数值门禁获阶段认可 | 模型／RAW、数学、SDK及NPU分配保持；范围见[ADR_48](ADR/ADR_48.md)、[核心说明](software/core/README.md) |
| 独立共享模型稳定性 | 10月15日完成30分钟、62,945次串行推理，数值与内存／句柄观察通过 | 有D41时延长尾；该历史配置没有叠加HDMI，不能替代当前联合长期验收。[阶段记录](ADR/ADR_48.md#2026-10-15后续独立实板与30分钟验证) |
| HDMI构建与显示 | 原厂适配工具链、实际bit／BOOT、静态色条、DDR图案、历史骨架、换帧及STOP释放已有验证；r24实际布线与资源审计完成 | 原AI两个最小周期例外保留；首次reader故障D44与跨启动D45未关闭。[工程入口](FPGA/hdmi_candidate/INTEGRATION.md)、[资源审计](FPGA/hdmi_candidate/R24-RESOURCE-AUDIT.md) |
| 新推理到HDMI | r13在一次健康启动中通过四档DMA，再完成3次新推理、3帧采纳、数值检查和现场切换确认 | 每帧约5秒观察，证明短时闭环；不保证每次健康启动之后均长期稳定。[成功方法与证据](FPGA/hdmi_candidate/HDMI-FAULT-HANDOFF.md#31-r13成功运行的实际方法与证据) |
| 启动故障诊断 | r26被动PS／PL时间轴、实际bit／BOOT及1次无SDK故障样本完成；原BOOT已恢复 | PS输出初态已高、PL释放后HDMI保留返回，未见已观测AR；仅等待PS高电平不能解释该样本。缺当前HP2／FIFO复位契约。[实际结果与限制](tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/PLAN.md)、[恢复状态](tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/state.json) |
| PC骨架传输与3D回放 | 本机C++→TCP→WebSocket→Three.js链路完成；60份历史真实结果按17／43帧分段回放 | 不是板端实时发布或新推理；未做HDMI与PC双路联合验收。[实现与验证](software/pc_viewer/README.md) |
| 真实CSI采集 | 单节点流式实采、训练原始日志顺序核对及固定幅度尺度适配完成，适配回放与离线输出逐字节相同 | 经验尺度不代表绝对RF标定或姿态精度；可靠性、全局同步及三独立节点配置尚缺，model_ready=false。[最新采集结果与恢复记录](tools/nexmon/README.md) |
| 旧VPU／RTSP演示 | 原预采CSI有界网络演示和相关代码、失败证据保留 | 属于历史分支，不再作为新展示主链的必做路径。[历史演示](software/demo/README.md) |

各项成果按发生时配置分别认定；历史回放、一次新推理、启动可靠性和连续长期互不替代。完整阶段记录见[Done.md](Done.md)。

## 主要难点与下一步顺序

- **D45启动稳定性优先。** r26收窄到启动／更早事务状态；PS初态已高不证明释放边沿，FIFO占用仍不可观测。需匹配当前器件／固件的复位契约，不能把PL复位有连接、CSR清零或单次Open成功当成修复。
- **D46真实输入适配是另一独立缺口。** 训练顺序已抽样精确绑定，单节点30点已作经验幅度适配；仍缺三独立接收节点同步配置及真实模型效果验证，不能直接送入现有模型。
- **D44、D29／D41及联合长期仍保留。** 首次reader失败根因、严格实时和长尾需分别验证；健康启动后的短时显示不等于长期稳定。

详细事实集中在[DIFFICULTIES.md](DIFFICULTIES.md)。后续顺序及验收条件见[ToDoLists.md](ToDoLists.md)；r26最新判读与当前资料缺口以本轮结果为准。启动稳定性解决后再回归推理与显示、接入PC，长期验证须用户单独批准。

## 当前状态与执行边界

用户本轮明确恢复HDMI故障排查并交由代理执行；用户不在板旁，本轮无需现场操作。r26实际1次候选＋1次原BOOT回退后已关闭，无后台工作；不删模块、不开SDK／DMA／推理／HDMI START，不做HDMI长期。用户确认暂无匹配PS资料，将咨询官方；相关寄存器／固件修改等待有效契约。旧包额度不恢复；旧DATA独立暂停，FAT不修，不接入Vivado MCP。

最终启动文件及运行中原BOOT已分别核验，六个SDK库／九启动文件身份符合，设备无占用；实际运行ID及原值见[r26板端结果](tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/board-summary.json)。CSI分支的恢复状态仍以[采集入口](tools/nexmon/README.md)为准。

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
