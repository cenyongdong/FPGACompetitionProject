# 2026-10-25：180-query实测、归档修正与HDMI启动停止

本轮用主机模拟CSI输入，在原BOOT上运行180-query主图，计划52,800帧/30Hz，**未启用HDMI，未接入CSI实采**。实际完成7,840次推理，保留7,840份完整有效首次输出，其中7,839帧收到最终确认，最后1帧保留但未确认；完整原值共584,424,960字节。全部已保存记录通过180候选有限性、身份及selection检查；本批来源不重复，不能据此宣称重复输入一致性或模型精度通过。[完整归档解析](../../.local/pose180-pipeline-20261025-r1/hardware-analysis.json)、[Host实际汇总](../../.local/pose180-pipeline-20261025-r1/hardware-host-originalboot/summary.json)

停止原因是最后一次Host raw归档写回调耗时**1,019.7889ms**，触发既定1秒最老未确认帧保护；该帧板端拥有值与PC已归档净数据74,160字节逐字节相同。最后一帧板端处理17.41478ms，其中forward为1.26182ms，因此本次停止不能归因为NPU长尾。Host关闭连接后，板端报告`Truncated/idle CSI connection`并停止；没有SDK异常或数据校验失败证据。严格30Hz、全部逐帧33.333ms及原计划长期稳定性均未通过。[归档与板端原值核对](../../.local/pose180-pipeline-20261025-r1/hardware-failure-analysis.json)、[资源及末帧耗时](../../.local/pose180-pipeline-20261025-r1/hardware-resource-analysis.json)

该批已清理，退出后设备占用为空，boot_id保持不变，BOOT写入/重启均为0，内核日志不变，最低MemAvailable为732,532KiB。SDK与模型未改，D48精度仍未验收。[板端退出与清理结果](../../.local/pose180-pipeline-20261025-r1/hardware-board-originalboot/outcome.json)

主机修正已提交`d7ac1277`：运行归档迁至C盘NVMe，在`HOST_READY`及发包前全量预写目标文件并`fsync`，将文件分配和有效数据扩展移出逐帧归档路径；完整首次输出、固定缓冲、归档背压及1秒保护保持。修正后的900帧localhost mock全部原值匹配，900次归档ACK/最终确认齐全、在途峰值8，退出并释放资源；注入200ms等待后仍明确`strict30Hz=false`。[900帧mock结果](C:/Users/cenyongdong/FPGACompetitionRuns/pose180-pipeline-20261025-r2/localhost-mock-900/mock-summary.json)

另用生产归档预备函数及有界writer写入52,800条、3,935,923,200字节（约3.94GB）：预写/flush约3.208秒，记录写回调p99为0.9132ms、最大9.461ms，无超过1秒回调，首尾原值一致，临时文件已回收。**这两项均为软件验证，不能替代NPU或HDMI实板稳定性结论。**[生产writer测试结果](../../.local/pose180-pipeline-20261025-r1/ssd-archive-probe.json)

新HDMI包`pose180-hdmi-20261025-r2`获用户明确批准后复用r45镜像，实际完成1次候选启动。串口接收标记验证后才安装/重启；候选上线后先将磁盘BOOT恢复原版并完整读回，再执行一次同boot启动准入。原生启动历史为PS AR=0、R=6；当前160位状态为`0xb00080002c00000000000000`，置位58/59/61/79/92/93/95。除原已知项外新增bit79 `AXI_AUXM_RCAM_UNDERFLOW`，超出既定有限消费允许范围，准入返回`Unknown native mandatory/capacity status`并停止。首个协议窗口中的容量超限标志为false，不能将报错文案直接解释为容量耗尽；本轮没有扩展豁免、执行消费、打开SDK或发HDMI START。[首次启动原值](../../.local/pose180-hdmi-20261025-r2/candidate-evidence/startup/observe-before/capture/result.json)、[原生协议窗口](../../.local/pose180-hdmi-20261025-r2/candidate-evidence/startup/protocol-before/raw.decoded.json)、[准入结果](../../.local/pose180-hdmi-20261025-r2/candidate-evidence/startup/before-seed.json)

本新包已按批准执行唯一一次原BOOT回退，实际为1候选/0 SDK/1回退，关闭后所有余额为0；没有重试候选或推理。最终boot_id为`2d5f618a-7891-493e-a519-714c0edcaa3c`，九个启动文件、六SDK库及FPGA operating核验通过，设备占用为空。两个串口捕获已关闭，主机服务器、pacer和SSH反向端口均已回收。[关闭结果](../../.local/pose180-hdmi-20261025-r2/closed.json)、[最终身份核验](../../.local/pose180-hdmi-20261025-r2/final-audit.json)

因此，当前180-query完整回传的实板样本已取得，但归档修正尚未重新实板验证；HDMI联合负载未开始，持续实屏、严格逐帧实时和整机长期稳定性均未通过。D45根因调查及旧DATA仍保持原暂停边界，D48精度仍未验收。后续需新的明确板测范围，不能复活本包或r53额度。
