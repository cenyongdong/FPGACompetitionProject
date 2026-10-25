# 项目进度总览

更新：2026-10-25。**真实CSI→板端180-query新推理→HDMI有界闭环已跑通，用户现场确认能看到多轮骨架更新。** 按[ADR_50](ADR/ADR_50.md)实现常驻核心、最新窗口、有界记录、PC解耦和网络恢复；无需严格30Hz。完整结果、版本、资源、回退状态及证据只维护在[本轮实施记录](software/pose180_pipeline/resident/README.md)。

已完成原BOOT回放输入新推理、真实CSI接入与跨断流恢复，以及HDMI有限联合验证。软件故障注入和有界滚动整理通过；启动可靠性、全天无人值守和人体识别精度仍未验收。

持续采集守护、独立启停和日志上限已投入实测；此前[r5卡顿优化与PC联合长测](software/pose180_pipeline/resident/STUTTER-VALIDATION.md)完成30分钟运行期、RX1单路断线恢复、PC物理离线超过5分钟期间HDMI持续更新及PC自动恢复。已正常停止、回原BOOT并关闭，该批恢复身份、计数与证据见r5记录。普通秒级缺窗仍存在；问题1姿态偏置继续搁置，旧包不复活。

最新[r6持续TX租约实测](software/pose180_pipeline/resident/TX-LEASE.md)已完成获准10分钟运行、正常停止及原BOOT回退，包关闭、余额0。同一TX任务续期成功，新版HDMI外观获现场确认；仍有共同窗口缺失后的长停顿与自动恢复，整体卡顿尚未解决。该批恢复身份与精确结果以r6记录为准。

[r7共同窗口优化实测](software/pose180_pipeline/resident/WINDOW-RECOVERY.md)已完成600秒运行期、正常退出与原BOOT回退并关闭；真实结果覆盖约428秒，无窗恢复长间隔缩短至约3.1～3.2秒，缺窗仍存在。现场黑屏／闪屏已归入[显示规格限制](software/pose180_pipeline/resident/WINDOW-RECOVERY.md#显示规格限制)，不再列为待定位故障。r7历史身份及精确结果见其记录。用户已授权必要验证可自主上板、无需再次询问，现行边界见[规范](Agents.md#自主权限与重大问题)。

[r8相位跟踪与r9见证复验](software/pose180_pipeline/resident/PHASE-TRACKING.md)已完成软件验证、首RVALID原始回放及实际RTL／布线核查。新r9复现1周期差异，并出现原准入范围外bit79；未启动SDK或验证RX1实机改善，已回原BOOT关闭、无本批负载。当前恢复身份与未知原因统一见该记录；问题1继续搁置。

| 用途 | 唯一入口 |
|---|---|
| 本轮实现、实际闭环、限制及恢复 | [常驻核心与实测](software/pose180_pipeline/resident/README.md) |
| 当前技术实现总览与历史分界 | [ADR/TechDetails.md](ADR/TechDetails.md) |
| 当前架构及执行规则 | [ADR_50](ADR/ADR_50.md)、[ADR_49](ADR/ADR_49.md)、[Agents.md](Agents.md) |
| 下一步与验收顺序 | [ToDoLists.md](ToDoLists.md) |
| 稳定问题与历史成果 | [DIFFICULTIES.md](DIFFICULTIES.md)、[Done.md](Done.md) |
| 合格bit／BOOT、已有时序例外及HDMI恢复 | [RESUME](FPGA/hdmi_candidate/RESUME.md)、[r45物理结果](tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md) |
| 旧严格主链、模型与CSI历史 | [旧主链实测](software/pose180_pipeline/RESULTS.md)、[180-query部署](tools/pose180/deploy/RESULTS.md)、[Nexmon](tools/nexmon/README.md) |

模型／RAW、SDK、原预处理、NPU分配、AI四路和帧协议保持。D45根因、旧D47和D48数值误差仍保留；旧DATA及D45全面根因调查独立暂停。未查询或操作训练旁支，不以本轮短时闭环改写旧失败，新的BOOT／重启／失败SDK重试仍按具体范围授权。
