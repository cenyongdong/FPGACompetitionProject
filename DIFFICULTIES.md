# 项目难点索引

更新：2026-10-19。用户已唤醒复位／启动排查，暂不做HDMI长期。已查明此前按键指引错误：r9的F8 sys_rst实际对应PL_KEY1／SW6，SW7是E7，不能用其按后0/2/2认定F8复位未生效。r21正确SW6实测已使0/2/2→0/0/0，观测器CSR复位生效；该启动本来健康，D45根因仍未定。[引脚纠正](FPGA/hdmi_candidate/PIN-CONTRACT.md)、[当前方案](tools/pose-v1/evidence/hdmi-reset-meter-20261019-r21/PLAN.md)。r13三窗新推理→HDMI结果保持已通过。

| 编号 | 现象与影响 | 已采取处理及效果 | 尚未解决／证据边界 |
|---|---|---|---|
| D44 | 首次HDMI START出现reader fault2，未采纳首帧 | 保存失败并STOP；用户明确要求重测后，在已归档安全idle条件下清错、新进程两图案和后续骨架显示通过 | fault将局部burst条件、RRESP、RID或RLAST／拍数异常汇总，不能区分具体原因；重测通过不是首启修复。早期独立failure-review已不在当前树，原已记录结论保留，不能补造原始报告；见[工程说明](FPGA/hdmi_candidate/INTEGRATION.md) |
| D45 | 同r9跨启动偶发HP2／HDMI持续RVALID背压，SDK参数上传或4KiB DMA可失败 | 已做分段观测、无SDK父进程／SDK子进程隔离、加载顺序与按键清零校准；r13健康启动时四档DMA和三窗新推理→HDMI通过 | Open前可复现但进程已加载SDK，不能唯一归因BOOT；r20实际按SW7而r9 sys_rst在SW6，故该结果不能验证F8复位。r21已证SW6清零观测器，随后加载／Open五段健康；未捕获故障启动的复位恢复对照，根因未修，见[暂停汇报](FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md)及[r20原值与结果](tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/REPORT.md) |

## 当前优先问题

- **D45启动稳定性：未解决，已唤醒诊断。** 需区分外部按键电平、内部复位边沿和CSR读回，再判断BOOT初始化／库加载／Open的影响；独立复位见证尚未实现。健康样本不构成可靠性验收。
- **D44首次reader故障：未定位。** 后续显示成功与原失败分别保留；不能按“未再出现”关闭问题。
- **D29严格实时、D41长尾与HDMI长期：未验收或未解决。** 原共享图独立串行30分钟不替代HDMI并发长期，后者须用户单独批准。
- **D25旧DATA：未解决，独立暂停。** D43 FAT来源问题也未修。D04 VPU连续页属于保留的旧演示分支，ADR_49新HDMI链不启动VPU。

## HDMI接入中已处理的问题（D05）

| 问题 | 采用的方法 | 结果及适用限制 |
|---|---|---|
| 扫描时钟与AXI／停止语义不完整 | 独立像素时钟；仅握手计读拍；按4KiB拆burst；STOP排空后给出匹配ID的safe_idle；双时钟FIFO与CDC约束 | 有限全帧／像素、背压、边界和停像素时钟后STOP仿真通过，动态实屏及释放通过；原RTL风险不直接证明原BOOT根因 |
| TMDS时钟图案常量错误 | ASCII字符串改为显式10位二进制常量，使用Lite目标参考模型 | 128周期模型占空比20%→50%；后续真实色条／骨架可见。数字模型通过不等于完整电气合规 |
| 工具库／扩展PS不匹配 | 核对原厂2018.3／030ai配套，按已批准范围备份补丁；用原厂JFM实现与Procise位流后处理 | 扩展PS及整机构建路径闭合；不继续用通用PCPU7导入失败作为当前阻塞，不将该路径推广到任意版本 |
| HDMI reader路径时序不合格 | 在隔离r9来源中缩短4KiB边界谓词，组合及有限状态比较后再实际实现、STA复核 | r9 setup／hold +0.030／+0.023ns；原AI两个Min Period例外保留，raw_timing_pass仍false；先前r5／r6／r8失败不回写 |
| 共享推理与显示设备／帧块所有权 | 导出副本显式传同一Device；PS复用原绘图、适配RGB565；新响应、采纳ID及STOP排空确认后释放 | r13三次新推理、三帧采纳、数值门与现场切换通过；不是严格实时／长期或跨启动修复 |
| 诊断工具未覆盖真正的库加载阶段、拒绝前漏存原值 | 纯POSIX父进程独立映射CSR，SDK子进程分开加载／Open；五寄存器先保存，再做初始代次门检 | 9类观测／4类协议及后续5类原值自测、ARM构建完成；r20实际验证非零初始值零命令退出。修复了取证缺口，没有修复硬件异常 |

