# 项目难点索引

每项记录现象、影响、证据、判断和当前结果。未查明不写成确定根因；原报告/失败目录保留，有决策取舍时使用独立ADR。

2026-10-08已按用户要求补全从项目开始至当前的主题归档，入口[ADR索引](ADR/README.md)。历史编号D01–D09保持；完整早期问题按下表定位，不把已解决的问题与未查明原因混为一谈。

| 历史主题 | 难点及解决路径 | ADR |
| --- | --- | --- |
| 平台/工具/证据 | FPGA约束和跨EDA IP；坏启动介质→换卡；扩容/SSH；编译SDK签名/日志；LF、gate与登录shell；ODR与预算 | [03](ADR/ADR_03.md) |
| 数据/模型/训练 | 300真实CSI一致、人工相位边界仍失败；独立ORT；排名/数值用户验收；26迁移与500轮分支退化旁支 | [04](ADR/ADR_04.md) |
| 异构推理 | 五缺注册/全有效布局；SDK显式搬运；融合1173追溯；跨帧绝对计数→reset(1)安全边界 | [05](ADR/ADR_05.md)、[01](ADR/ADR_01.md) |
| 性能/应用 | 单时钟/profiling-off/lazy消息；生产Engine；TCP完整窗口单槽；显示投影独立于数学 | [06](ADR/ADR_06.md) |
| 视频/传输 | 格式顺序/MPLANE/cookie；owned packet/PTS；RTSP配套/保活；HDMI尚缺映射 | [07](ADR/ADR_07.md) |
| 启动/常驻 | 普通高阶页6→2缓冲；队列popLatest；Engine主线程实测；在线模块契约 | [02](ADR/ADR_02.md)、[08](ADR/ADR_08.md) |

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
| D10 | live555外部线程通知限制，已编码参考链不能像画面队列一样随意覆盖 | 独立AU模块/容量8通道，生产者仅写非阻塞pipe，网络事件循环唯一owner，超限拒绝不丢P帧；Native/ARM及200帧门检通过 | 实时VPU慢客户端/整体争用仍待；[ADR_08](ADR/ADR_08.md) |
| D11 | 不同encoded_id的P帧压缩字节可能相同，按唯一NAL哈希建立参考失败 | 首IDR定位、连续帧序号/实际PTS和逐帧VCL比较，再解码10bit ID与原像素独立确认 | 493参考AU/200网络解码通过；不能仅由单NAL哈希判定来源；[结果](tools/pose-v1/OWNED-AU-RESULTS-20261008.md) |
| D12 | PowerShell属性集合.Count并非集合元素总数；旧OpenCV环境为Python3.8，缺removeprefix/is_relative_to；SDP探测临时source额外计数 | 使用显式数组计数、兼容3.8的前缀/父目录检查，分别核验0号SDP无AU及1/2实际流和三次释放 | 本机预检/审查错误原目录保留，无硬件重跑；[本轮修正](tools/pose-v1/evidence/owned-rtsp-20261008-r3/local-corrections.json) |
