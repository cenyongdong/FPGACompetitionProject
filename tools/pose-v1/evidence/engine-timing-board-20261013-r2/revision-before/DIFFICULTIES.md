# 项目难点索引

整理日期：2026-10-13；状态依据截至2026-10-11的实际验证，本次未新增板测。稳定编号D01–D18沿用原索引，D19起补充基础及近期取证问题。每个条目关联决策和证据，完整过程放入ADR及[历史归档](ADR/history/20261013/README.md)，本页不再按批次重复堆叠“最新”。当前项目状态见[PROJECT-PROGRESS](PROJECT-PROGRESS.md)。

## 当前优先问题

- **D25首次读旧数据：未解决，用户要求暂停排查。** 后续方案仅准备，原坏值与两轮晚源保持，不用正确晚值修补首文件。
- **D04 VPU普通连续页：有界演示可运行，永久首启动未证。** 一次重启许可已使用；规整授权仍适用，CMA/内核/BOOT未改。
- **D05 HDMI及D29严格性能/长期：待验。** 编码和主机GUI通过不等于HDMI、严格5Hz或30分钟通过。

## 接入、编排和视频难点（原编号）

| 编号 | 现象与影响 | 已采用处理/验证 | 当前结论与证据 |
|---|---|---|---|
| D01 | 新Case布局与冻结Host类型产生ODR/vector弱符号冲突、Host139 | 助手进入匿名namespace，冻结源不改，Host107回归 | 编排修正通过；[失败审查](tools/pose-v1/evidence/pipeline-20261007-r2/failure-review.json)、[ADR_03](ADR/ADR_03.md) |
| D02 | Host反复解析图导致预算不足，95例后超时 | 拆分Host总预算与硬件预算，外部420秒完成107例，不改拒绝规则 | Host门检修正通过，不扩大硬件预算；[历史超时](tools/pose-v1/evidence/pipeline-20261008-r8/host-timeout-review.json) |
| D03 | Engine约29秒初始化被算入25秒文件编码deadline | 初始化、producer、codec/stall及总预算分开计量 | 有限生命周期通过，demo实际约31秒NoInput初始化；[ADR_02](ADR/ADR_02.md)、[ADR_45](ADR/ADR_45.md) |
| D04 | MVX固件order7/512KiB普通连续页不足，即使总体内存/CMA空闲仍启动失败 | 原六缓冲改两缓冲、单上下文常驻，快照/规整分开；demo首失败规整无效，经一次获准重启成功 | **缓解，永久首启动未修**；无GFP_MOVABLE的普通申请不能直接使用空闲CMA，扩大CMA不是默认解；[ADR_02](ADR/ADR_02.md)、[ADR_27](ADR/ADR_27.md)、[ADR_45](ADR/ADR_45.md) |
| D05 | HDMI输入时序不支持，scanout/安全停止映射未闭合 | 目标改1080p60，编码仍720p；配套未知不猜写 | **待验**，当前demo排除HDMI；[ADR_00](ADR/ADR_00.md)、[ADR_07](ADR/ADR_07.md) |
| D06 | 在线编码、RTSP所有权和实际PTS交接 | owned NV12/packet/AU、有界队列、常驻VPU/独立网络owner | 有界真实来源全链已过，非长期验收；[ADR_08](ADR/ADR_08.md)、[ADR_45](ADR/ADR_45.md) |
| D07 | FIFO积压会显示旧结果 | popLatest；coalesced和overwritten分别计，采样实际时刻产生PTS | Native/有限全链通过，重复不算新姿态；[ADR_02](ADR/ADR_02.md) |
| D08 | PowerShell内嵌多语言引号/命令替换引发生成语法错误 | 独立源码/生成脚本，完整捕获输出并查实际退出码；保留旧构建原型 | 工具脚本修正，不将编译错误误归板端；[ADR_03](ADR/ADR_03.md) |
| D09 | 后台Engine并发模式首读非有限值 | Engine所有者回父主线程，编码仍后台，有限回归通过 | 首版采用主线程；后来旧值异常仍出现，SDK内部原因未证，不泛称线程限制；[ADR_02](ADR/ADR_02.md)、[ADR_17](ADR/ADR_17.md) |
| D10 | live555对象跨线程限制，P帧不能随意覆盖 | AU容量8/非阻塞pipe唤醒，网络事件循环唯一owner，超限停止 | AU与有限在线通过，非任意压力下保证；[ADR_08](ADR/ADR_08.md) |
| D11 | 不同encoded_id的P帧压缩字节可相同，唯一NAL哈希无法判来源 | IDR定位、连续序号/PTS/VCL、10bit ID和解码像素独立核验 | 映射方法通过，不凭单NAL哈希认定来源；[OWNED-AU](tools/pose-v1/OWNED-AU-RESULTS-20261008.md) |
| D12 | PowerShell.Count、Python3.8接口及SDP临时source造成审查误判 | 显式数组/版本兼容检查，SDP与实际客户端计数分开 | 本机审查修正，旧失败保留，无硬件重跑；[修正记录](tools/pose-v1/evidence/owned-rtsp-20261008-r3/local-corrections.json) |
| D13 | sample先于ready发布，unsigned时间相减可下溢 | 先比较再相减，阶段时刻独立核验 | 源码风险已修，非已观察的硬件故障；[ADR_09](ADR/ADR_09.md) |
| D14 | 客户端晚加入只能看视频前缀或后缀，不能覆盖全部来源 | 外部就绪放行和同阶段协调，先实际解码后发送CSI | demo3/60全来源通过；原晚加入失败保留；[ADR_09](ADR/ADR_09.md)、[ADR_45](ADR/ADR_45.md) |
| D15 | AU容量不能约束库内部TCP发送失败/慢客户端 | guarded公共发送错误回调、64KiB请求/128KiB实际缓冲，全局停止失败peer | 负面门检和有限正常回归过，原无guard版本不回填结论；[ADR_10](ADR/ADR_10.md) |
| D16 | Engine初始化前监听不存在，refused/timeout使客户端过早退出 | 有界启动探测，已接受会话不重连；demo输入ready及实际解码门禁 | 当前有界演示通过；[ADR_11](ADR/ADR_11.md)、[ADR_45](ADR/ADR_45.md) |
| D17 | 主机进程工具启动延迟超过板端输入等待 | PEER_ARMED/START协调，独立启动预算 | 启动编排修正通过，不等于模型修复；[ADR_11](ADR/ADR_11.md) |
| D18 | 输出失配先比较后保存导致实际错误缺失 | 独立save-only层先完整保存再原严格比较，诊断失败不掩原错 | 保存缺口已修；**失配根因未修**，关联D25；[ADR_12](ADR/ADR_12.md)、[ADR_13](ADR/ADR_13.md)、[ADR_33](ADR/ADR_33.md) |

