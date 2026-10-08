# 项目难点索引

每项记录现象、影响、证据、判断和当前结果。未查明不写成确定根因；原报告/失败目录保留，有决策取舍时使用独立ADR。

| 编号 | 难点与影响 | 当前判断/处理 | 状态与证据 |
| --- | --- | --- | --- |
| D01 | 新全局Case与冻结Host源不同布局，vector弱符号冲突导致Host139 | 新助手进入匿名namespace，原冻结源保持 | 已修正并Host107回归；[r2证据](tools/pose-v1/evidence/pipeline-20261007-r2/failure-review.json) |
| D02 | Host图重复解析使60秒预算超时；r8在300秒完成95例后超时 | 首次解析2447.24ms；r8估计约338秒，新外部420秒完成107，拒绝规则不改 | 本批完整通过；[r3](tools/pose-v1/evidence/pipeline-20261007-r3/failure-review.json)、[r8历史超时](tools/pose-v1/evidence/pipeline-20261008-r8/host-timeout-review.json) |
| D03 | Engine初始化约29秒误计入文件编码25秒deadline | 有界producer时间独立记录，codec25秒/stall5秒及总180秒保持 | 有限回归通过；[r5证据](tools/pose-v1/evidence/pipeline-20261008-r5/combined-failure-review.json) |
| D04 | MVX固件512KiB连续分配失败，阻断进程启动 | r7确认六缓冲耗尽普通高阶块；隔离请求2缓冲、实际返回2，CMA保持 | 本轮三次启动回归通过，非长期保证；[ADR_02](ADR/ADR_02.md)、[启动证据](tools/pose-v1/VPU-STARTUP-RESULTS-20261008.md) |
| D05 | HDMI时序/scanout/安全停止映射未建立 | 目标1080p60，配套不明不猜写 | 待验证；[V0配套](tools/pose-v1/V0-VIDEO-PAIRING-20261007.md) |
| D06 | 在线编码→RTSP所有权/实际PTS及整机争用尚未验证 | owned字节、有界队列、常驻上下文分阶段接入，重复帧不计新姿态 | 待实现/验收；[F0接续](tools/pose-v1/PIPELINE-NEXT-20261008.md) |
| D07 | 容量2画面队列若按FIFO采样会在积压时显示旧结果 | 采样使用popLatest，合并跳过旧帧独立计coalesced；满队列覆盖另计overwritten；实际PTS在源选择后取时刻 | Native及最终r6三/27窗口验证通过，无固定流丢弃；[当前ADR](ADR/ADR_02.md) |
| D08 | PowerShell内嵌Python/C++或shell文本的引号与命令替换导致本机生成语法错误 | 源文件采用直接补丁、复杂生成改独立Python文件；依赖步骤检查退出码。原编译原型保留，错误未执行板端硬件 | 已改正工具路径；r1/r3/r4仅本机构建原型，r2只Host，最终r5另核验 |
| D09 | r5常驻编码并行下第一次模型读取出现非有限值，阻断三/27窗口验收 | 七ZG/七Host回调与745/ready完整、内核不变。r6只将Engine所有者回主线程，编码仍后台，32完整前向与987视频核验通过 | 首版采用实测主线程模式；SDK内部原因未证，不泛称线程限制；[失败](tools/pose-v1/evidence/resident-20261008-r5/resident-three-failure-review.json)、[结果](tools/pose-v1/RESIDENT-RESULTS-20261008.md) |