源码、工具、完整输出与归档入口见[INTEGRATION.md](FPGA/hdmi_candidate/INTEGRATION.md)。D42／D43保留在后表，按原编号维护，不按每轮实验新增问题编号。

## D45的事实、推断与未知

已验证：64B成功只覆盖HC0，不能证明共享HP2正常；r12已在首笔DMA前看到HDMI异常；r14和r18在显式Open前复现，因此不能把Open或多笔DMA拥塞当作已确定的首次触发点。它们的进程已加载SDK，也不能据此证明纯BOOT初始化一定出错。

已采取：同r9的返回ID／位宽／S00与S01连线审查及有限64笔连续读、并行读、背压仿真未发现直接错线或误发；高位截断、仲裁／缓冲区异常仍未取得实板逐事务证据。网表中跨层级反相优化不应当作错线，“最后25个差异门”也不等于25处错误。

复位尚待证明：静态RTL／DCP已有F8高有效sys_rst路径。2026-10-19直接复核原厂手册、原理图与r9约束后，发现F8实际为PL_KEY1／SW6，此前误称PL_KEY2／SW7；E7／SW7在r9连接rx_gtx_full_reset。因而r18／r20的按SW7后未归零不能证明F8复位失效。r21已验证正确SW6使观测器初始代次归零，随后纯CSR及加载／Open五段健康；这证明CSR域复位生效，不证明所有HP2／MIG复位与释放均正确，D45不能直接归因缺少复位。

当前执行点：r21已关闭并回原BOOT，正确SW6功能验证通过；尚需故障启动下的正确按键对照。用户已拔网线，串口只读命令通道可用，未重编产品位流或开展长期负载。此前原值保留在[暂停汇报](FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md)。

## 接入、编排和视频难点（原编号）

