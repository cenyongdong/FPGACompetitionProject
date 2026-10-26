# HDMI交接与恢复入口

2026-10-26 最新：追加 r3 已结束，首轮 PL_KEY1 运行中复位后黑屏失联，完整断电恢复；后两轮各 300 秒及现场画面确认通过，其中第 2 轮 SDK 前有界消费 16 拍返回后正常运行。最终已回原 BOOT，启动编号 `7170b447-f844-421f-b5d6-36140b450e1a`；全部新包关闭、余额 0，无本批活动负载。按键恢复仍未解决，r1／r2 不复活；[唯一结果与产物入口](probe_free_drain/README.md)，精确状态见 `tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r3/state.json`。

2026-10-26 当前专项已完成：[去除诊断、保留异常消费的 r45 派生候选](probe_free_drain/README.md)。完整物理资格及三轮各 5 分钟真实全链路测试通过，原 BOOT 文件和实际回退启动均已核验，三包关闭、无本批后台工作。产物、精确结果、恢复身份和限制统一见该记录；日志位于 `tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1`，运行资产位于 `.local/hdmi-probe-free-drain-20261026-r1`。不复活下述历史额度或独立暂停任务。

2026-10-26 心率专项恢复：[PS 流式模块与实采](../../software/vitals/HYBRID-20261026.md)、[小型 PL 自相关核](../vitals_acf/README.md)。已完成 OOC／仿真和保留全部 r45 保护的独立覆盖层，未生成新整机位流或上板；HDMI／旧问题恢复边界仍按下文。

最新离线工作：[防闪现后处理与精简硬件](pose_stabilizer/README.md)。软件CPU后端、派生展示、1／4路RTL及OOC比较已完成；LUT预算与精简守卫覆盖缺口如实保留，未生成候选位流或部署。板端暂停与r12恢复边界不变；后续不将该覆盖层直接用作启动位流。

前一批次：[r6持续TX租约](../../software/pose180_pipeline/resident/TX-LEASE.md)已按1候选／1 SDK／10分钟／1原BOOT回退完成并关闭，全部余额0、无本批负载。该批原BOOT身份、恢复证据及剩余卡顿以r6记录为准；下述r5及更早状态保留历史，不复用旧额度。

