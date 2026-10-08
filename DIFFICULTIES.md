# 项目难点索引

最新：[独立显示子进程](ADR/ADR_15.md)已可行，70全参考/视频通过，33个5Hz输入全消费无覆盖；4.99165Hz不舍入判过，inv28 forward221.61ms尖峰未定位，连续分配可靠性仍待。

此前计量难点：[整机串行显示44.31ms/4.22Hz与结束时高阶块耗尽](ADR/ADR_14.md)，原数值/来源通过，5Hz和长期首次分配未验；最小显示线程方案待实施。

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
| D13 | 并发读取的sample时刻可能早于刚发布的Engine初始化/ready时刻，unsigned相减存在下溢风险 | 源码审查后r2增加当前时刻核验/先比较再相减；r1仅构建、未板测，数学/SDK协议不改 | 三窗真实在线生命周期通过；不将风险写为已观察故障 |
| D14 | 首轮27窗网络客户端过晚加入ID450，只收到40帧，虽28推理/490编码正确也无法覆盖来源 | 新外部runner就绪标记与同次工具启动，保持程序/包与门禁，新目录429帧/全部28来源通过；16秒正常对照91帧不足另改独立30秒控制223帧，不降低门禁 | 修正通过；[ADR_09](ADR/ADR_09.md)，原失败完整保留 |
| D15 | AU队列上限不覆盖库内部TCP发送失败，正常网络通过不足以证明慢客户端停止 | 实际库确认500ms发送补偿/错误返回，独立guarded候选注册公共发送错误回调和每连接64KiB发送缓冲；负面拒绝及正常223帧对照通过 | 原r2未含该保护；[ADR_10](ADR/ADR_10.md)，候选/正式集成门检分别记录 |
| D16 | TCP监听在Engine约29秒初始化后才建立；外部等待只捕获refused，1秒连接timeout提前退出，板端0输入/0前向 | 原失败111项/344NoInput及内核同保留；新外部65秒启动等待同时记录refused/timeout，已连接数据流失败不重连，程序/包/Host保持，新目录修正验证 | 验证中；[ADR_11](ADR/ADR_11.md) |
| D17 | 工具启动主机进程的延迟可能越过板端5秒输入等待，27窗开始前便退出 | 保留111项/0输入/0前向/内核同失败；主机先PEER_ARMED，再板端LIVE_READY通过已有进程START放行，硬件预算保持 | 验证中；[ADR_11](ADR/ADR_11.md)，与D14晚加入属于启动协调问题而非模型计算问题 |
| D18 | TCP27第六窗S12_48_349输出逐位回归失配；原比较先于保存，丢失实际错误结果 | 六输入/五完整正确前向/131项/内核同保留；新隔离适配层在原异常后存完整实际值再原样抛出，数学/SDK/门禁保持 | Native契约与构建通过，原因待验证；[ADR_12](ADR/ADR_12.md) |

2026-10-08后续：用户批准先完整保存再原门检以及一次规整。保存缺口已以独立适配层补齐，32前向483,200FP32全部逐位旧参考、S12_48_349当前差异0，未复现旧失配/颠倒，D18根因仍未知。一次规整159.69498ms、普通高阶折算512KiB单位5→91，随后两个进程启动和984编码/864网络全来源/PTS/像素通过；D04本轮恢复有效但长期可靠性未证。27本机审查曾在SFTP未完成时提前报缺文件hash，待完成同数据核验通过，无板测重跑。详见[ADR_13](ADR/ADR_13.md)、[结果](tools/pose-v1/PRESAVED-RESULTS-20261008.md)。

新定位：[forward内部尖峰与有界负载扩展](ADR/ADR_16.md)，隔离诊断已构建，Host/板测进行中；trace结果不混入低日志验收。

r1已定位到inv3 GatherElements192两输入复制后的索引拒绝；未保存失败输入，根因待证。Host/三窗正确，原inv28尖峰未到；[失败与接续](tools/pose-v1/FORWARD-TRACE-RESULTS-20261008.md)。
