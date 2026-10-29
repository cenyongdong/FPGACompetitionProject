# 项目进度总览

**最新收尾（2026-10-29）：最终交付为 [r3 最终演示包](Deliverables/pose180-three-clips-20261029-r3-final.tar.gz)，操作见[部署步骤](Deliverables/pose180-three-clips-20261029-r3-DEPLOY.md)，目录见[交付索引](Deliverables/README.txt)。** 核心源码保留模块目录，原 epoch99、TopK=3、严格 score >0.2 与官方 1／2／3 人片段保持；最终包补入 Node.js 查找和 PC 有线连接修正。板端保留 `/root/pose180-three-clips-20261029-r3`，历史项目上传已清理；最近既有 r3 记录显示 420 帧推理／HDMI／PC 全部完成并安全退出，当前无设备占用。本轮只读取结果、整理文件，未启动新 SDK、写 BOOT 或重启。旧采集数据及冗余副本按用户要求删除，必要故障证据、模型与 FPGA 恢复资产保留；精确范围见[收尾记录](.local/project-cleanup-20261029-r1/summary.json)。

更新：2026-10-28。长期目标仍是稳定的真实CSI→PS／NPU→HDMI，PC独立。微调epoch13和随机初始化训练epoch4均已使用最新安全核心完成有限实板对比并正常退出；用户反馈动作跟随及位置仍较差，未确认自采训练带来明显改善。**已按最新要求换回未使用自采数据的原始epoch99模型**，保持TopK=1／无阈值／CPU单人滤波、HDMI／PC及性能指标栏。实际运行、恢复和结束状态统一见[本轮结果](.local/pose180-kinect-board-test-20261028-r1/README.md)，包入口见[测试说明](software/pose180_pipeline/resident/KINECT-BOARD-TEST-20261028.md)。

