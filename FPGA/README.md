# FPGA 工程资料入口

更新：2026-10-29。最终演示复用已发布 `probe-free-drain-filter-v1`，保留启动消费与已有 PL 功能；软件默认 CPU 后处理。新增几何／批量滤波 PL 已取消，心率冻结。有限实板运行与物理资格已有记录，但 D45 根因、运行中 PL_KEY1 恢复及全天稳定性未验收。

| 用途 | 入口 |
|---|---|
| 当前选择、最后观察与本机恢复备份 | [恢复入口](hdmi_candidate/RESUME.md)、[默认 BOOT 身份](hdmi_candidate/default_boot.json) |
| HDL、接口、帧采纳与停止契约 | [HDMI 工程说明](hdmi_candidate/INTEGRATION.md) |
| 保留启动消费的派生硬件 | [probe_free_drain](hdmi_candidate/probe_free_drain/README.md) |
| 已有 PL 滤波的物理结果与分项测时 | [后处理与 PS／PL 比较](../software/pose180_pipeline/resident/PRESENTATION-20261026.md#pl-计算与资源) |
| 启动异常历史、事实与假设 | [故障交接](hdmi_candidate/HDMI-FAULT-HANDOFF.md)、[困难最终处置](../DIFFICULTIES.md) |
| 构建工具与适配依据 | [路线二配置](hdmi_candidate/ROUTE2-BUILD-PLAN.md)、[资料索引](../REFERENCES.md) |
| 全部硬件 Markdown | [完整文档目录](../DOCUMENTATION.md) |

[10 月 16 日总结](FPGA-WORK-SUMMARY-20261016.md)、各候选和诊断报告保留当时源码／约束／启动身份。旧“当前”“下一步”不代表现行方案，不能将任意工作副本视为合格位流来源；无设计变更不重复构建。
