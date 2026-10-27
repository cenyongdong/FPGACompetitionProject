# 项目进度总览

更新：2026-10-27。长期目标仍是稳定的真实 CSI → PS／NPU → HDMI，PC 独立。**当前阶段按用户要求优先使用 Person-in-WiFi 3D 官方训练／测试集开发验证和效果视频演示，关闭板端实时采集输入，两个输出画面完全保持。** 新本地数据集入口、已准备片段与验证状态见[数据集阶段记录](software/pose180_pipeline/resident/DATASET-DEMO.md)。

## 当前可确认的状态

**最新发布已完成：合格 `probe-free-drain-filter-v1` 已成为当前运行及默认启动位流，旧参考 BOOT 保留恢复备份。** HDMI 新增显示服务就绪后、首次结果前的七色条，随后切回原骨架画面；49 帧官方数据实板验证完成，HDMI／PC 同时接收，安全停止且无后台负载。没有新增 FPGA 构建或 SDK 自启动，精确身份及结果见[恢复入口](FPGA/hdmi_candidate/RESUME.md#2026-10-27-默认启动发布与七色条)。

真实闭环、独立 PC、路由器开机采集和有限故障恢复已跑通；**重合／突跳、秒级输入间断和长期无人值守仍未验收**。最新软件候选、最新合格位流与最近一次实际运行身份分别记录，不能互相替代。

2026-10-27 已按用户要求将常驻 PS One Euro 改为 **0.5／0.3／1**，完成官方训练／测试各单人、双人、三人共六片段的 HDMI／PC 同时实测，合计 3024 次新推理。含首次 PC 观察器故障后的独立补测，本批七包均安全退出并实际回退原 BOOT，SDK、串口及 PC 观察负载已结束。原有两轮结果保留，最新精确身份及关闭记录见[恢复入口](FPGA/hdmi_candidate/RESUME.md)。

| 工作内容 | 已达到的阶段 | 未完成的边界／唯一结果入口 |
|---|---|---|
| 数据集开发／演示 | 六片段、867 个不同官方样本，显式重复仍执行新推理；HDMI／PC 同时运行，EOF 安全退出与实际回退完成 | 每包初始替换 3 帧；双人训练片段存在 PC 接收缺帧及秒级间隔，未做真值精度、实屏观感验收或视频录制；[唯一记录](software/pose180_pipeline/resident/DATASET-DEMO.md) |
| 常驻主链与恢复 | 最新完整窗口、单 SDK 所有者、有界异步记录；真实 RX 断线恢复和 PC 离线期间 HDMI 更新已验证 | 秒级缺窗仍存在，全天与跨启动可靠性未验收；[常驻核心](software/pose180_pipeline/resident/README.md)、[窗口恢复](software/pose180_pipeline/resident/WINDOW-RECOVERY.md) |
| 实采容错组窗算法 | 保留原严格路径；新增同帧优先、学习容限、后台映射及窗口边界切换，已有录制回放／TCP mock 和 ARM64 编译完成 | 未恢复现场采集、未部署，真实新推理连续性及近似配对精度仍待；[唯一记录](software/pose180_pipeline/resident/ADAPTIVE-CSI.md) |
| HDMI／PC 展示 | 共用 PresentationFrame；精简控件、骨架统一蓝色；HDMI 首次结果前增加七色条，PC 原样；39385 与原始 39383 分开 | 最近现场实时版本为 v3，重影／突跳仍开放；[最新待机发布](FPGA/hdmi_candidate/RESUME.md)、[历史展示](software/pose180_pipeline/resident/PRESENTATION-20261026.md) |
| v5 PS 后处理 | 关联与显示平滑解耦、局部异常门控；0.5／0.3／1 本机／ARM64及上述实板完成，纯滤波平均约 7／13／19 μs（1／2／3 人） | 三人训练片段仍有轨迹重建，更强平滑有运动滞后；未验证新现场 CSI 或防闪现观感；[设计](software/pose180_pipeline/resident/PRESENTATION-20261026.md#2026-10-27v5-后处理与已取消的-pl-扩展)与[实板结果](software/pose180_pipeline/resident/DATASET-DEMO.md) |
| 去诊断、保留启动消费 | 独立 r45 派生版本已完成物理资格与有限真实闭环；有实际消费异常返回后成功运行的样本 | 不等价于完整 AXI 检查器，不关闭 D45；运行中 PL_KEY1 黑屏失联样本保留；[结果](FPGA/hdmi_candidate/probe_free_drain/README.md) |
| 1／4 路 PL 滤波 | 参数化 RTL、位精确仿真、资源比较；4 路整机物理资格和有限板测完成 | CSR 搬运使总耗时高于 PS，CPU 继续默认；[资源与实测分项](software/pose180_pipeline/resident/PRESENTATION-20261026.md#pl-计算与资源) |
| 独立精简启动守卫 | ABI、覆盖映射、RTL 与离线测试已有实现 | 保护覆盖仍有缺口，**未取得部署资格**；与上面的保留消费候选分开；[首次离线结果](FPGA/hdmi_candidate/pose_stabilizer/README.md) |
| 心率支线 | PS 流式算法、隔离、可选 PL 核和有限真实 CSI 采集完成 | 尚无可信真实心率，未接板端常驻服务，未做新整机位流；[心率记录](software/vitals/HYBRID-20261026.md) |

## 下一步规划依据

用户要求的**暂停布线、取消新增 PL 开发**继续有效，本批实现进程已全部停止；新几何／批量滤波核仅保留源码、仿真和未完成实现，不生成或部署新位流。复用已有合格位流，集中 PS 后处理及可靠性，心率仍冻结。v5 已完成上述新参数板端集成验证；下一步评估轨迹重建与运动拖尾、录制既有画面的多片段演示。历史跨 ID 突跳仍开放，两个界面不变，实时 CSI 与现场新采集延后。

下一步的依赖、验证口径和优先级见[ToDoLists.md](ToDoLists.md)。旧 DATA、D45 全面调查与姿态偏置／标定的独立暂停保持；[心率冻结状态](software/vitals/HYBRID-20261026.md)按最新决定执行。所有旧包保持关闭，必要新验证沿用[现行自主授权](Agents.md#自主权限与重大问题)，仍须有界执行、安全停止及记录实际范围。

| 用途 | 入口 |
|---|---|
| 当前架构、接口、缓存与源码地图 | [ADR/TechDetails.md](ADR/TechDetails.md) |
| 硬件／软件版本选择、实际运行与恢复 | [FPGA/hdmi_candidate/RESUME.md](FPGA/hdmi_candidate/RESUME.md) |
| 后处理回放、PS／PL 性能、位流与原始证据 | [PRESENTATION-20261026.md](software/pose180_pipeline/resident/PRESENTATION-20261026.md) |
| 采集源的独立启停与自启动 | [路由器开机服务](software/pose180_pipeline/resident/autostart/README.md) |
| 未解决问题、历史成果与执行规则 | [DIFFICULTIES.md](DIFFICULTIES.md)、[Done.md](Done.md)、[Agents.md](Agents.md)、[ADR_50](ADR/ADR_50.md) |

模型／RAW、SDK、原预处理、NPU 分配、AI 四路、HP 分配和原始帧协议保持。历史失败与数值误差不由有限演示、回放或单模块测试回写为通过。
