# HDMI交接与恢复入口

前一批次：[r6持续TX租约](../../software/pose180_pipeline/resident/TX-LEASE.md)已按1候选／1 SDK／10分钟／1原BOOT回退完成并关闭，全部余额0、无本批负载。该批原BOOT身份、恢复证据及剩余卡顿以r6记录为准；下述r5及更早状态保留历史，不复用旧额度。

当前最新批次：[r7共同窗口优化](../../software/pose180_pipeline/resident/WINDOW-RECOVERY.md)已执行并关闭，1候选／1 SDK／600秒运行期／1原BOOT回退，全部余额0、无本批负载；**当前原BOOT身份及实际结果以r7记录为准**。无窗恢复等待已缩短，显示器整屏黑屏经重新上电恢复、原因未定。必要新验证可按[最新自主板测规范](../../Agents.md#自主权限与重大问题)另记新批次直接执行，不复活旧包。

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