| 编号 | 现象与影响 | 已采用处理/验证 | 当前结论与证据 |
|---|---|---|---|
| D01 | 新Case布局与冻结Host类型产生ODR/vector弱符号冲突、Host139 | 助手进入匿名namespace，冻结源不改，Host107回归 | 编排修正通过；[失败审查](tools/pose-v1/evidence/pipeline-20261007-r2/failure-review.json)、[ADR_03](ADR/ADR_03.md) |
| D02 | Host反复解析图导致预算不足，95例后超时 | 拆分Host总预算与硬件预算，外部420秒完成107例，不改拒绝规则 | Host门检修正通过，不扩大硬件预算；[历史超时](tools/pose-v1/evidence/pipeline-20261008-r8/host-timeout-review.json) |
| D03 | Engine约29秒初始化被算入25秒文件编码deadline | 初始化、producer、codec/stall及总预算分开计量 | 有限生命周期通过，demo实际约31秒NoInput初始化；[ADR_02](ADR/ADR_02.md)、[ADR_45](ADR/ADR_45.md) |
| D04 | MVX固件order7/512KiB普通连续页不足，即使总体内存/CMA空闲仍启动失败 | 原六缓冲改两缓冲、单上下文常驻，快照/规整分开；demo首失败规整无效，经一次获准重启成功 | **缓解，永久首启动未修**；无GFP_MOVABLE的普通申请不能直接使用空闲CMA，扩大CMA不是默认解；[ADR_02](ADR/ADR_02.md)、[ADR_27](ADR/ADR_27.md)、[ADR_45](ADR/ADR_45.md) |
| D05 | HDMI接入、读帧与资源生命周期 | r5下图案／历史骨架与STOP通过；后续r9下r13新三窗推理→HDMI及现场确认通过，处理方法见上表 | 有界闭环已完成；D44／D45、严格实时及长期分别保留；[工程与证据](FPGA/hdmi_candidate/INTEGRATION.md) |
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
| D23 | apply融合后原HardOp看似未绑定；次帧旧完成计数提前满足导致同输出 | merge_from唯一追溯1173→七ZG组，安全帧reset(1)，确认0/最终745 | 正式三帧/重复及后续有限链通过，不能推广其他图计数；[ADR_05](ADR/ADR_05.md) 15日新去Scatter图独立引擎以公开metadata完整追溯1158→五组/736且三次完成736，未套旧表；[报告](tools/pose-v1/evidence/noscatter-board-20261015-r1/REPORT.md)。 |
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
| D32 | CPU桥164ms等待被误解为纯NPU计算或可全消除的交接；缺少DDR-stall独立计数 | 独立副本墙钟/线程CPU/rusage及桥区间并集；13分析合同、Linux采样、ARM编译及baseline/wall各3窗口逐位通过。新等待162.294ms，期间线程CPU161.908ms。[实测表](tools/pose-v1/evidence/engine-timing-board-20261013-r2/timing-table.md) | 等待包含大量CPU活动；SDK tuple单位/累积、硬件层序映射仍待核实；纯算术/DDR停顿/精确SDK调度未知，不由残余推定；未换模型、旧DATA暂停 15日去Scatter实测forward16.010ms后末端仍等157.975ms，Engine184.163ms；等待移位而非消失，纯NPU/DDR仍未知；[报告](tools/pose-v1/evidence/noscatter-board-20261015-r1/REPORT.md)。 |
| D33 | 计时预检用历史dmesg版本与当前proc/version比较，误报内核变化 | r1前向0次，保存停止；历史/当前dmesg版本完全相同。新r3包改同源比较，新r2板端目录执行。[来源审查](tools/pose-v1/evidence/engine-timing-board-20261013-r1/identity-source-review.json) | 比较来源问题已修；原失败和封存包不覆盖；未更改内核 |
| D34 | SDK getLayerTime(745)返回含负值及巨大值，硬件总耗时无法可信计算 | SDK模式第1帧数值通过后采集745项，其中215项负值；原值完整保存，立即停止、未执行剩余2帧、未重试。[原值](tools/pose-v1/evidence/engine-timing-board-20261013-r2/sdk-return/run-sdk/results/hardware-layers.jsonl) | SDK计时数据/数量与层序语义根因未证，不删除负值、只取有效前缀或推定纯NPU时间；与旧DATA异常不可等同 |
| D35 | 2026-10-14正式核心复核首次SSH到192.168.126.49:22连接超时，新板测无法启动 | 保存exit255和原连接日志，未部署/未运行CPU107或三窗口，未自动重试；新11组本机和ARM构建已过。用户选择稍后恢复板端连接。[本轮证据](tools/pose-v1/evidence/core-check-20261014-r1/README.md) | 供电/网络/IP状态未核实，不推定源码或SDK故障；新板测及Agents开发基准规范待连接恢复 15日连接恢复并完成独立去Scatter三窗，不替代原正式核心CPU107/整机复核；[报告](tools/pose-v1/evidence/noscatter-board-20261015-r1/REPORT.md)。 |
| D36 | 迁移保留encodeNv12File/encodeNv12Producer/serveOwnedAccessUnits/mixed_host_check声明，当前demo目标不提供定义 | 实际CMake与ARM符号表确认；当前链使用encodeResident/serveGuardedAccessUnits及Engine，无上述未定义调用；[接口手册](software/core/INTERFACES.md)明确保留声明的可链接范围 | 当前链编译通过；后续不能仅据声明新增调用或为补齐旧入口混编历史实现，扩展须按实际需求设计与验证 |

## 维护与追溯