## 基础环境、数学与近期取证难点

| 编号 | 现象与影响 | 已采用处理/验证 | 当前结论与证据 |
|---|---|---|---|
| D19 | ARM Host缺TopK/GatherElements/ScatterND注册，common核拒merged_distr | 应用显式注册、全有效分布临时描述适配、公开SDK Host暂存，Gather保持/NPU Matmul保持 | 107例/12注册/59600FP32过；仅当前FP32规格，不支持通用去填充或全CPU Matmul；[ADR_05](ADR/ADR_05.md) |
| D20 | CSI相位校正、unwrap、signed-zero与训练不一致 | 复现训练复指数重建/相位步骤，300真实CSI逐位核验 | 固定真实规格过；人工±π诊断仍有误差，非任意边界等价；[ADR_04](ADR/ADR_04.md)、[300结果](tools/pose-v1/RESULTS-300.md) |
| D21 | SD启动头/文件损坏、镜像校验失败 | 分离imageUSB512字节头、FAT文件哈希；换读卡器仍异常，换SD后启动及扩容通过 | 旧卡链路失败记录保留，未确诊假容量/单一硬件原因；[ADR_03](ADR/ADR_03.md) |
| D22 | Windows缺SDK/CUDA依赖、开发终端不继承；容器无python、签名/stderr处理不符 | 独立Icraft运行依赖、跨窗口核验、主机SDK审计、实际头签名及完整退出码 | 构建路径修正，不将koala设置当项目基线；[ADR_03](ADR/ADR_03.md) |
| D23 | apply融合后原HardOp看似未绑定；次帧旧完成计数提前满足导致同输出 | merge_from唯一追溯1173→七ZG组，安全帧reset(1)，确认0/最终745 | 正式三帧/重复及后续有限链通过，不能推广其他图计数；[ADR_05](ADR/ADR_05.md) |
| D24 | CPU Matmul参考阻塞、候选排名交换及训练分支衰退 | 独立ORT1.23.2 CPU固定环境直接比较；完整同槽/最佳候选误差分别报告，固定2024部署；训练旁支隔离 | 27样本获用户部署阶段验收，query身份/定点原因未完全证明；训练500轮未完成；[ADR_04](ADR/ADR_04.md) |
| D25 | 192索引/582更新与独立ZG DATA出现前输入片段，晚源可正确 | 保留首次Host值、元数据、计数、上游、两轮晚read；独立双源/较高地址/真实生产组/租约对照 | **未解决且暂停**。最新inv94 DATA96同上一B、INDEX对、四晚源对；首次指纹在保存后记录，非早期即时采样。不能唯一归因CPU ScatterND/NPU/DMA/cache；[ADR_34–44入口](ADR/README.md)、[最新原结果](tools/pose-v1/PRODUCER-PREPARED-RESULTS-20261011.md) |
| D26 | reset前目录创建915ms及I/O等待使绝对时隙超限 | 分段单钟/CPU/缺页观测、准备后二次截止，放行前预建唯一目录及一次令牌 | 目录热领取改正；输入保存仍max166.999ms，FS/存储/调度责任未证；[ADR_41](ADR/ADR_41.md)、[ADR_43](ADR/ADR_43.md)、[ADR_44](ADR/ADR_44.md) |
| D27 | 归档权限/符号链接使Host审查解包拒绝 | 保留原tar和partial，仅普通文件字节+精确链接元数据审查，非法路径拒绝 | 本机审查修正，无失败Session重跑；[ADR_44](ADR/ADR_44.md) |
| D28 | demo入口缺Engine目录/Producer配置，播放器失败后归档回传延迟 | 独立demo_engine集中配置，先取消播放器并始终归档，各修订新包新目录 | 三/60窗口GUI全链及正常回收过，原失败不覆盖；[ADR_45](ADR/ADR_45.md) |
| D29 | 粗时钟与整机争用导致4.998467Hz，5.05Hz诊断又出现坏值 | QPC发送绝对计划、单steady_clock分段、profiling-off；核心与整机、重复画面与新姿态分别统计 | **严格5Hz/长期未过**；不调频掩故障，不将5.24655核心当整机；[ADR_14](ADR/ADR_14.md)、[ADR_32](ADR/ADR_32.md) |
| D30 | 执行规范文档持续堆进度/难点，历史“当前”和许可相互冲突 | Agents只存规则，单一进度总览、稳定难点索引、主题历史归档与迁移清单 | 本次文档整理完成；不改变阶段结果或权限；[ADR_46](ADR/ADR_46.md) |

