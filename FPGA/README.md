# FPGA工程资料入口

更新：2026-10-18。HDMI动态图案、历史骨架回放和r13三窗新推理→HDMI有界闭环已通过；D44首次reader故障和D45跨启动偶发异常未解决。开发与上板整体暂停，等待用户明确唤醒；本次仅整理文档。

- [HDMI结构、接口、开发过程与验证边界](hdmi_candidate/INTEGRATION.md)：本模块的维护入口。
- [显示应用与构建说明](../software/hdmi_demo/README.md)：PS渲染、共享Engine和帧生命周期。
- [难点与处理结果](../DIFFICULTIES.md)：D05接入成果、D42暂存路径、D43 FAT、D44首次START、D45启动异常。
- [当前暂停汇报](hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md)与[恢复入口](hdmi_candidate/RESUME.md)：近期实验、安全状态及未解决项。
- [阶段成果](../Done.md)、[ADR_49架构](../ADR/ADR_49.md)与[耗时复盘](hdmi_candidate/TIME-REPORT-20261018.md)。

源码、约束和仿真位于[hdmi_candidate](hdmi_candidate)。r9实际发布来源与仓库通用RTL须区分，不能把任意当前工作副本当作已验收位流的源码。

[10月16日工作总结](FPGA-WORK-SUMMARY-20261016.md)、[原整机接入计划](hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)和各候选执行包保留其当时范围；其中的“下一步”、旧暂停状态及已用完次数均不作为当前执行授权。原BOOT已回退；HDMI长期验证须另获用户批准。
