# 项目进度总览

更新：2026-10-25。**真实CSI→板端180-query新推理→HDMI有界闭环已跑通，用户现场确认能看到多轮骨架更新。** 按[ADR_50](ADR/ADR_50.md)实现常驻核心、最新窗口、有界记录、PC解耦和网络恢复；无需严格30Hz。完整结果、版本、资源、回退状态及证据只维护在[本轮实施记录](software/pose180_pipeline/resident/README.md)。

已完成原BOOT回放输入新推理、真实CSI接入与跨断流恢复，以及HDMI有限联合验证。软件故障注入和有界滚动整理通过；启动可靠性、全天无人值守和人体识别精度仍未验收。

持续采集守护、设备本地独立启停和原生日志上限已投入实测；[30分钟联合验证r4](software/pose180_pipeline/resident/LONG-VALIDATION.md)已完成RX断线恢复与PC物理离线后的实屏持续更新，正常停止并回原BOOT，包已关闭。早期TX续发问题已修正；秒级重同步停顿、画面等待提示和真实动作效果是下一重点。精确结果、限制与恢复身份只维护于r4记录，旧包不复活。

| 用途 | 唯一入口 |
|---|---|
| 本轮实现、实际闭环、限制及恢复 | [常驻核心与实测](software/pose180_pipeline/resident/README.md) |
| 当前架构及执行规则 | [ADR_50](ADR/ADR_50.md)、[ADR_49](ADR/ADR_49.md)、[Agents.md](Agents.md) |
| 下一步与验收顺序 | [ToDoLists.md](ToDoLists.md) |
| 稳定问题与历史成果 | [DIFFICULTIES.md](DIFFICULTIES.md)、[Done.md](Done.md) |
| 合格bit／BOOT、已有时序例外及HDMI恢复 | [RESUME](FPGA/hdmi_candidate/RESUME.md)、[r45物理结果](tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md) |
| 旧严格主链、模型与CSI历史 | [旧主链实测](software/pose180_pipeline/RESULTS.md)、[180-query部署](tools/pose180/deploy/RESULTS.md)、[Nexmon](tools/nexmon/README.md) |

模型／RAW、SDK、原预处理、NPU分配、AI四路和帧协议保持。D45根因、旧D47和D48数值误差仍保留；旧DATA及D45全面根因调查独立暂停。未查询或操作训练旁支，不以本轮短时闭环改写旧失败，新的BOOT／重启／失败SDK重试仍按具体范围授权。