上一批次：[r7共同窗口优化](../../software/pose180_pipeline/resident/WINDOW-RECOVERY.md)已执行并关闭，1候选／1 SDK／600秒运行期／1原BOOT回退，全部余额0、无本批负载；该批原BOOT身份及实际结果以r7记录为准。无窗恢复等待已缩短，显示器黑屏／闪屏已按用户确认的[显示规格限制](../../software/pose180_pipeline/resident/WINDOW-RECOVERY.md#显示规格限制)移出待定位故障。必要新验证可按[最新自主板测规范](../../Agents.md#自主权限与重大问题)另记新批次直接执行，不复活旧包。

当前最新批次：[r10／r11／r12](../../software/pose180_pipeline/resident/TOP3-VALIDATION.md)。r12有限推理及PC接收验证完成，随后用户关闭板端并要求暂停工作。原BOOT文件已恢复，但未执行回退启动核验；本机观察进程已结束，无本批活动负载，不自动恢复。实际次数、身份、未取回证据及恢复边界以该记录为准。

2026-10-25较早批次：[r5卡顿优化与PC联合长测](../../software/pose180_pipeline/resident/STUTTER-VALIDATION.md)已完成30分钟、RX物理恢复及PC离线实屏验证，正常停止、回原BOOT并关闭。实际1候选／1SDK／1回退，全部余额0；无本批活动负载，该批恢复身份与原值统一见r5记录及本机`.local/pose180-resident-stutter-20261025-r5/run-state.json`。r4及更早包均保持关闭。

2026-10-25新决策：[ADR_50](../../ADR/ADR_50.md)已批准端到端演示优先、有界缓存、PC／归档解耦及分级恢复，无需严格30Hz。实现与本轮真实CSI→推理→HDMI有界结果见[常驻演示记录](../../software/pose180_pipeline/resident/README.md)，用户已现场确认多轮骨架更新；最新包状态与恢复身份以该记录为准。下一步见[待办](../../ToDoLists.md)；下述旧包失败与关闭额度不回写。

2026-10-25较早严格主链实测：180-query新主链已部署；原BOOT有界测试止于Host归档1秒保护，修正后完成软件验证。新HDMI包`pose180-hdmi-20261025-r2`在SDK前因新增RCAM_UNDERFLOW状态未过准入，实际1候选/0 SDK/1原BOOT回退，已关闭、余额0；当前原BOOT、无占用及详细证据统一见[新主链实测](../../software/pose180_pipeline/RESULTS.md)。下述r53保留历史，不作为当前启动身份或新额度。

入口整理：2026-10-25。HDMI旧板测r53已回原BOOT；实际1次候选/1次SDK/1次回退，包关闭、余额全部0，批次结束时无本批后台工作。后续独立180-query批次的恢复见[部署实测](../../tools/pose180/deploy/RESULTS.md)；恢复时不能将历史运行身份视作实时身份。现行执行边界见[项目总览](../../PROJECT-PROGRESS.md)。

## r53历史核验状态与原始证据

| 用途 | 唯一维护入口 |
|---|---|
| 当前事实、恢复身份、问题及原始数据位置 | [r53 RESULTS](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/RESULTS.md)、[state.json](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/state.json) |
| 原BOOT运行、启动文件/SDK及无占用核验 | [final-audit.json](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/final-audit.json)、[closed.json](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/closed.json)；历史boot_id不得直接作为下次会话身份 |
| r53首读/即时副本/两轮SDK晚读和协议完整原值 | [candidate-evidence.tar.gz](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/candidate-evidence.tar.gz)、[离线字节比较](../../tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/index-read-analysis.json) |
| 当前源码、硬件与数据流 | [INTEGRATION](INTEGRATION.md)、[r45硬件源码](diagnostics/deferred_consume_r45/sources)、[r53主调度](diagnostics/native_rgb565_r53/joint/main.cpp)、[SDK显示适配](diagnostics/native_rgb565_r53/display/hdmi_output.cpp) |
| 当前硬件物理资格与BOOT对应关系 | [r45 RESULTS](../../tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/RESULTS.md)；r46～r53复用，无重新EDA或新增时序例外 |
| 隔离/逐拍波形/原生协议历史 | [S01隔离](diagnostics/S01-ISOLATION.md)、[r30波形](diagnostics/waveforms-r30-20261022/README.md)、[r37协议结果](../../tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37/RESULTS.md) |
| 实际异常消费后有限业务 | [r52 RESULTS](../../tools/pose-v1/evidence/hdmi-long-git-20261024-r52/RESULTS.md)；不以r53健康消费0的样本替代 |
| 完成、难点、下一计划 | [Done](../../Done.md)、[DIFFICULTIES](../../DIFFICULTIES.md)、[ToDoLists](../../ToDoLists.md) |

## 当前结论与执行边界

r53健康启动（AR=0/R=0、消费0），完成187次HDMI采纳后第189次推理首读索引1568字混入同帧姿态内容。晚读正确不能修补首读，产生环节未定；用户只见瞬间骨架，持续实屏和联合长期均未通过。

保留原有限消费及AI四路：HC0→HP0、HC1→HP1、HC2→HP2/S00、HC3→HP3；HDMI→HP2/S01。官方说明HP FIFO位于PL，撤下PS内部HP FIFO残留的既定解释；D45根因未关闭，文档任务不恢复已中止的根因板测。

所有旧包保持关闭；新增BOOT/重启、失败SDK负载再执行按具体新包授权，不复活旧次数。旧DATA独立暂停，不删模块、不修FAT、不改模型/数学/SDK/NPU分配/帧协议，不接入Vivado MCP。SSH为主、COM7备用，未来操作前重新核验实际身份与恢复通道。

正确按键为PL_KEY1/SW6/F8；PL_KEY2/SW7/E7用于SDI GTX。观测器清零、PL互联复位、宏内部事务状态分别认定。旧r26与10月18日暂停报告保留历史，不作为最新状态或新操作授权。
