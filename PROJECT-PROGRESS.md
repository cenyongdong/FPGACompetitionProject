# 项目进度总览

整理：2026-10-27。最高优先级仍是**真实 CSI → 板端 PS／NPU → 本地 HDMI 的稳定演示与分级恢复**，PC 为可断开的独立观察端，不以严格 30 Hz 为门槛。本次仅整理已有实现与记录，没有启动构建、部署或板测。

## 当前可确认的状态

真实闭环、独立 PC、路由器开机采集和有限故障恢复已跑通；**重合／突跳、秒级输入间断和长期无人值守仍未验收**。最新软件候选、最新合格位流与最近一次实际运行身份分别记录，不能互相替代。

最近一次核验为原 BOOT 已实际回退；2026-10-27 的 PS 历史回放未改变启动身份，未调用 SDK。相关板测、基准、PC 观察和临时构建负载均已结束，路由器开机服务保持独立启用。这是已有记录的最后状态，不是本次重新连接设备的实时核验。精确身份及关闭记录见[恢复入口](FPGA/hdmi_candidate/RESUME.md)。

| 工作内容 | 已达到的阶段 | 未完成的边界／唯一结果入口 |
|---|---|---|
| 常驻主链与恢复 | 最新完整窗口、单 SDK 所有者、有界异步记录；真实 RX 断线恢复和 PC 离线期间 HDMI 更新已验证 | 秒级缺窗仍存在，全天与跨启动可靠性未验收；[常驻核心](software/pose180_pipeline/resident/README.md)、[窗口恢复](software/pose180_pipeline/resident/WINDOW-RECOVERY.md) |
| HDMI／PC 展示 | 共用 PresentationFrame；精简文字及控件、骨架统一蓝色；39385 派生展示与原始 39383 分开 | 最近实时版本为 v3，现场重影／突跳仍开放；[展示与实板记录](software/pose180_pipeline/resident/PRESENTATION-20261026.md) |
| v4 后处理候选 | 历史候选选择、稳健中心预测、弱相似目标延期及新旧身份交接；本机／ARM64 测试、同源回放和 PS 测时完成 | 近距离配对减少，但跨 ID 大替换仍有回归；尚未部署为实时版本，不能称防闪现完成；[v4 结果](software/pose180_pipeline/resident/PRESENTATION-20261026.md#2026-10-27v4-人物级时序去重及-ps-回放验证) |
| 去诊断、保留启动消费 | 独立 r45 派生版本已完成物理资格与有限真实闭环；有实际消费异常返回后成功运行的样本 | 不等价于完整 AXI 检查器，不关闭 D45；运行中 PL_KEY1 黑屏失联样本保留；[结果](FPGA/hdmi_candidate/probe_free_drain/README.md) |
| 1／4 路 PL 滤波 | 参数化 RTL、位精确仿真、资源比较；4 路整机物理资格和有限板测完成 | CSR 搬运使总耗时高于 PS，CPU 继续默认；[资源与实测分项](software/pose180_pipeline/resident/PRESENTATION-20261026.md#pl-计算与资源) |
| 独立精简启动守卫 | ABI、覆盖映射、RTL 与离线测试已有实现 | 保护覆盖仍有缺口，**未取得部署资格**；与上面的保留消费候选分开；[首次离线结果](FPGA/hdmi_candidate/pose_stabilizer/README.md) |
| 心率支线 | PS 流式算法、隔离、可选 PL 核和有限真实 CSI 采集完成 | 尚无可信真实心率，未接板端常驻服务，未做新整机位流；[心率记录](software/vitals/HYBRID-20261026.md) |

## 下一步规划依据

先处理人物级关联／交接及跨 ID 画面替换，同时把输入缺窗作为独立连续性问题分析。不能用更强坐标平滑、长时间保留旧姿态或强制 Top1 代替这两类问题的解决。v4 保留为有限对照候选；CPU 为默认，已有合格硬件按匹配 profile 复用，不因整理或纯软件修改重跑 FPGA。

下一步的依赖、验证口径和优先级见[ToDoLists.md](ToDoLists.md)。旧 DATA、D45 全面调查与姿态偏置／标定的独立暂停保持；心率与当前后处理按用户后续专项授权推进。所有旧包保持关闭，必要新验证沿用[现行自主授权](Agents.md#自主权限与重大问题)，仍须有界执行、安全停止及记录实际范围。

| 用途 | 入口 |
|---|---|
| 当前架构、接口、缓存与源码地图 | [ADR/TechDetails.md](ADR/TechDetails.md) |
| 硬件／软件版本选择、实际运行与恢复 | [FPGA/hdmi_candidate/RESUME.md](FPGA/hdmi_candidate/RESUME.md) |
| 后处理回放、PS／PL 性能、位流与原始证据 | [PRESENTATION-20261026.md](software/pose180_pipeline/resident/PRESENTATION-20261026.md) |
| 采集源的独立启停与自启动 | [路由器开机服务](software/pose180_pipeline/resident/autostart/README.md) |
| 未解决问题、历史成果与执行规则 | [DIFFICULTIES.md](DIFFICULTIES.md)、[Done.md](Done.md)、[Agents.md](Agents.md)、[ADR_50](ADR/ADR_50.md) |

模型／RAW、SDK、原预处理、NPU 分配、AI 四路、HP 分配和原始帧协议保持。历史失败与数值误差不由有限演示、回放或单模块测试回写为通过。