## 本轮源码迁移与环境核验

| 编号 | 现象与影响 | 处理与证据 | 剩余边界 |
|---|---|---|---|
| D31 | 新工作区缺旧.local参考/环境，版本文件导出别名容易改错核心；FPAI起初停止 | 核验git worktree，恢复原NumPy2.2.5及原CPU107/三窗口参考；启动既有FPAI，不安装。新核心52份C++逐token、926冻结文件、11本机、CPU107和三窗口通过。[ADR_47](ADR/ADR_47.md) | 旧缓存不是永久来源保证；后续先核路径与身份，不能将默认Python版本或导出名当基线 |
| D32 | CPU桥164ms等待被误解为纯NPU计算或可全消除的交接；缺少DDR-stall独立计数 | 新独立计时副本记录墙钟/线程CPU/rusage、桥各项、SDK raw与硬件层ms，用区间并集排除重复累计；13分析合同、Linux采样和ARM编译通过。[程序](software/engine_timing/README.md)／[证据](tools/pose-v1/evidence/engine-timing-20261013-r1/README.md) | **尚无新模型/板端计时**；SDK tuple单位/累积、硬件层序映射待核实；纯算术/DDR停顿/精确SDK调度输出未知，不由残余推定 |

## 维护与追溯

新问题追加稳定编号；同一问题更新状态和对应ADR结果，不按每个实验重复造编号。新架构取舍新建ADR，原始失败保留，未证假设不写成根因。旧D01–D18的逐批原文及历史状态见[difficulties-before](ADR/history/20261013/difficulties-before.md)，从Agents迁出的实施过程见[主题归档](ADR/history/20261013/README.md)。

2026-10-13重构回归有实际CPU107和三窗口设备验证；旧DATA问题未修且继续暂停，83/100管理估计保持。原文档整理阶段“无设备操作”只适用于其历史范围。
