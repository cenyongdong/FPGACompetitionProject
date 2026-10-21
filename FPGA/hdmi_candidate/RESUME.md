# HDMI暂停与恢复入口

更新：2026-10-21，仅整理文档。实施继续暂停，用户明确不删减模块；本页不恢复离线实现、仿真、构建、部署、板测或后台续作。最新项目范围见[项目总览](../../PROJECT-PROGRESS.md)，后续顺序见[ToDoLists.md](../../ToDoLists.md)。

## 当前技术状态

r13在一次健康启动下完成四档DMA与三窗新推理到HDMI，现场确认通过。r24已生成实际bit／BOOT并见证PL互联复位，r25复用同BOOT在SDK加载前仍故障；D44／D45未关闭，短时通过不保证健康启动后的持续稳定。

r26已完成原厂PS适配与r24 Routed DCP离线分析，确认FIFO名引脚复用及真实PS HP2复位输出未被观测；被动PS／PL时间轴方案尚未实现，无新观测RTL、bit、BOOT或板端结果。

| 交接用途 | 当前入口 |
|---|---|
| 唯一恢复状态 | [r26 state.json](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/state.json) |
| 最后FPGA实板审计 | [r25 final-audit.json](../../tools/pose-v1/evidence/hdmi-startup-stability-20261020-r25/final-audit.json)，原BOOT运行与文件恢复已分别核验；不是本次实时核验 |
| 详细故障、接线、寄存器与产物 | [工程师交接](HDMI-FAULT-HANDOFF.md) |
| 尚未实施的下一技术方案 | [r26 PLAN.md](../../tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/PLAN.md) |
| 已完成结构与显示应用 | [INTEGRATION.md](INTEGRATION.md)、[software/hdmi_demo](../../software/hdmi_demo/README.md) |
| 稳定问题及独立暂停项 | [DIFFICULTIES.md](../../DIFFICULTIES.md) |

## 用户明确恢复后

先核验实际板端运行身份、原BOOT备份／恢复文件、SDK／启动身份、设备占用、SSH主机密钥及串口身份；不直接使用历史boot_id或失败Session。SSH为主通道、COM7备用，当前现场状态未重新读取。

优先按r26准备被动启动观测，以真实PS／PL复位释放、HP时钟和首AR／R事件区分原因，并补旧视频写侧活动；不靠增加软件延时、重复Open或强制RREADY排空未知返回来冒充修复。详细判读和构建门见工程师交接，不在此复制完整执行包。

正确按键为PL_KEY1／SW6／F8，PL_KEY2／SW7／E7用于SDI GTX。r21／r22已证明正确SW6可清观测器；r24证明PL互联实际复位，仍不能等同PS内部FIFO复位。当前下一方案不需要按键或屏幕观察，不重复以旧SW7结果排查F8。

r23／r24／r25及此前包均已关闭，旧次数不恢复。此前PS复位／FIFO／释放顺序诊断的BOOT／重启授权保留，但须先由用户解除当前暂停并按安全恢复策略使用；它不授权长期HDMI或其它重大变更。旧DATA独立暂停，FAT不修，本任务不接入Vivado MCP。

旧[10月18日暂停汇报](STARTUP-PAUSE-REPORT-20261018.md)和r20状态仅保留当时事实；按键纠正及r23至r25的新结果已取代其中过期的“当前判断”。不将旧计划或恢复路径作为新的执行授权。