| 编号 | 现象与影响 | 处理与证据 | 剩余边界 |
|---|---|---|---|
| D38 | Icraft3.39.0显式输入要求NOP scale/mean/swap全填，XIR **C不接受为CLI layout；资料描述与当前签名有差异 | r1/r2网络加载前参数检查exit1，分别保留实际TOML/调用/失败；依文档NOP及实际CLI FD建立新r3。五阶段exit0、XIR **C、FP32端口、RAW MD5/SHA核验通过。[证据](tools/pose-v1/evidence/icraft-no-scatter-20261014-r1/README.md) | 主机配置问题已解决，新FP16候选1158 HardOp/四Host/ScatterND0留model；原量化TOML未找到不能伪称全文复原。736非板测阈值，原Engine/融合/数值/性能未适配，旧DATA暂停 |
| D39 | 共享细化改变批形状后FP32/FP16非逐位；误差与置信度范围需明确区分 | 固定epoch442/两TopK，原FP32/导出/转换及旧失败保留。全候选v1第三窗5.524271728mm失败见[原复验](tools/pose-v1/evidence/shared-gate-policy-20261015-r1/REPORT.md)。用户后明确仅score>0.2检查3mm，按[ADR_48现行v2](ADR/ADR_48.md)实现21自测、新ARM构建；三份保存输出C++/NumPy复核3/3符合，受检最大0.9765625mm，原超限槽score0.001296997为位置排除对象，全部原值/分数/有限性仍检查。[最新证据](tools/pose-v1/evidence/shared-confidence-gate-20261015-r1/REPORT.md) | 用户已按新范围认可当前阶段；本轮无新板端成功进程或完整数据集/长期验收。FP16步长特征及本组三窗误差集中背景为观察事实；物理偏置/训练约束不足漂移仍未证，不证旧DATA复发或已修。旧失败不改、正式基线门禁和DATA暂停保持 |
| D40 | 稳定性观测器假定/proc/PID/task/PID/children存在，Lite内核没有该可选接口，首次初始化被观测器中止 | r1原失败/强制终止与无完整帧保持；只读确认status/smaps_rollup可用、children缺失，r2只将该项标为不支持，RSS/PSS/FD/线程及进程组清理不变；4项本机兼容测试、经用户明确允许后的3窗与30秒/1131次实板通过。[失败](tools/pose-v1/evidence/shared-stability-20261015-r1/REPORT.md)、[修复与后续](tools/pose-v1/evidence/shared-stability-20261015-r2/REPORT.md) | 观测器兼容缺口已修，原中止不是模型崩溃/泄漏证据；后续30分钟/62945次独立实板及完整原值复核通过，未观察到持续内存/句柄增长；仅三冻结来源串行，无视频叠加。归档SSH超时监测原压缩进程并取回，不重跑推理 |
| D41 | 共享图30分钟串行推理出现11次>1秒时延尖峰，最大process4158.13099ms，forward4150.52165ms、CPU20.177ms；全部数值仍过、无崩溃/内存增长 | 全62945次无裁剪：均值23.27822ms、P9523.45126ms、P9924.49497ms；保留逐帧、粗粒度资源与vmstat，movable分配停顿/回收存在但未能对应根因。[长尾证据](tools/pose-v1/evidence/shared-stability-20261015-r2/latency-tail-analysis.json)、[报告](tools/pose-v1/evidence/shared-stability-20261015-r2/REPORT.md) | 运行完成及内存观察通过不代表实时最坏时延通过；阻塞发生在forward区间，SDK/调度/页回收/设备责任未知；未追加定位负载或恢复旧DATA调查 |
| D42 | 跨重启/tmp暂存被系统清理，首次BOOT恢复找不到源文件 | 在挂载/写入前失败；确认/usr/lib/tmpfiles.d/tmp.conf配置D /tmp，原回传BOOT主机SHA保持。新/root持久目录重新传入，r2恢复及全部启动文件身份通过 | 已修复本次恢复路径，不重写原失败；跨重启资产须用持久路径并保留主机完整回传，原一次候选启动未重复；[当时总结](FPGA/FPGA-WORK-SUMMARY-20261016.md) |
| D43 | FAT启动分区脏标志与两条未引用簇链，来源未明 | 内核报未正常卸载；两FAT相同、FAT16 clean/no-hard-error位均置位，但BPB状态字节1。只读全目录链遍历未见交叉/环/长度错误，另有2168个未引用簇约33.9MiB；现有启动文件SHA不变，板端无fsck.fat | 原阶段停止写入，后续仅按逐包明确授权临时替换并还原BOOT，未修复FAT；无操作前快照，不能归因或称完整fsck通过；[原元数据](tools/pose-v1/evidence/hdmi-board-candidate-20261016-r1/FAT-metadata-snapshot) |

新问题追加稳定编号；同一问题更新状态和对应ADR结果，不按每个实验重复造编号。新架构取舍新建ADR，原始失败保留，未证假设不写成根因。旧D01–D18的逐批原文及历史状态见[difficulties-before](ADR/history/20261013/difficulties-before.md)，从Agents迁出的实施过程见[主题归档](ADR/history/20261013/README.md)。

2026-10-13重构回归有实际CPU107和三窗口设备验证；旧DATA问题未修且继续暂停，83/100管理估计保持。原文档整理阶段“无设备操作”只适用于其历史范围。

本次HDMI文档整理前原文及迁移说明见[修订记录](tools/pose-v1/evidence/hdmi-documents-20261018-r1/revision.json)。历史失败、原值和完成清单不回写。
