# FPGA工程资料入口

2026-10-17最新：用户明确恢复HDMI接入与渲染；DDR读帧、双缓冲翻帧、在途STOP及三份真实骨架回放已板测，现场确认画面。新推理联动因模型参数上传SDK DMA异常停止；首次reader故障根因未明。当前入口：[本轮报告](../tools/pose-v1/evidence/hdmi-display-20261017-r1/REPORT.md)、[显示软件](../software/hdmi_demo/README.md)。以下架构归档及交接文字保留当时范围。

2026-10-17：[新架构ADR_49](../ADR/ADR_49.md)已确认PS／NPU感知、PL本地HDMI、PC独立3D展示，未来主链停用VPU／RTSP。本轮仅归档，下一阶段实施仍暂停待明确执行指令。历史计划与执行许可不触发自动续作。

- [FPGA／HDMI负责范围、完成内容、原厂位流操作与交接总结](FPGA-WORK-SUMMARY-20261016.md)。
- [HDMI当前恢复入口](hdmi_candidate/RESUME.md)。
- [现有整机接口和实施记录](hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)。
- [实际静态实屏结果与未验收边界](../tools/pose-v1/evidence/hdmi-board-candidate-20261016-r1/REPORT.md)。

源码、约束、仿真和配套工具位于[hdmi_candidate](hdmi_candidate)；下一阶段职责以ADR_49为准，具体接口和执行范围仍待确定，不能把架构确认当作动态帧验证已经完成。
