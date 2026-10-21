# FPGA工程资料入口

更新：2026-10-21，仅整理文档。r13三窗新推理到HDMI有界通过，r24已有实际PL互联复位，r25在SDK前仍复现；D44／D45未关闭，r26只有离线分析与方案。实施暂停、不删模块，长期HDMI须单独批准。

- [HDMI结构、接口、开发过程与验证边界](hdmi_candidate/INTEGRATION.md)：本模块的维护入口。
- [HDMI启动故障工程交接](hdmi_candidate/HDMI-FAULT-HANDOFF.md)：资深工程师所需实际接线、原值、DCP／源码／BOOT和定向判读。
- [显示应用与构建说明](../software/hdmi_demo/README.md)：PS渲染、共享Engine和帧生命周期。
- [难点与处理结果](../DIFFICULTIES.md)：D05接入成果、D42暂存路径、D43 FAT、D44首次START、D45启动异常。
- [当前恢复入口](hdmi_candidate/RESUME.md)及[r26恢复状态](../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/state.json)：实施状态与安全恢复；[10月18日暂停汇报](hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md)仅作历史。
- [阶段成果](../Done.md)、[ADR_49架构](../ADR/ADR_49.md)与[耗时复盘](hdmi_candidate/TIME-REPORT-20261018.md)。

源码、约束和仿真位于[hdmi_candidate](hdmi_candidate)。r9实际发布来源与仓库通用RTL须区分，不能把任意当前工作副本当作已验收位流的源码。

[10月16日工作总结](FPGA-WORK-SUMMARY-20261016.md)、[原整机接入计划](hdmi_candidate/SYSTEM-INTEGRATION-PLAN.md)和各候选执行包保留其当时范围；其中的“下一步”、旧暂停状态及已用完次数均不作为当前执行授权。原BOOT已回退；HDMI长期验证须另获用户批准。
