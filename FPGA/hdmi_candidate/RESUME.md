# HDMI排查恢复入口

更新：2026-10-21，r26实际bit／BOOT及第1次被动故障取证完成，已安全回原BOOT，包关闭、余额0，无后台工作。用户暂无匹配PS资料，将咨询比赛官方；寄存器／启动固件修改等待有效契约。实际身份和额度以[r26状态](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/state.json)为准。

## 当前技术状态

r13在一次健康启动下完成四档DMA与三窗新推理到HDMI，现场确认通过。r24已生成实际bit／BOOT并见证PL互联复位，r25复用同BOOT在SDK加载前仍故障；D44／D45未关闭，短时通过不保证健康启动后的持续稳定。

r26被动PS／PL记录器、定向仿真及旧CSR回归通过；复用原厂PS检查点，仅导出真实HP2复位输出，原有253个单元保持。完整布线与setup／hold在既定例外范围内通过，实际bit及仅替换PL的BOOT已生成。第1次无SDK启动复现，取消第2候选并回原BOOT；本次PS出口随后已空闲，HDMI返回支路仍保留RVALID，不能沿用“PS始终背压”的描述。原值、物理门检和判读限制集中在r26 PLAN。

| 交接用途 | 当前入口 |
|---|---|
| 唯一恢复状态 | [r26 state.json](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/state.json) |
| 实际板测及最终恢复 | [board-summary.json](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/board-summary.json)、[原值归档](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/board-evidence.tar.gz)；原BOOT文件与运行、SDK身份和无占用已核验，COM7两次启动RX完成并关闭 |
| 详细故障、接线、寄存器与产物 | [工程师交接](HDMI-FAULT-HANDOFF.md) |
| 当前技术方案与判读边界 | [r26 PLAN.md](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/PLAN.md) |
| 已完成结构与显示应用 | [INTEGRATION.md](INTEGRATION.md)、[software/hdmi_demo](../../software/hdmi_demo/README.md) |
| 稳定问题及独立暂停项 | [DIFFICULTIES.md](../../DIFFICULTIES.md) |

## 当前执行边界

SSH为主通道、COM7备用；原BOOT运行已核验，不使用历史boot_id或失败Session。r26自设最多2次候选＋1次回退，第1次故障后按停止条件关闭，实际1＋1、全部余额0；不能再执行其第2候选。

下一步需取得当前AArch64／030ai BSP或厂商HP2／FIFO复位契约，核对安全复位顺序及Linux重启覆盖范围，再准备针对性修正。FSBL实际非零初始化表已由运行时复制及原BOOT字节核对，不能误判未初始化；不套用旧A7地址、不靠延时、重复Open或强制RREADY排空未知返回。详细证据及限制见r26 PLAN。

正确按键为PL_KEY1／SW6／F8，PL_KEY2／SW7／E7用于SDI GTX。r21／r22已证明正确SW6可清观测器；r24证明PL互联实际复位，仍不能等同PS内部FIFO复位。当前下一方案不需要按键或屏幕观察，不重复以旧SW7结果排查F8。

r26及此前包均已关闭，旧次数不恢复。本轮SDK／Open、DMA、推理、HDMI START、按键及长期验证实际均为0；不删模块。旧DATA独立暂停，FAT不修，本任务不接入Vivado MCP。

旧[10月18日暂停汇报](STARTUP-PAUSE-REPORT-20261018.md)和r20状态仅保留当时事实；按键纠正及r23至r25的新结果已取代其中过期的“当前判断”。不将旧计划或恢复路径作为新的执行授权。