安全核心补齐HDMI部分构造回滚、重复释放保护、NPU在途异常释放守卫和非标准异常收尾；完成未证明时进入 `release_blocked`，保留资源及独占，不误报关闭。复用另一聊天已验证的ARM64程序，没有重新构建FPGA或更换SDK；原epoch99的r4归档保留历史，当前两个测试包包含新修订。[源码结果与边界](software/pose180_pipeline/resident/STARTUP-PACKAGE.md#板端异常资源保护源码修订未打包)。

## 当前可确认的状态

此前原epoch99／Top1／score >0.2的8344次运行保留历史；当前新包已恢复为原epoch99／Top1／无阈值，使用最新安全核心。旧远端关闭回执、TX／RX3临时SSH恢复及部分旧包原生日志归档仍未全部收尾，不把本轮结束当作旧包关闭。[当前恢复入口](FPGA/hdmi_candidate/RESUME.md)。

**最新发布已完成：合格 `probe-free-drain-filter-v1` 已成为当前运行及默认启动位流，旧参考 BOOT 保留恢复备份。** HDMI 新增显示服务就绪后、首次结果前的七色条，随后切回原骨架画面；49 帧官方数据实板验证完成，HDMI／PC 同时接收，安全停止且无后台负载。没有新增 FPGA 构建或 SDK 自启动，精确身份及结果见[恢复入口](FPGA/hdmi_candidate/RESUME.md#2026-10-27-默认启动发布与七色条)。

真实闭环、独立 PC、路由器开机采集和有限故障恢复已跑通；**重合／突跳、秒级输入间断和长期无人值守仍未验收**。最新软件候选、最新合格位流与最近一次实际运行身份分别记录，不能互相替代。

2026-10-27 已按用户要求将常驻 PS One Euro 改为 **0.5／0.3／1**，完成官方训练／测试各单人、双人、三人共六片段的 HDMI／PC 同时实测，合计 3024 次新推理。含首次 PC 观察器故障后的独立补测，本批七包均安全退出并实际回退原 BOOT，SDK、串口及 PC 观察负载已结束。原有两轮结果保留，最新精确身份及关闭记录见[恢复入口](FPGA/hdmi_candidate/RESUME.md)。

| 工作内容 | 已达到的阶段 | 未完成的边界／唯一结果入口 |
|---|---|---|
| 数据集开发／演示 | 六片段、867 个不同官方样本，显式重复仍执行新推理；HDMI／PC 同时运行，EOF 安全退出与实际回退完成 | 每包初始替换 3 帧；双人训练片段存在 PC 接收缺帧及秒级间隔，未做真值精度、实屏观感验收或视频录制；[唯一记录](software/pose180_pipeline/resident/DATASET-DEMO.md) |
| 常驻主链与恢复 | 最新完整窗口、单 SDK 所有者、有界异步记录；真实 RX 断线恢复和 PC 离线期间 HDMI 更新已验证 | 秒级缺窗仍存在，全天与跨启动可靠性未验收；[常驻核心](software/pose180_pipeline/resident/README.md)、[窗口恢复](software/pose180_pipeline/resident/WINDOW-RECOVERY.md) |
| 实采容错组窗算法 | 已接入最新七色条／v5 实时系统，完成故障恢复及修订后有限实板连续性验证；原严格路径保留 | 修订后有限复测无全局重同步；全天、实屏观感及近似配对姿态精度仍未验收；[唯一结果](software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md) |
| 时间相位分支修正 | 可选模块、原方法对照、已有三 RX 实采及官方训练／测试子集 CPU 实际模型比较完成，Windows／Linux 测试及 ARM64 编译通过 | 推理效果混合，此修正未接入正式服务，原预处理保持默认；[唯一记录](software/pose180_pipeline/resident/PHASE-CONTINUITY.md) |
| HDMI／PC 展示 | 共用 PresentationFrame；精简控件、骨架统一蓝色；HDMI 首次结果前增加七色条，PC 原样；39385 与原始 39383 分开 | v5 空旷场地补测已获两路持续更新的用户确认；重影／突跳及姿态精度仍开放；[最新结果](software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md)、[历史展示](software/pose180_pipeline/resident/PRESENTATION-20261026.md) |
| v5 PS 后处理 | 关联与显示平滑解耦、局部异常门控；0.5／0.3／1 数据集实板及本轮真实 CSI 接入完成，纯滤波平均约 7／13／19 μs（1／2／3 人） | 三人训练片段仍有轨迹重建，更强平滑有运动滞后；防闪现人工观感与姿态精度仍未验收；[设计](software/pose180_pipeline/resident/PRESENTATION-20261026.md#2026-10-27v5-后处理与已取消的-pl-扩展)与[最新实板结果](software/pose180_pipeline/resident/CSI-INTEGRATION-20261027.md) |
| 去诊断、保留启动消费 | 独立 r45 派生版本已完成物理资格与有限真实闭环；有实际消费异常返回后成功运行的样本 | 不等价于完整 AXI 检查器，不关闭 D45；运行中 PL_KEY1 黑屏失联样本保留；[结果](FPGA/hdmi_candidate/probe_free_drain/README.md) |
| 1／4 路 PL 滤波 | 参数化 RTL、位精确仿真、资源比较；4 路整机物理资格和有限板测完成 | CSR 搬运使总耗时高于 PS，CPU 继续默认；[资源与实测分项](software/pose180_pipeline/resident/PRESENTATION-20261026.md#pl-计算与资源) |
| 独立精简启动守卫 | ABI、覆盖映射、RTL 与离线测试已有实现 | 保护覆盖仍有缺口，**未取得部署资格**；与上面的保留消费候选分开；[首次离线结果](FPGA/hdmi_candidate/pose_stabilizer/README.md) |
| 心率支线 | PS 流式算法、隔离、可选 PL 核和有限真实 CSI 采集完成 | 尚无可信真实心率，未接板端常驻服务，未做新整机位流；[心率记录](software/vitals/HYBRID-20261026.md) |

## 下一步规划依据

用户要求的**暂停布线、取消新增 PL 开发**继续有效，本批实现进程已全部停止；新几何／批量滤波核仅保留源码、仿真和未完成实现，不生成或部署新位流。复用已有合格位流，集中 PS 后处理及可靠性，心率仍冻结。v5 新参数及自适应实时输入已完成上述有限集成验证；后续可评估轨迹重建与运动拖尾、录制既有画面的多片段演示。历史跨 ID 突跳与全天稳定性仍开放，两界面不变，有限新验证使用独立新包。

下一步的依赖、验证口径和优先级见[ToDoLists.md](ToDoLists.md)。旧 DATA、D45 全面调查与姿态偏置／标定的独立暂停保持；[心率冻结状态](software/vitals/HYBRID-20261026.md)按最新决定执行。所有旧包保持关闭，必要新验证沿用[现行自主授权](Agents.md#自主权限与重大问题)，仍须有界执行、安全停止及记录实际范围。

| 用途 | 入口 |
|---|---|
| 当前架构、接口、缓存与源码地图 | [ADR/TechDetails.md](ADR/TechDetails.md) |
| 硬件／软件版本选择、实际运行与恢复 | [FPGA/hdmi_candidate/RESUME.md](FPGA/hdmi_candidate/RESUME.md) |
| 后处理回放、PS／PL 性能、位流与原始证据 | [PRESENTATION-20261026.md](software/pose180_pipeline/resident/PRESENTATION-20261026.md) |
| 采集源的独立启停与自启动 | [路由器开机服务](software/pose180_pipeline/resident/autostart/README.md) |
| 未解决问题、历史成果与执行规则 | [DIFFICULTIES.md](DIFFICULTIES.md)、[Done.md](Done.md)、[Agents.md](Agents.md)、[ADR_50](ADR/ADR_50.md) |

模型／RAW、SDK、原预处理、NPU 分配、AI 四路、HP 分配和原始帧协议保持。历史失败与数值误差不由有限演示、回放或单模块测试回写为通过。
