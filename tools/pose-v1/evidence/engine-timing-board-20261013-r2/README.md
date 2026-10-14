# Engine有限计时证据（2026-10-13）

用户任务：计算当前工具可获得的各项耗时并返回表格。执行位置Windows D:\FPGACompetitionProject、既有FPAI交叉编译产物、Lite /tmp/wifi-pose-engine-timing-20261013-r2。新包.local/engine-timing-delivery-20261013-r3，仅包装器内核版本比较来源修订；正式129锁定源码、模型JSON/RAW、SDK、BOOT不改。

默认每模式3次固定308/309/310窗口，无预热、无VPU/TCP，120秒＋5秒退出宽限，无压力/内存规整/重启。前置NPU独占、模型/SDK/BOOT/内核身份一致，完整实际输出保存后逐位比较，任何异常立即停止且不重试。

- [实测表](timing-table.md)、[可计算汇总](timing-summary.json)、[重算脚本](summarize.py)：逐帧汇总桥区间后求3帧均值；forward用回调区间并集扣除剩余。脚本不触发板端执行。
- [baseline分析](baseline-return/run-baseline/analysis/report.json)、[wall分析](wall-return/run-wall/analysis/report.json)：各3前向数值/身份/计数/保存和回收通过；本机独立分析核验完整证据哈希。
- [SDK失败](sdk-return/run-sdk/results/failure.json)：第1帧输出正确，采样745层时间含215负值，立即停止。原[硬件层数组](sdk-return/run-sdk/results/hardware-layers.jsonl)、[SDK tuple](sdk-return/run-sdk/results/sdk-profile.jsonl)保留；剩余2帧未执行，未重试。批次[result](result.json)为failed_stopped_no_retry，不把失败模式计作通过。
- [执行计划](execution-plan.json)、[操作记录](steps.json)、[包审查](delivery-review.json)：完整归档baseline/wall/sdk-return.tar及解包文件，含全部实际数组、日志、身份、内核、资源前后快照和退出码。
- [最终现场](99-final-state.txt)：无pose进程、FPGA operating，SSH已关闭。没有遗留本批后台工作；板端无关系统服务不由本批修改。
- [文档/包装器修订](revision-record.json)及revision-before完整副本：不回写历史来源/构建/交付清单。board_run.py来源比较修正与实际新包一致，原C++未改。

前次r1预检错误：用历史dmesg与当前proc/version比较，0次前向即停止；[历史与当前同源核验](../engine-timing-board-20261013-r1/identity-source-review.json)证明dmesg版本一致，新包新目录修正后执行。旧失败、完整归档不覆盖。历史30帧164.456893ms等待的[重算](../engine-timing-board-20261013-r1/historical-recomputed.json)与本批独立。

认证通用管道遭自动审批拒绝，未创建/未执行推理；专门OpenSSH askpass仅响应指定板端用户认证提示，读取用户已有凭据于内存，不置命令/环境/运行日志，经审批后执行。前期本机脚本引号/GBK错误保留于transport修订记录，未复用失败Session。

测量限制：无DDR-stall独立计数；硬件层计时非法，不能有效求和；SDK tuple单位/累计与层序映射未确认；forward剩余包含SDK调度及未覆盖工作，不能全部归因。3样本且有探针开销，不能外推并发长期或严格整机5Hz。旧DATA调查未恢复，计时异常根因未证。
