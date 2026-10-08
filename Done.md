# 已完成工作记录

## 2026-10-08：VPU启动最小修正与有限常驻工作者完成

### 工程内容总结

r7快照与实际amvx指令确认六缓冲REQBUFS耗尽普通高阶页，固件512KiB走__alloc_pages_nodemask而非直接CMA。新隔离请求2缓冲、两端实际返回2，映射19.9→6.64MiB；Host107及三次独立启动/24前向/30编码通过，无规整或重启，CMA256/SDK/BOOT保持。[启动结果](tools/pose-v1/VPU-STARTUP-RESULTS-20261008.md)。300秒Host95例超时保存，新外部420秒完成107，硬件180秒不变。

新增同进程owned画面/packet与容量2最新画面队列、实际steady_clock PTS及停止传播。r5后台Engine首次非有限输出失败保留；r6仅改回主线程所有者、编码仍后台，Host107/三帧4前向/27＋重复28前向均完整通过。32次输入/输出483,200 FP32逐位原板端，987编码全解码源/ID正确、5530关节核验；两阶段无队列覆盖/合并、内核同，退出0/stderr空。程序f4f15b7e…e7060，402载荷/23来源。活动预览197帧已回传核验。[完整结果/视频](tools/pose-v1/RESIDENT-RESULTS-20261008.md)。

### 对后续开发的参考

规范新增ADR优先新编号与逐难点记录；独立ADR_02和DIFFICULTIES索引已建立，启动与所有者方法分别实测记录。主线程模式有效不证明SDK一般线程限制；两缓冲三次启动不保证任意碎片状态。当前有限工作者测试不是永久服务或在线RTSP/整机吞吐，重复帧不算新结果，预览名义10fps不代替实际PTS。后续owned AU/live555接入、色彩/HDMI配套及整机长期继续按门检推进。测试/SSH/SFTP全部关闭，无后台；新恢复点保存，管理81/100不因记录文件自动增加。

## 2026-10-08：真实推理画面有限接入VPU；启动稳定性问题定位

### 工程内容总结

新增隔离owned NV12/packet接口与同进程有限检查器，原Engine/数学/桥/模型/SDK/BOOT/VPU文件入口保持。r6构建13693d45…f8f086，350包/21来源/15头文件通过。Host107/12注册/59,600 FP32及六拒绝通过；两次成功各八完整前向逐位旧参考、四新画面→十编码帧（两NoInput＋八真实重复画面），NV12逐位NumPy、两H264逐字节一致。主机十ID/112关节可见性核验，MP4已回传；成功阶段均exit0/stderr空/dmesg同。详见[结果/视频](tools/pose-v1/PIPELINE-RESULTS-20261008.md)、[汇总](tools/pose-v1/evidence/pipeline-20261008-r6/completion-review.json)。

r2全局Case ODR类型冲突通过匿名namespace隔离；r3原60秒Host预算恢复已用300秒；r5近29秒Engine初始化误入25秒编码期限，通过分别记录有界producer/codec时钟修正。r4与r6新进程重复出现MVX固件order7/512KiB连续页分配失败；一次0.193秒显式内存规整后新目录成功，不能据此宣称启动修复。所有失败及清理记录保留。

### 对后续开发的参考

当前完成有限串行接入与内容对照，**无规整的进程重复启动可靠性仍未通过**。普通可用内存不证明高阶连续页可分配；需在REQBUFS/prime/STREAMON期间取证，不把完成后的页数当分配现场。规整不是生产政策，不静默写sysctl或自动重试。下一[门检](tools/pose-v1/PIPELINE-NEXT-20261008.md)先分配时序取证，再依据证据修正启动，之后常驻编码器/真实PTS/有界工作者与在线RTSP；常驻避免服务内重开，不代替首次启动修复。HDMI/显式色彩/整机5Hz/30分钟保持待验。会话与测试已关闭，新检查点保存，管理81/100保持。

## 2026-10-07：独立RTSP传输/重连与标准播放器首批完成

### 工程内容总结

用户已审查动态骨架视频并要求继续。复用厂商live5552024.11.28和配套OpenSSL头/静态库，新增SDK无关有界RTSP回放。原r5输入/编码、推理/渲染/SDK/BOOT保持，无新安装。r1缺ARM配套头路径失败保留，r2构建454d21c2…58fb2。
首客户端缺保活导致10秒会话回收，88正确帧和全记录保留；仅客户端补每3秒GET_PARAMETER，新r3两个会话各100帧通过，实际SPS/PPS/IDR加入/TEARDOWN/重连/FU-A/NAL/9000 ticks时基均核验。200帧全解码像素逐位r5；r4现有OpenCV/FFmpeg直接RTSP另100帧通过。两60秒服务上下文退出0，内核/BOOT/SDK保持、sources/端口全部归还。stderr厂商诊断行原样保留并分类，不谎称为空。[完整结果/录制视频](tools/pose-v1/RTSP-RESULTS-20261007.md)。

### 对后续开发的参考

SPS实际video_signal_type_present_flag=0，显式色彩仍待。当前回放为已有VPU输出，不是在线VPU或NPU编码并发；固定单slice索引也非通用AU解析。下一[F0门检](tools/pose-v1/F0-INTEGRATION-PREP-20261007.md)先真实Engine结果→渲染→有限编码，再owned AU/有界工作者/RTSP。HDMI时序配套仍缺，整机5Hz与长期未验收。会话关闭，新恢复检查点已保存，旧失败/暂停按历史保留。

## 2026-10-07：恢复视频任务，MMAP描述兼容修正与真实骨架完整编码通过

### 工程内容总结

r2取得VPU MMU异常地址、完整映射/入队/归还/Host复制证据；r3/r4单平面色彩拒绝保留，不放宽规格。r5保留QUERYBUF的opaque MMAP cookie用于QBUF，与厂商客户端约定对应，原格式/容量/复制/controls/所有权保持。新程序01965fa2…23d3无SDK依赖，协商与两次独立上下文各54帧编码均exit0/stderr空/dmesg同/BOOT及SDK保持，无复位或固件替换。
两次H264179648字节逐位一致，MP4已回传；主机54帧ID/27来源/756关节可见性通过，姿态不同。仅预生成离散窗口，10fps文件节奏不作实时5Hz或连续动作录像。完整[报告与动态视频](tools/pose-v1/VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md)、[核验](tools/pose-v1/evidence/video-descriptor-20261007-r5/completion-review.json)。

### 对后续开发的参考

保留r1/r2失败、r3/r4分配前拒绝与源码差异；当前有限编码缺陷已实测修正，不推断驱动页表内部根因。实际首参数集31字节、56 capture chunks对应54图像，RTSP须实际NAL/PTS和拥有字节的AU，不套固定24/8参数集或保存已归还缓冲区指针。下一为动态视频人工审查及独立RTSP准备；HDMI当前BOOT时序/scanout/停止协议仍缺证，目标1080p60未写入。没有并发推理、RTSP、整机性能/长期验收；会话已关闭。[恢复入口](tools/pose-v1/RESUME-VIDEO-20261007.md)指向新检查点，旧暂停为历史。

## 2026-10-07：真实骨架视频首批故障保存与用户暂停

### 工程内容总结

用户批准下一视频计划后，代理新增SDK无关有限编码API/独立CLI、54帧准备/构建/运行/主机审查工具，原30帧、推理与渲染源码保持。新GCC9.4 AArch64程序`109e24bd32517f49f86a9f4f131ad2a3e1f070da48dd07c88db901429eef7e8c`，27份ARM真实NV12/元数据与原回传逐项哈希通过，54帧输入74649600字节，骨架最大Y539.12不触及底部Y600诊断区。
实际协商exit0/stderr空/dmesg同；真实编码一次退出1，提交9/归还3、4capture chunk、部分29879字节可解码ID0/1/2。内核明确H264ENC MMU ABORT，根因与故障地址未知，不能归因单个帧或宣布动态视频通过。BOOT/SDK/三库与失败后FPGAoperating保持，无OOM、重试、复位或修改固件。全部失败、固件身份与部分图像已回传独立复核。
HDMI授权已恢复，完成只读配套核查及主机1080p RGB565离线色条。BOOT/DTB与Lite发布包对应，但时钟/时序映射/scanout归属和停止协议仍未建立，无fbdev/DRM/EDID。没有HDMI写入、实屏或RTSP。详见[首批报告](tools/pose-v1/VIDEO-SEQUENCE-RESULTS-20261007.md)、[失败复核](tools/pose-v1/evidence/video-sequence-20261007-r1/failure-review.json)。

### 对后续开发的参考

用户随后明确暂停并等待唤醒。所有测试程序已退出、SSH/SFTP关闭；补查download.bit的连接在认证前取消，未执行该查询。新[暂停检查点](tools/pose-v1/evidence/video-sequence-20261007-r1/next-checkpoint.json)与[恢复说明](tools/pose-v1/RESUME-VIDEO-20261007.md)已保存；暂停期间不连接、构建或新板测。
恢复先核对冻结来源/包/失败记录，优先准备完整QUERYBUF/QBUF/DQBUF映射/长度/offset/flags/PTS与所有权取证，明确固件MMU异常边界再新修订验证；不盲重跑旧包或修改profile/cache/BOOT。HDMI授权保持，仍按配套证据进入写操作。当前未增加功能验收份额，原合成编码成功不推广为真实视频稳定。

## 2026-10-07：用户完成视频审查，下一视频阶段计划与HDMI恢复标记

### 工程内容总结

用户确认已审查独立H264样片，并允许HDMI测试，撤销上一轮暂停。代理核对现有完成证据及厂商参考：HDMI默认1920×1080类只申请udma帧缓存并提交参考scanout地址，没有时序/像素时钟配置；参考SDK3.36.0与当前3.39.0不能据版本标签直接认定寄存器适用。当前未改硬件或执行新板测。
已形成[NEXT-VIDEO-PLAN-20261007.md](tools/pose-v1/NEXT-VIDEO-PLAN-20261007.md)，首批真实27预生成骨架→54帧动态文件/主机审查，以及当前BOOT的HDMIclock/scanout/换帧配套核对；随后独立1080p60实屏、RTSP和真实推理合并。原独立编码完成证据/暂停检查点保留，新恢复标记单独保存。

### 对后续开发的参考

用户允许HDMI测试不代替时序、内存归属和停止scanout协议证据；配套不明时继续编码分支而不猜写参考地址。真实预生成离散骨架帧用于证明姿态变化，不冒充连续动作录像或整机有效5Hz。编码时间戳/VUI、实屏观察和新链路性能仍待阶段验收。

## 2026-10-07：独立VPU H.264编码、回传与主机逐帧审查完成；HDMI暂停

### 工程内容总结

用户接入DELL E2421HN后报告不支持输入时序，明确后续HDMI目标为1920×1080@60Hz并暂停HDMI测试。已更新ADR目标，未改板端时序/BOOT/位流。新增SDK无关有限V4L2编码器及构建/运行/审查脚本，原推理、SDK、CPU渲染保持。
MVX实际720p NV12两plane、stride1280、Y921600/UV460800及H264单plane通过，显式色彩/10fps/2Mbps/Baseline读回一致。30帧独立合成背景＋逐帧ID/移动条成功编码，正常STOP/LAST与输入归还；H26436717字节、MP437649字节已回传主机，完整SHA256一致。
主机已有OpenCV两端各解码30帧、ID0..29/移动条/不同画面全部正确；原始H264与MP4解码像素逐位相同，MP4为720p10fps/3秒。六帧图片已目视检查，无新依赖。GCC9.4新r4程序`8f713fc8d6c76a03053544634591448f1068ef0a392261023bf73d5b1538e8ce`，协商与编码exit0/stderr空/dmesg保持，BOOT/SDK身份一致。
保留r1 CRLF清单预检、r2编码2×2顺序问题、r3默认色彩协商及裸流元数据断言历史。细节与证据：[VPU结果](tools/pose-v1/VPU-RESULTS-20261007.md)、[样片](tools/pose-v1/evidence/vpu-20261007-r1/encode-r4/results/review.mp4)、[完成复核](tools/pose-v1/evidence/vpu-20261007-r1/completion-review.json)。

### 对后续开发的参考

本次独立有限文件编码通过；没有NPU并发、HDMI/RTSP、实时或长期验收。原始码流缺少容器PTS和ffprobe显式色彩标记，MP4仅按10fps重建离线时间轴；RTSP应使用capture时间戳，补色彩信号依据，不沿用固定SPS/PPS切片或裸流默认速率。后续有界编码接口→真实预生成画面→RTSP→与推理合并，HDMI继续暂停。全部会话已关闭，恢复读新[检查点](tools/pose-v1/evidence/vpu-20261007-r1/next-checkpoint.json)。

## 2026-10-07：E1-C CPU骨架渲染与V0视频查询完成

### 工程内容总结

用户确认进度后要求继续下一阶段，并说明HDMI屏幕尚未连接。代理新增1280×720固定正交渲染、RGB565LE/NV12/NV21转换、独立检查器及本帧结果返回后的绘图接入。
源码确认24版BONES与limb_loss共14条连接，原可视化明确显示层C2翻转；当前只沿用索引与显示符号，保留原始坐标，不导入GT/滤波/匹配/阈值或米/毫米标定。合成/真实图片已目视检查，画面显示帧号、分数、槽位和状态。
Native四画面/8拒绝及真实27帧独立投影/格式通过；新467包/23来源三ARM程序构建身份通过。ARM纯CPU27画面及三格式全部与Native逐字节一致、NumPy核验一致，真实关节零裁剪；179回传，无Device::Open。
新Host107/12注册/22输出59600FP32和Host正负内容通过，52回传；三帧2Hz网络新推理＋绘图通过，70回传，完整输入/输出逐位此前板端，选中42坐标与帧号6/7/8对应。三阶段exit0/stderr空/dmesg前后相同，原引擎/数学/SDK/模型/RAW/BOOT/帧协议保持。
ARM绘图均值11.93939ms/P95 12.13419ms，同时生成三种诊断格式均值88.84998ms/P95 89.60106ms；不计磁盘，不作整机5Hz或长期验收。
只读MVX查询发现/dev/video0仅枚举两端MPLANE，NV12/NV21/H264及720p范围存在；参考单平面CAPTURE不可直接套。DT为Linlon-v5，/proc/fb空，未确认HDMI像素时钟/扫描配套；未S_FMT/REQBUFS/STREAMON/编码、未写候选寄存器。
结果：[RENDER-RESULTS-20261007.md](tools/pose-v1/RENDER-RESULTS-20261007.md)、[视频配套表](tools/pose-v1/V0-VIDEO-PAIRING-20261007.md)、[完整核验](tools/pose-v1/evidence/render-20261007-r1/completion-review.json)。预览是ARM RGB无损导出，不由电脑重推理。验证全部结束，会话关闭，无新依赖或后台服务。

### 对后续开发的参考

E1-C CPU帧缓存与真实推理接入通过，V0为部分接口事实，不等于硬件输出通过；解剖名称/物理轴仍未标定。下一步准备有限VPU720p H264合成编码、按实际返回planes/stride/色彩约定拷贝，再文件解码/RTSP；双路输出按已批准有界工作者方案测资源争用，不把全部三格式诊断开销直接作生产预算。
HDMI须确认当前BOOT720p时序/像素时钟/换帧映射并连接显示器；当前不猜测寄存器、套相机MMU初始化或更换BOOT。原始画面/失败及所有旧证据保留，已通过阶段不重跑，下一恢复点已更新。

## 2026-10-07：E1-A生产接口与E1-B网络回放实板验证完成

### 工程内容总结

用户批准全流程计划后，代理实施首批新隔离application核心、TCP接收与验证程序。生产入口返回完整分数/姿态，不依赖冻结Tokens；验证入口保留逐位检查，CPU数学、SDK显式复制/注册、Gather/NPU分工及reset(1)/最终745协议保持。
TCP按32＋86400字节组包，最新未处理完整窗口槽位1，已弹出窗口按值持有；拒绝非法/中断/非有限及连接内重复倒退帧号，重连清未处理旧窗口。最小日志路径采样4帧、计时容量8192，CLI有界最多1000帧，尚非长期守护服务。
Native与ARM纯协议自检通过（7非法记录/原始位模式/槽位/碎片/中断/重复/空闲）；BOOT9与SDK身份保持。411包/19构建来源，应用程序402cac43ca9de6bccb3ddf41ea7069d351f6d2e8e4500f33c41940d0869cc50c。
Host107/12注册/22输出59600FP32通过；生产/验证交替三帧＋重复共8次，以及3/27次真实网络前向通过，38成功前向全部输入/全输出逐位此前板端一致。四阶段exit0/stderr空/dmesg相同，52/68/55/128完整回传。
27帧网络在2Hz原始发送下无丢弃/拒绝，到达至结果均值191.95180ms/P95 193.76084ms；不作为5Hz吞吐或整机验收。网络路径不读冻结参考，不由PC预处理或推理。
首次r1函数名编译失败保留并新r2修正；首次27阶段因20秒就绪检查/120秒整体预算和人工诊断延误退出124，七完整结果仍逐位一致。只在外部新控制脚本/新目录增加300秒总预算及90秒就绪检查，READY后立即发送，一次修正验证通过；原包/程序及失败证据不改。
完整报告：[APPLICATION-RESULTS-20261007.md](tools/pose-v1/APPLICATION-RESULTS-20261007.md)、[核验](tools/pose-v1/evidence/application-20261007-r2/completion-review.json)。SSH/SFTP已关闭，无后台验证任务，未初始化视频或安装依赖。

### 对后续开发的参考

计算核心已接到真实TCP回放链路，下一阶段E1-C需要确认14关节连线/轴向并渲染，V0核对当前位流720p、帧缓存和VPU输入配套；独立视频测试后才合并双路。
不要把低速无丢帧测试扩大为NPU过载/重连/长期运行或5Hz通过。生产API配置必须沿用最小日志和有界采样，未来长期服务还需统计/结果保存策略和生命周期；原始证据与中间失败保留。部署耗时单独预算，监听READY后立即发送，不凭纯前向耗时计算进程总时限。

## 2026-10-07：首版异构方案固化与全流程接入规划

### 工程内容总结

用户明确选择当前已验证异构方案作为首版基线，先完成整个回放系统闭环，再研究真实指针映射/零拷贝、图与自定义算子优化。
已新增[ADR_01](ADR/ADR_01.md)，集中记录ARM注册、受限布局、跨域内存、融合追溯、帧计数/最终同步、生产接口及视频配套难点，列出后续解法的前提和验收边界。
沿用lazy-r4显式SDK复制及原算法/校验/帧协议；等待约164.46ms不是已证实DMA耗时，可见CPU桥复制约0.47ms，不能据此预设零拷贝能消除主要等待。
新增[全流程计划](tools/pose-v1/FULL-FLOW-PLAN-20261007.md)：生产接口、TCP完整窗口及有界队列、标签核对/渲染、视频配套、独立HDMI与编码RTSP、双路和30分钟门检。同步项目总览、待办及资料索引。

本轮仅整理本机证据与文档，没有新源码/构建/板测、SSH或视频初始化；现有65%–70%管理粗估保持，方案归档不算功能完成。

### 对后续开发的参考

下一实施批次建议E1-A生产接口与E1-B TCP回放：独立验证包装器保留固定参考比较，生产入口仍进行有限性/布局/身份/同步检查；单Engine串行、有界最新完整窗口、输出帧号可追溯。
闭环预算应按关键路径/工作者吞吐和争用测量，不能将平均9.4ms余量当最坏情况保证，或将10fps重复编码当10Hz骨架更新。关节连接/轴向、当前位流720p时钟和VPU输入配套须明确再设备门检。
原始证据/失败和已验收旧包保留，不重跑阶段或复用旧门禁作新验收；下一具体实施范围尚未执行。

## 2026-10-07：用户确认现有部署数值阶段验收，批准profiling-off单时钟性能定位

### 工程内容总结

用户明确接受现有27样本数据精度阶段，认为微小运算精度变化可导致候选颠倒；本次按用户验收决定记录通过，原误差与离群均保留。
PC/板端模型输入已逐位一致，不能把差异改写为已证实的传输损坏；跨端原query身份未证明，排序交换仍为证据支持的推断。
未新增数值阈值、GT/MPJPE或物理标定，也不将27样本结论推广至未知数据/模型。
证据：[user-numerical-acceptance.json](tools/pose-v1/evidence/perf-20261007-r3/user-numerical-acceptance.json)。

用户同时批准关闭SDK profiling，优先以单一时钟拆分forward并寻找优化方案。已新增隔离timed_runtime_core/timed_mixed_bridge/timed_runtime_check及forward_clock，r2/r6原源码和CPU内核保持；r3及独立错误消息优化lazy-r4已完成构建/Host107/输出回归/计量。
计量采用同一个steady_clock和帧内ns基准，批量保存后端调用与桥等待/复制/CPU计算、边界观察等区间；ZG后端跨度含SDK工作，不能视为纯NPU核时间。
profiling-off可能异步返回，因此只把最终输出就绪/745作为完成证明，中间返回状态如实保存，不靠计量接口制造额外同步。


本轮实测：profiling-off单时钟r3仍平均212.93086ms/4.69636Hz。内部CPU桥等待164.4799ms、CPU forward29.5905ms、复制0.4731ms；ZG调用跨度0.8466ms不代表纯硬件耗时。
源码发现成功的字面量错误消息也被构造为std::string；在新副本新增两个const char*重载共4行，不删除检查、不改算法/同步/缓存。原源码及动态消息重载保持。
lazy-r4再次通过107例（含拒绝）、四原帧回归及3预热＋30计量，全部37次输出与r6逐位一致；三个阶段exit0/stderr空/dmesg保持。
平均190.60146ms、中位190.60452ms、P95 190.75409ms、最大190.80669ms，处理吞吐5.24655Hz；对r3减少22.32941ms，CPU forward降至13.6379ms、原始/输入检查降至0.1020/0.1415ms，等待基本不变164.4569ms。
限定30次处理核心基线达到5Hz，距200ms预算平均约9.4ms；不含网络/绘图/编码，整机5Hz、10Hz与30分钟闭环仍未通过。
程序4f7fe3597bb2aaaa69884a429062ce0c3977b63a30c328b8ce6c9f9e41ab84ad，352包/16构建来源，模型/RAW/SDK/BOOT、r2/r3/r6保持。
审查工具遗漏hashlib的NameError通过独立review_perf_stage.py仅补标准库绑定修正，包/数据/规则不改写、不重跑板测；原失败与修正记录保留。
结果：[P2-RESULTS-20261007.md](tools/pose-v1/P2-RESULTS-20261007.md)、[完整核验](tools/pose-v1/evidence/perf-20261007-lazy-r4/completion-review.json)、[命令](tools/pose-v1/P2-SINGLE-CLOCK-COMMANDS-20261007.md)。SSH/SFTP已关闭，无后台任务。

### 对后续开发的参考

区分用户基于现有工程证据的数值验收决定与尚未证实的误差根因；历史自动检查器numerical_accepted=false不改写，项目层验收通过单独关联用户决定。
profiling关闭与计量插桩同时变化，和旧基线的耗时差不是严格单因素因果试验。先证明全部输出回归、再分析内部开销，据实测提出最小优化，不自动改模型、同步、缓存、并行或视频。


## 2026-10-07：恢复任务并完成E0/N1/P1工程验证及H0资料整理

### 工程内容总结

用户确认Lite开机并明确要求继续，代理从20261006检查点恢复，完成源码/参考复核、P1前置r6门禁、新r2构建与传输，以及Lite逐阶段执行。
FPAI GCC9.4.0/CMake3.24.2、ARM Icraft/CustomOp3.39.0、Lite25122301/icore24160628；9个启动文件、SDK头文件/Host/ZG/XRT身份与基线一致。
原模型/RAW/SDK/BOOT、CPU内核/桥、预处理、r6源码程序及r1旧包构建参考保留，SDK profiling未关闭。
新程序SHA256 `8970f692b8636e420ae972277fb2a45b79b844895e0664fd99d8352e4cf00192`；包manifest `c99e3b6c07dd1111bcbdcf199e8350417d5252f232d60decb1de7df896e57fab`，351项LF清单。

Host107、E0、N1、P1四阶段程序退出0、stderr空、完整dmesg前后相同；分别52/124/604/113回传核验。
Host107/12注册/22输出59,600 FP32通过，Gather保持。新可复用核心E0四次308/309/310/308完整输出与r6逐位一致，68捕获/实际CPU52,000值独立一致。
N1九组27＋首帧重复共28次，27份完整输出各不相同、首帧所有捕获和最终输出一致，476捕获/实际CPU364,000值NumPy逐位一致。
E0/N1/P1共65次forward均每帧0→745、1173原HardOp七ZG组完整追溯，六计算Host执行。Gather内容和提供输出writeback没有扩大验收。

既有ORT27参考完成独立86项/环境模块/输入/输出有限/重复与旧308复核，证明r1/r2模型输入不变后复用，不重跑或修改旧参考身份。
27份同槽分数最大差0.06548452、同槽坐标2.77696973、各端最高分坐标2.67561984模型单位，数值容限未验收。
离群S52_18_317的固定前两名交叉比较差约0.017/0.024，相同排名差约2.65–2.68，板端TopK437索引[1,0]；支持排名交换推断，缺ORT query身份证明，不匹配重排或剔除原误差。
其余26帧最高分坐标最大差不超过本次观测0.03171778，不把该数作为阈值，不作物理标定/GT/MPJPE。

P1三预热与r6完整输出核对后才30次计量，全部33次输出与r6一致。process_window中位214.72506ms/P95 215.49764ms/最大216.61380ms，平均214.85948ms、吞吐4.65420Hz；未达到5Hz且不含网络/绘图/编码。
forward平均201.36566ms占93.72%，另约5.41603ms未分段；CPU近单核等效满负荷不证明NPU闲置。RSS87,316–88,808KiB，available前后均741MiB/Swap0；不是长期稳定性或30分钟闭环验收。
H0原始源码/配套资料归档完成，720p时钟/当前位流映射、关节连接冲突及VPU/RTSP输入/缓冲区仍待确认；未操作视频硬件。

结果：[RUNTIME-RESULTS-20261007.md](tools/pose-v1/RUNTIME-RESULTS-20261007.md)、[完整核验](tools/pose-v1/evidence/runtime-20261007-r2/completion-review.json)、[复现命令](tools/pose-v1/RUNTIME-COMMANDS-20261007.md)。
下一轮[N2候选身份＋P2前向分段](tools/pose-v1/NEXT-GATE-20261007.md)为未批准/未执行候选；E1应用/视频、profiling变化、新依赖和容限另议。SSH/SFTP已关闭，没有后台测试或自动重跑。

### 对后续开发的参考

可复用已验证单Engine/单Session、异常永久停止及安全帧清理协议，固定745仅适用于已核对融合/模型/SDK。
当前核心API带固定reference Tokens门禁，是固定回放验证基础，未知实时窗口的生产接口仍需单独接入。
工程门检完成、误差统计完成、数值容限通过、5Hz通过、视频/长期闭环通过需分开记录；本轮完成执行计划不代表作品完成。
下一步先解释候选排名与forward瓶颈，再据实测讨论数值容限和正式应用/视频顺序；不能通过丢同步检查、读旧输出或关闭profiling而未经批准宣布达标。


## 2026-10-06：首版混合推理工程验收、难点复盘与下一阶段准备

### 工程内容总结

本次已完成**全项目进度整理与恢复标记**：[PROJECT-PROGRESS.md](PROJECT-PROGRESS.md)集中展示已验收、已实现待验证及未实施内容，按首版工作包作约50%–60%的工程估算（规划权重58/100，不是统计通过率或工期）。当前阶段为“小样本板端混合推理已跑通→数值/性能验证与正式应用集成”。[恢复入口](tools/pose-v1/RESUME-20261006.md)、[待办](ToDoLists.md)及机器可读状态已补齐；旧失败、构建、模型和参考未移动或覆盖。

P1初版缺少“预热三帧对照r6后才能进入计量”的前置门禁，恢复时先在新修订中补齐，再按E0→N1→P1执行；27份ORT独立核验也仍待完成。HDMI配套、骨架定义冲突、数值容限和整机闭环单独保持未验收。暂停没有解除，本轮未连接Lite、构建或执行模型。


**本轮E0/N1/P1实施暂停（2026-10-06，用户明确要求）：** 用户批准代理执行NEXT-PHASE-PLAN，随后确认Lite已关机、本人不在现场，要求先中断，唤醒后再继续。已新增隔离runtime_core运行核心、runtime_check、CMake、分阶段runner和离线审查工具，原r6检查器、CPU计算桥/内核及预处理源码保留。FPAI GCC9.4.0/CMake3.24.2交叉编译成功，15份构建来源及ARM SDK头文件/Host和ZG库身份通过；新程序SHA256 `2738b5150db4d63a949470984ec72cec56abea7b044e6f2236ded2ad94362242`，仅沿用r6版本JSON排版警告。构建证据：[build.acceptance.json](tools/pose-v1/evidence/runtime-20261006-r1/build.acceptance.json)。源码和审查工具仍需交付前完整复核；**尚未运行Host107或新核心板端回归，不能称为E0通过。**

既有Conda Python3.10.21/NumPy2.2.5/CPU ORT1.23.2已生成九组27固定输入及首帧重复参考；固定ONNX哈希、CPUExecutionProvider、顺序执行、线程1/1及ORT_ENABLE_ALL保持。27份完整输出116,100个有限FP32，首帧重复逐位一致，86项清单自核验完成；独立复核仍待完成。[参考summary](.local/pose-v1-runtime/onnx-27-20261006-r1/summary.json)。本轮没有安装新依赖、板端传输、Device::Open或推理；SSH超时及本机以太网Disconnected与用户关机确认一致，不归因于推理代码。N1板端28次、P1低日志3预热＋30计量及H0资料归档未完成。恢复入口：[暂停检查点](tools/pose-v1/evidence/runtime-20261006-r1/pause-checkpoint.json)。


本次整理以此前已验收记录为依据，不重复执行或另记同一成果。历史失败、批准修正及阶段快照保留；
下文“ORT未批准/缺失、CPU未编译/待回传、mixed待讨论”等均按对应日期理解，当前以本节为准。
最新工程结论：r6跨帧状态修正已在Lite完成三样本及同Session首帧重复验收；旧r3/r4/r5停止状态保留为历史，数值容限和持续性能仍待验收。

| 已完成工作 | 验证范围与证据 | 适用限制 |
| --- | --- | --- |
| SD启动、根文件系统扩容、SSH通信 | 用户现场确认启动/登录及扩容；[扩容截图](tools/sd-image-validation/20261003-expansion-success.png)、[环境记录](tools/development-environment/20261003-progress.json)，后续SSH只读审计已执行 | 不包含长期稳定、全容量读写或AI验证 |
| FPAI交叉编译与Lite加载 | GCC9.4.0/CMake3.24.2、ARM Icraft/CustomOp3.39.0；[原检查器构建核验](tools/pose-v1/evidence/cross-build-review-20261005.json)，后续CPU r2已实板运行 | 编译/加载不证明NPU计算 |
| 原生/MCP流水灯与简单IP交接 | Procise2025.1.1 temp/SVN32494，Vivado2019.1；本文原验收条目、[MCP流水灯结果](tools/mcp-validation/led1324/RESULTS.md)、[xlconcat IP交接](tools/mcp-validation/ip-reuse/RESULTS.md) | 独立PL与IP方法验证，不表示PS/DDR/AI系统工程已完成 |
| 启动基线与运行身份 | Lite25122301 BOOT哈希、FSBL加载及0x25122301回读；后续SDK Open/version通过，见[300份结果](tools/pose-v1/RESULTS-300.md)和历史probe记录 | 不将uEnv后续文件错误改记为download.bit成功，也不将Open/version当NPU通过 |
| 300份真实CSI预处理 | Windows/Linux/Lite逐位一致，幅度/相位差0、四类非法记录拒绝；[300份汇总](tools/pose-v1/evidence/replay-300-summary.json) | 人工±π周期误差2.333111/2.693437rad仍失败，仅经用户批准改为非阻断诊断 |
| CPU注册与最小适配 | 107例、12注册、22输出/59,600 FP32逐位一致，Gather保持；[最终结果](tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md) | 独立CPU范围为固定FP32/全有效分布/Host CPTR；NPU交接验收见后续混合行 |
| PS/NPU混合工程与跨帧状态修正 | 1173原HardOp七组追溯/六计算Host，三帧输出不同、重复首帧全部内容逐位一致；[r6实板结果](tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md) | 当前三份固定CSI工程验收；数值容限/连续性能/HDMI/RTSP仍待，提供输出buffer的writeback未触发 |

用户已批准本轮调整：**工程与数值验收分阶段，使用ONNX直接对照板端，不等待Icraft全CPU Matmul参考**。
CPU Matmul缺口保持诊断状态，正式Matmul的NPU分配不改。ADR、资料索引及阶段状态已同步。

已实际建立新Conda `.local/pose-v1-onnx-conda`，固定Python3.10.21/NumPy2.2.5/CPU ORT1.23.2。
使用缓存创建Conda、官方wheel安装ORT，八个wheel及实际依赖哈希锁定，Conda explicit/list/history、安装报告、
pip freeze/check和模块来源检查已保存。初次沙箱Conda因CUDA虚拟包IPC的WinError5失败；同一命令自动审批后成功，
不覆盖失败证据、不改变依赖配方或既有环境。源码构建和板端依赖安装未发生。

固定epoch442 ONNX哈希、CPUExecutionProvider、顺序执行、intra/inter线程数均为1及ORT_ENABLE_ALL，
308/309/310同一输入生成全部100候选的分数与14关节坐标，共12,900个有限FP32输出。
首样本重复逐位一致，不同输入响应存在；参考12项哈希独立复核。前向约221.808/221.606/212.305ms，
仅为Windows CPU参考耗时，不计板端性能。详见[ONNX参考结果](tools/pose-v1/ONNX-REFERENCE-RESULTS-20261006.md)
及[环境/产物身份](tools/pose-v1/evidence/onnx-reference-environment-20261006.json)。

<details>
<summary>混合验证交付及r1至r5历史阶段记录（保留失败与审批过程，不作为当前执行入口）</summary>

新增独立 `pose_mixed_check`源码、CMake、构建/分阶段runner/回传及数值核验工具和新测试包
`.local/pose-v1-mixed-validation/package-20261006-final`。三类Host注册调用已验收计算接口，SDK搬运至Host暂存，
真实RAW参数检查、107例回归、两16KiB缓冲区往返、Session绑定、单/三样本回调与全部输出记录已编写。
三样本阶段同一Session第四次重复308，另存重复输出和回调编号；纯PS预处理耗时与证据读写耗时分开。
新目录/LF清单、明确硬件flag、外部timeout和逐阶段验收文件门禁已交付。
15份SDK头文件与原ARM包比对通过；原推理源码/CMake、三CPU文件、原模型及固定输入身份保持。
Python AST、嵌入板端Python3.8语法、PowerShell语法、shell换行与包清单静态核验通过。
交付记录：[mixed-source-delivery-20261006.json](tools/pose-v1/evidence/mixed-source-delivery-20261006.json)。

**源码交付时新C++未交叉编译；随后用户r1构建及代理核验已完成，见以下补充。新107例桥回归/SDK内存/Session/mixed仍未在Lite执行，尚无板端输出误差报告。**
候选交付是开发成果，不能当正式推理通过。FPAI编译、传输、Lite运行仍由用户逐阶段执行；代理主动读日志和产物。
入口[用户命令](tools/pose-v1/MIXED-VALIDATION-COMMANDS.md)，范围[混合验证说明](tools/pose-v1/MIXED-VALIDATION.md)。

用户mixed-20261006-r1构建反馈及复核：GCC9.4.0/CMake3.24.2、两包ARM3.39.0，配置/编译/链接完成。
290项包、10份源码/副本、15头文件及Host/ZG库匹配；AArch64 PIE SHA256
`7cf761f1dd7d1ca1bf8a1db1826e4d9b34574b1a8dc0ac662c987eed52722a17`。
唯一-Wmisleading-indentation位于版本JSON输出三语句同一行，条件只控制逗号，后两条无条件执行符合预期；
未发现该警告导致逻辑错误，源码/包保持，不需重编译。代理只读/文件分析核验，未执行程序或访问板端。
完整[构建警告审查](tools/pose-v1/MIXED-BUILD-REVIEW-20261006.md)及
[验收文件](tools/pose-v1/evidence/mixed-20261006-r1/build.acceptance.json)。
现在可由用户继续命令B传输，再C仅host-check；不能把构建通过记为新桥/完整mixed通过。

随后用户截图反馈：B传输已达到板端文件列出阶段，host-check runner报告exit=0；尚无新阶段完整回传，
12注册/107桥用例/实际输出及SDK/程序身份仍待独立核验，不能提前宣布新Host桥通过。
用户提前执行offline-check，在读取gates/host-check.acceptance.json时FileNotFoundError；
已核对runner顺序，该预检在程序调用前，离线程序未启动。原因是前阶段尚未回传核验/生成并传入验收文件。
证据[evidence/mixed-20261006-r1/host-offline-gate-feedback.json](tools/pose-v1/evidence/mixed-20261006-r1/host-offline-gate-feedback.json)。
已补齐失败预检目录回传及在验收后保留改名的具体命令；本轮仅截图/源码审查及命令准备，未操作板端或改变runner。

Host完整回传后的最新验收：代理文件核验及独立数值复查通过，107例=18正常/89拒绝，12注册记录匹配，
22输出/59,600 FP32全有限、逐位一致、最大差0；新SDK Host暂存桥的五节点搬运有记录，指针均CPTR。
包290/回传45哈希、15ARM头文件/Host＋ZG库/两包3.39.0/程序身份匹配，ldd完整，退出0/stderr空。
完整dmesg前后相同，available686→687MiB/Swap0；mode=host-check、未Device::Open/完整Session/RAW或NPU执行。
[Host桥结果](tools/pose-v1/MIXED-HOST-RESULTS-20261006.md)、
[独立核验](tools/pose-v1/evidence/mixed-20261006-r1/host-independent-review.json)、
[host-check验收文件](tools/pose-v1/evidence/mixed-20261006-r1/host-check.acceptance.json)已生成。
此前待回传为历史状态；现在用户传入验收文件，失败offline预检目录先保留回传审阅，再按补充命令进入离线阶段。

离线失败预检回传核验补充：用户报告Host验收文件已传板，并回传原失败目录；目录仅package-check.log、
timeout-path/version三文件，290项校验全部OK、GNU timeout8.30，无results/exit.txt/SDK审计/程序日志。
与已核对runner及此前缺gate异常位置一致，确认离线程序未启动，失败证据已完整保留。
[预检审查](tools/pose-v1/evidence/mixed-20261006-r1/offline-preflight-review.json)完成；
现在用户按固定工作目录保留改名后执行一次30秒offline-check并完整回传，代理未操作板端或代执行。
本次不生成offline验收文件，真实RAW/PS输入检查仍待程序实际运行结果。

正式offline-check完整回传后的验收更新：用户执行成功、退出0/stdout及stderr空/阶段完整，代理独立核验32回传/290包及SDK/程序身份通过。
原RAW的TopK188/437两个K=100，ScatterND582/649两份50,400字节有限整数索引转储与完整100×14×3坐标网格一致，
四参数已加载、无fixture替换。308/309/310共32,400有限FP32输入与固定及ONNX参考逐位一致，12注册记录符合预期、Gather保持。
完整dmesg前后相同，available686→687MiB、Swap0；纯PS观测15.35236/5.60302/5.58911ms不作连续性能结论。
mode=offline-check/device_init_allowed=false，未初始化设备/创建完整Session/执行前向。
[离线结果](tools/pose-v1/MIXED-OFFLINE-RESULTS-20261006.md)、[独立复核](tools/pose-v1/evidence/mixed-20261006-r1/offline-independent-review.json)、
[offline验收文件](tools/pose-v1/evidence/mixed-20261006-r1/offline-check.acceptance.json)已生成。
下一步用户传入验收文件，并在BOOT/JTAG保持、设备无竞争访问的前提下，仅执行30秒SDK两16KiB内存往返并回传。
本阶段不代表1173HardOp/六Host实际绑定、NPU内存同步、完整mixed或精度通过；先前offline未执行为历史状态。

SDK内存阶段最新验收：用户一次受限memory-check退出0、完整回传，代理核对28回传/290包及15头文件/两库/版本/程序身份通过。
SDK Open成功，device25122301/icore24160628保持；两个16KiB缓冲区为ADDR、AXIZG330AIPLDDRMemRegionNode、chunk/offset正确。
固定程序核对区域归属及不重叠，三模式/六份输出共24,576有限FP32逐位一致、最大差0，-0/+0符号位保持。
stderr空、阶段完整、完整dmesg前后相同、available前后687MiB/Swap0；未创建完整Session或执行模型前向。
[内存结果](tools/pose-v1/MIXED-MEMORY-RESULTS-20261006.md)、[独立复核](tools/pose-v1/evidence/mixed-20261006-r1/memory-independent-review.json)、
[memory验收文件](tools/pose-v1/evidence/mixed-20261006-r1/memory-check.acceptance.json)已生成。
本次CPU↔设备SDK搬运不证明NPU生产者/CPU消费者同步或推理数值；下一步用户仅300秒apply-check（创建/apply/绑定，无forward），回传再核验。
代理未接入板端/重跑/复位/改配置；此前memory待执行是历史状态。

apply失败/SSH退出审查补充：用户截图在登录shell单独set -eu，test ! -e遇到已存在run-apply-check触发errexit导致SSH关闭。
代理按特殊问题权限SSH只读列目录、SCP取回既有完整结果，35项回传/290包、程序/SDK/上一memory身份匹配。
实际apply退出1，阶段已到session_applied，随后因首个原HardOp8622未在预期绑定表中找到而检查器主动停止；
绑定文件仅Input0一条，无forward_started/模型输出/桥搬运，dmesg前后相同。Session创建/apply返回不等于完整部署验收。
[失败审查](tools/pose-v1/MIXED-APPLY-FAILURE-20261006.md)、[证据](tools/pose-v1/evidence/mixed-20261006-r1/apply-failure-review.json)已保存。
SDK明确提供autoMerge、HardOpInfo.merge_from和运行视图，但当前没有完整实际映射，融合仅为候选原因。
已准备[仅加绑定快照的候选](tools/pose-v1/MIXED-BINDING-SNAPSHOT-PLAN.md)，未应用/编译/运行；
后续方案须讨论批准，不改计数/SDK选项、不重跑或删除旧目录，不进入mixed。代理没有运行检查器/初始化设备，口令未落项目文件。

### 绑定快照r2批准后应用（2026-10-06）

工程内容总结：用户明确“同意方案”，已将[审阅候选](tools/pose-v1/mixed_check.binding-snapshot.candidate.cpp)
逐字节应用到mixed_check.cpp，原r1源码备份在evidence/mixed-20261006-binding-r2/mixed_check.before-binding-snapshot.cpp。
仅新增Session创建后、apply返回后的完整绑定/运行与后端视图/ZG hardop_map及merge_from/同步索引快照，
原严格1173HardOp＋六Host门检、前向代码、数据桥、CPU内核、默认SDK优化保持；不再次调用autoMerge。
新包.local/pose-v1-mixed-validation/package-20261006-binding-r2已准备，290项哈希通过，
与r1的289项非manifest载荷逐位相同；13份源身份记录只有mixed_check.cpp改变，
原推理器/CMake、已验收CPU实现、模型/RAW/输入与r1二进制/失败证据保持。
Python AST、板端嵌入Python3.8、PowerShell语法、LF清单及SDK公共字段静态审查通过。
[应用记录](tools/pose-v1/evidence/mixed-20261006-binding-r2/source-applied.json)、
[新包静态核验](tools/pose-v1/evidence/mixed-20261006-binding-r2/package-preparation.json)，
[用户执行入口](tools/pose-v1/MIXED-BINDING-R2-COMMANDS.md)。
**新r2未交叉编译/运行Host、离线、内存或apply；不称新增快照运行通过或绑定问题已修复。**

对后续开发的参考：旧失败程序缺完整绑定表，补足前后公共元数据有助于区分SDK合并表示和真实遗漏；
merge_from是官方字段，但实际内容需新程序运行核验，不能只凭接口存在认定1173原节点全部覆盖。
保留原失败条件，取证可能仍退出1；完成日志采集不作部署验收，不直接执行mixed。
新程序身份对应新的构建/Host/离线/内存门禁，不复用旧验收文件；按已批准顺序先构建核验再逐阶段。
SSH登录shell不单独执行set -eu，新运行命令用独立sh入口，runner自身仍非0即停，旧r1不重跑/删改。

r2构建最新验收：用户完成mixed-20261006-binding-r2配置/五CPP编译/链接，代理核对290项包/10源码及副本/
15ARM头文件/Host＋ZG库/两包3.39.0/脚本/manifest身份匹配。快照源码与批准候选一致，公共字段已通过ARM编译。
程序AArch64 ELF64 PIE、518,712字节，SHA25694a03a903a4a97f229b1549dcbd1bade193d60dbb23753c1f030431fbd061248；
直接Host/ZG依赖、无RPATH/RUNPATH。完整日志只有已审阅的原142行缩进warning，无error；无需重编译。
[构建结果](tools/pose-v1/MIXED-BINDING-R2-BUILD-RESULTS.md)、
[验收文件](tools/pose-v1/evidence/mixed-20261006-binding-r2/build.acceptance.json)及build-review.json已保存。
本次只构建身份验收，未新板测/快照运行；用户下一步新目录传输后先Host107回传，不跳过门禁到apply/mixed。
前述r2未编译为应用时历史，旧r1始终保留失败状态，代理未代编译/板端接入。

r2用户运行截图补充：host-check runner报告exit=0，完整结果尚未回传，107例/注册/输出身份待独立复核。
用户随后提前执行offline-check，因gates/host-check.acceptance.json缺失退出1；核对runner，此处在SDK审计及程序调用前，离线检查器未运行。
截图及[反馈记录](tools/pose-v1/evidence/mixed-20261006-binding-r2/host-offline-gate-feedback.json)已保存。
下一步先回传run-host-check及原run-offline-check预检目录；通过Host核验后才生成新r2验收文件。
保留现有失败目录，不重跑Host/offline或硬件、不复用r1门禁；代理本轮仅本机文件分析，未接入板端。

r2完整回传验收更新：107例（18正常/89拒绝）、12注册、22份输出/59,600有限FP32逐位一致，与已验收r1输出也一致；
290包/45回传校验、15ARM头文件/两库/3.39.0及新程序94a03a90…bd061248身份匹配，退出0/stderr空。
94次Host CPTR桥事件（84输入/10输出），dmesg完整前后相同；无Device::Open、完整Session或NPU。
提前offline仅三份预检/290项全部OK，确认检查器未启动；本机失败目录原样整理到offline-preflight-missing-gate。
[Host结果](tools/pose-v1/MIXED-BINDING-R2-HOST-RESULTS.md)、host-independent-review.json、host-check.acceptance.json及offline-preflight-review.json已保存。
下一步按r2命令E传入新验收、受保护地改名保留板端预检目录后仅运行30秒离线阶段并回传；不重跑Host/跳到硬件。
后续参考：验收文件必须对应新程序/包身份，失败预检与正式程序结果分开保留；本阶段不能证明快照、融合映射或混合精度。

r2正式离线验收更新：用户执行并完整回传，32回传/290包项、15ARM头文件/两库/3.39.0及新程序身份匹配，退出0/stdout及stderr空。
真实RAW两个TopK K=100、两份50,400字节ScatterND索引与完整[100,14,3]网格逐位一致；12注册及原Gather保持。
三PS输入共32,400有限FP32与固定及ONNX参考逐位一致，观测预处理5.67611/5.51163/5.55515ms；不作性能验收。
dmesg完整前后相同，available均723MiB、Swap0；无设备初始化、完整Session或NPU计算。
[离线结果](tools/pose-v1/MIXED-BINDING-R2-OFFLINE-RESULTS.md)、offline-independent-review.json及offline-check.acceptance.json已保存。
下一步用户按r2命令F传新离线门禁，在BOOT/JTAG及设备无竞争访问前提下仅一次30秒SDK内存往返并回传。
后续参考：实际参数加载与PS输入是独立离线证据，不代替设备搬运、快照融合映射或前向精度；原失败预检仍独立保留。

r2 SDK内存往返验收更新：用户完成并回传，28回传/290包/15ARM头文件/两库/3.39.0及新程序身份匹配，退出0/stderr空。
Device25122301/icore24160628、SDK数据区域AXIZG330AIPLDDRMemRegionNode匹配；两16KiB ADDR缓冲区三组模式，
六回读共24,576有限FP32值逐位一致，包含正负零，与r1模式相同。固定程序检查区域所属设备与分配不重叠，未输出绝对地址。
完整dmesg前后相同，available723→724MiB/Swap0；未创建完整Session或前向，不证明NPU生产者同步/混合精度。
[内存结果](tools/pose-v1/MIXED-BINDING-R2-MEMORY-RESULTS.md)、memory-independent-review.json和memory-check.acceptance.json已保存。
下一步按已批准r2命令G仅一次300秒apply取证并完整回传；原门检可能仍失败，不自动重试/复位/改SDK，不进入mixed。
后续参考：设备复制模式通过与真实NPU生产者同步分开验收，公共快照实际运行及1173融合映射仍待取证。

r2 apply快照取证完成：用户一次执行完整回传45项，程序/包/SDK/设备身份通过，退出1仍为原8622直接ID门检。
Session创建/apply均返回，两阶段十份快照齐全；创建时1173原HardOp均ZG，部署后七组9185–9191实际ZG绑定，
七组merge_from恰好覆盖全部1173原节点且无遗漏/重复/额外节点；8622属于9185，六计算Host及Input/Output保持。
完整dmesg前后相同、真实RAW/PS与离线基线一致；无forward/模型输出，不生成apply验收。
新增仅本机mixed_binding_snapshot_audit.py，实际快照审计和九项异常拒绝通过，1173项原到有效组映射已保存。
428个原条目layer_count=0，仅依组成员集合证明原覆盖；不把层数当逻辑节点数或解释为NPU丢算子。
另核验器HardOp字符串与实际HardOpNode不符，生产代码尚未修正。
[取证结果](tools/pose-v1/MIXED-BINDING-R2-APPLY-RESULTS.md)、apply-independent-review.json及binding-snapshot-audit已保存。
[正式融合追溯修正方案](tools/pose-v1/MIXED-FUSION-BINDING-FIX-PLAN.md)已准备待批准；当前暂停新apply/forward，不改SDK优化或降低覆盖数。
后续参考：实际后端绑定的合并组必须通过merge_from追溯到完整原集合；映射元数据审计与正式部署/计算/精度分阶段验收。

### 正式融合追溯修正r3批准后交付（2026-10-06）

工程内容总结：用户回复“同意”批准正式融合门检方案，已保存r2源码/核验器备份并修改混合候选及核验器。
创建时验证1181原绑定、1173HardOp均ZG；apply后只处理实际绑定的七ZG组，验证同一后端实例、组ID/同步表/
固定成员及全部1173原HardOp完整唯一覆盖，八Host保持。保留十份公共快照，新增全1181原节点有效ID追溯和绑定汇总。
核验器使用真实HardOpNode类型，独立复核全部映射，并拒绝apply模式中的前向产物。
新增从r2证据生成的静态C++/JSON基线；模型/RAW/原infer及CMake、三CPU实现、预处理、桥和forward代码尾部保持。
本机真实快照＋模拟新格式记录回放通过，18类异常及额外非布尔标记拒绝；不是ARM程序输出。
新包package-20261006-fusion-r3的291项哈希、11构建文件/17源身份核验通过；r2原289项非manifest载荷保持，LF/AST/板端Python3.8语法通过。
[交付](tools/pose-v1/MIXED-FUSION-R3-DELIVERY.md)、[源码/包审查](tools/pose-v1/evidence/mixed-20261006-fusion-r3/source-and-package-review.json)、
[最终回放](tools/pose-v1/evidence/mixed-20261006-fusion-r3/offline-replay-final/review.json)已保存；代理未编译/SSH/运行设备。
用户当前仅[MIXED-FUSION-R3-COMMANDS.md A](tools/pose-v1/MIXED-FUSION-R3-COMMANDS.md)新标签交叉编译，日志核验后再逐阶段板测，不复用旧门禁。

对后续开发的参考：分开记录原节点与合并执行组，不能用七组代替1173覆盖数；同步层数与原逻辑节点数不同。
基线变化、缺失/重复成员、Host混入或错误后端应停止，默认SDK融合保持。本机回放仅验核验逻辑，不证明ARM API、NPU同步或精度。
新正式apply未执行且混合前向仍未验证，不能把本轮修正交付记为部署通过。

r3构建验收更新：用户完成GCC9.4/CMake3.24.2、ARM两包3.39.0配置/五CPP编译/链接；291包项/17来源/
11构建副本（含融合基线头）/15ARM头文件/Host＋ZG库身份匹配。程序555,800字节、AArch64 PIE，SHA256
e8d66113ad3d9a34f9f210e5f7038560bc3dbfa681b9a057d748ff39e6c696a8；直接Host/ZG依赖，无RPATH/RUNPATH。
仅原JSON输出缩进warning移至143行且已审查，无error；新SDK追溯调用可编译，实际运行仍待验收。
[构建结果](tools/pose-v1/MIXED-FUSION-R3-BUILD-RESULTS.md)、build-review.json及build.acceptance.json已保存。
用户当前按r3命令B/C创建新目录传输后仅Host107回归并完整回传，不重编译/复用旧门禁/直接离线或硬件。
代理仅本机文件核验，未编译、SSH或运行设备；此前r3未编译是交付时状态。

r3 Host回归验收更新：用户完整执行回传，107例（18正常/89拒绝）、12注册、22输出/59,600有限FP32与固定及r2已验收输出逐位一致，最大差0。
94次Host CPTR桥搬运（84输入/10输出），Gather保持；45回传/291包/15ARM头文件/两库/3.39.0及程序e8d66113…e6c696a8身份匹配。
退出0/stderr空，完整dmesg前后相同，available均723MiB/Swap0；无设备初始化、完整Session或NPU，正式融合函数未执行。
[Host结果](tools/pose-v1/MIXED-FUSION-R3-HOST-RESULTS.md)、host-independent-review.json和host-check.acceptance.json已保存。
用户下一步仅r3命令D传新验收后一次30秒真实RAW/PS离线门检并回传；不重跑旧阶段/复用旧门禁/直接硬件。
后续参考：核心候选身份变更后Host回归已通过，但Session融合追溯仍须其独立apply路径实际运行。

r3离线验收更新：用户一次执行完整回传，真实四RAW参数与r2已验收转储一致（两K=100、两份50,400字节完整ScatterND坐标网格），
三PS输入32,400有限FP32与固定/ONNX/r2参考逐位一致，12注册及原Gather保持。32回传/291包/15ARM头文件/两库/3.39.0及新程序身份匹配。
退出0/stdout及stderr空，dmesg完整前后相同，available722→723MiB/Swap0；预处理观测5.65894/5.54286/5.55557ms，不作持续性能结论。
[离线结果](tools/pose-v1/MIXED-FUSION-R3-OFFLINE-RESULTS.md)、offline-independent-review.json及offline-check.acceptance.json已保存。
无设备初始化/完整Session/NPU；用户下一步仅r3命令E传新验收，在BOOT/JTAG保持及无竞争访问前提下30秒SDK内存往返并回传，不apply/forward。
后续参考：真实输入/参数门检已在新程序身份下通过，但并不证明新融合函数的实际SDK运行或两端数值精度。

r3 SDK内存往返验收更新：用户一次执行完整回传，device25122301/icore24160628及区域身份匹配；两16KiB ADDR SDK设备缓冲区六回读/24,576有限FP32逐位一致含正负零，与r2模式一致。
28回传/291包/15ARM头文件/两库/3.39.0及程序身份匹配，退出0/stderr空，dmesg完整前后相同，available均723MiB/Swap0。
[内存结果](tools/pose-v1/MIXED-FUSION-R3-MEMORY-RESULTS.md)、memory-independent-review.json及memory-check.acceptance.json已保存。
未完整Session或模型前向，不证明NPU生产者同步；下一步仅r3命令F一次300秒正式apply门检并完整回传，核验前不mixed。
后续参考：新程序前置Host/离线/SDK复制均通过，原到融合组的实际ARM校验仍须Session路径证明；代理仅读本机证据。

r3正式apply验收更新：用户一次执行完整回传45项，退出0/stderr空、无failure；创建1181原绑定及部署后1181逻辑追溯记录齐全。
1173原HardOp通过七个实际ZG组9185–9191完整唯一覆盖、固定成员/同步基线匹配，六计算Host和Input/Output保持；8622→9185。
两组十份快照和binding-summary齐全，C++正式融合门检与本机独立核验均通过；291包/SDK/程序/设备身份及RAW/PS与基线一致。
完整dmesg前后相同，available均723MiB/Swap0；无forward阶段/桥执行/模型结果，仅Session创建、apply部署和绑定追溯通过。
[apply结果](tools/pose-v1/MIXED-FUSION-R3-APPLY-RESULTS.md)、apply-independent-review.json及apply-check.acceptance.json已保存，旧r1/r2失败保持。
下一步仅r3命令G一次180秒308单样本实际混合计算并完整回传；尚未验证NPU计算/生产者同步/完整数值或性能，不直接三样本。
后续参考：原节点与融合执行组追溯已在ARM实际通过；部署通过仍需独立实际前向、执行回调和完整候选数值证据。

r3 308单样本混合工程验收更新：用户一次执行完整回传51项，退出0/stderr空；七ZG组及六Host计算节点均实际执行，frame6/invocation0一次前向。
五适配节点八次SDK ADDR→Host CPTR搬运115,360字节，结果返回Host CPTR，SDK提供输出缓冲区writeback分支本次未触发。
全部100分数和100×14×3姿态共4300有限FP32保存，输入/真实参数/1173原融合绑定及291包/SDK/程序/设备身份通过，内核前后相同。
前向204.64506ms、输出转储2.7998ms、含证据帧耗时208.09317ms、Session初始化26795.38561ms；单次观测不作5Hz/连续性能结论。
[单样本结果](tools/pose-v1/MIXED-FUSION-R3-ONE-RESULTS.md)、mixed-one-independent-review.json及mixed-one.acceptance.json已保存。
初步ONNX差异：全分数同槽最大0.00304520、全坐标同槽最大1.32329583，各端最高分槽均0但最佳候选坐标最大差0.01611638；非逐位一致。
仅模型原始单位/部署对照，不推断候选身份、差异原因、物理误差或MPJPE，无容限验收。
下一步仅r3命令H一次300秒308/309/310和同Session重复308完整回传，检查首帧跨Session及同Session一致、不同输入响应，再汇总全误差。
后续参考：这次实际单帧PS/NPU链路已通过工程门检，仍不代表整个测试集精度、所有缓冲区分支或持续同步/性能通过。

r3三样本异常停止复核：用户一次执行回传61项，四次308/309/310/308均完成后退出1，All outputs identical for distinct CSI，未成功summary/三样本验收。
三PS输入哈希不同且与固定/ONNX一致，309/310相对308分别10431/10445元素变化，ONNX分数和姿态响应均变化；板端三帧4300输出却全部逐位相同，与308首帧及之前mixed-one相同。
每次七ZG/六计算Host回调，32桥事件；有限输出/首帧重复通过不能抵消不同输入响应失败。291包/SDK/设备/注册/融合绑定及真实参数身份通过，dmesg完整前后相同，available均689MiB/Swap0。
前向207.1123/39.10712/38.51481/38.37844ms是失败运行观测，后续39ms不作性能或5Hz结论。
[失败审查](tools/pose-v1/MIXED-FUSION-R3-THREE-FAILURE.md)、mixed-three-failure-review.json及SDK-source-review.json已保存；正式数值报告不绕过失败门禁生成。
SDK公开forward/私有tmap/ready及本机Input明文注册已只读审查，但当前无逐次实际Host输入/Input0/中间内容，不能确定缓存、同步或生命周期根因。
[输入内容诊断方案](tools/pose-v1/MIXED-INPUT-FRESHNESS-DIAGNOSTIC-PLAN.md)已准备待批准；代理未改运行源码/SDK、未构建/SSH/重跑，暂停新硬件和数值验收推进。
后续参考：回调次数和首样本重复不等于每次消费新帧，连续推理必须同时验证不同输入响应；原单样本工程记录保留其有限范围。

### 连续输入内容取证r4批准后交付（2026-10-06）

工程内容总结：用户回复“同意”，已保存r3核心/桥/脚本五份备份，新增显式Host内容捕获。
每次实际caller Tensor.write后SDK read回读、Input0 API返回内容逐位对照、桥原有SDK复制之后Host暂存及CPU结果转储，记录invocation防混淆。
Capture只允许已分配有界Host CPTR FP32，不新增设备读/寄存器访问；辅助Tensor句柄不跨forward保留，原等待/复制/就绪调用、CPU数学/Gather/融合基线/模型/RAW保持。
Host在107例后增加两模式纯Host捕获与别名模拟、错期望/未分配/FP16拒绝；真实Session Input0尚未执行。
新本机核验器的Host/单次/四次模拟正例及11类异常/提前停止检查通过；Python AST/板端Python3.8/LF/捕获名称字面量及来源检查通过。
最终package-20261006-content-r4-final已准备，291项哈希/12构建文件/20来源，原r3非manifest载荷289份保持、runner捕获参数更新。
[交付](tools/pose-v1/MIXED-CONTENT-R4-DELIVERY.md)、[最终身份](tools/pose-v1/evidence/mixed-20261006-content-r4/delivery-review.json)、
[本机模拟检查](tools/pose-v1/evidence/mixed-20261006-content-r4/offline-content-tests-final/review.json)已保存，未编译/SSH/板端运行。
用户当前仅[MIXED-CONTENT-R4-COMMANDS.md A](tools/pose-v1/MIXED-CONTENT-R4-COMMANDS.md)最终标签交叉编译，核验后按新身份逐阶段，旧r3失败不重跑。

对后续开发的参考：Caller读回、Input0返回及第一Host消费的ZG结果形成内容边界证据；如提前失败也保留实际字节和上下文。
模拟格式测试不证明SDK实际读回；诊断IO/主机分配可能改变时序，问题消失不能宣布修复，仍不得修改ready/cache/SDK或自动放宽原门禁。
正常三样本工程/数值验收仍未完成，当前源码交付不作根因或模型精度结论。

r4-final构建验收更新：用户完成GCC9.4/CMake3.24.2、ARM Icraft/CustomOp3.39.0配置/五CPP编译/链接，291包/20来源/
12构建文件副本/15ARM头文件/Host＋ZG库匹配，新Host SDK read/句柄/Chunk调用已可编译。
程序578,960字节、AArch64 PIE，SHA256ba8d53985fabdfdc12939d794825d31a0ee29bf9516567be5ba9356c515dcea7，直接Host/ZG依赖、无RPATH/RUNPATH。
仅原JSON缩进warning移至147行且已审查，无error；[构建结果](tools/pose-v1/MIXED-CONTENT-R4-BUILD-RESULTS.md)、build-review.json和build.acceptance.json已保存。
用户当前仅r4命令B/C新final目录传输后Host107＋纯Host内容路径并完整回传，核验前不离线/硬件或复用旧门禁。
代理仅读本机文件，未编译/SSH/运行程序；API编译通过不等于SDK实际内容读回、Session输入定位或r3故障修复。

r4 Host/内容路径验收更新：用户执行完整回传52项，107例（18正常/89拒绝）、12注册、22CPU输出/59,600有限FP32与固定/r3逐位一致，94桥事件均Host CPTR、原Gather保持。
附加两模式caller SDK读回及模拟Input0别名共四正例与NumPy模式逐位一致；错期望负例记录false且实际Tensor不变，未分配/FP16读取前拒绝。
五捕获共216,000字节、内容汇总/阶段齐全；SDK Host读取和日志路径已在ARM验证，但不是实际Session Input0测试。
291包/SDK/程序身份通过，退出0/stderr空，完整dmesg前后相同，available686→687MiB/Swap0，无设备初始化/Session/NPU。
[Host结果](tools/pose-v1/MIXED-CONTENT-R4-HOST-RESULTS.md)、host-independent-review.json及host-check.acceptance.json已保存。
用户当前仅r4命令D传新Host门禁后一次30秒真实RAW/PS离线检查并完整回传，核验前不硬件；r3不同输入相同输出仍未定位。
后续参考：期望不符的Host负例记录false是设计预期，不与真实混合帧失配混淆；模拟别名只能证明记录能力，不证明Session传入新帧。

r4离线验收更新：用户一次执行完整回传32项，真实四RAW参数与r3一致（两K=100、两份50,400字节完整ScatterND索引网格），三PS输入32,400有限FP32与固定/ONNX/r3逐位一致，12注册及Gather保持。
291包/15ARM头文件/两库/3.39.0及程序身份通过，退出0/stdout及stderr空、dmesg完整前后相同，available均686MiB/Swap0。
预处理观测5.66225/5.52195/5.54218ms不作持续性能结论，无设备初始化/Session/NPU，内容捕获关闭。
[离线结果](tools/pose-v1/MIXED-CONTENT-R4-OFFLINE-RESULTS.md)、offline-independent-review.json及offline-check.acceptance.json已保存。
用户当前仅r4命令E传新门禁，在BOOT/JTAG保持及无竞争访问时一次30秒SDK内存往返并完整回传，不直接apply/forward。
后续参考：PS/参数输入在新诊断身份下保持，仍不能确定实际Session传入内容或连续forward故障原因。

r4 SDK内存往返验收更新：用户一次执行完整回传28项，两16KiB ADDR SDK设备缓冲区六回读/24,576有限FP32逐位一致含正负零，与r3模式一致。
device25122301/icore24160628及SDK区域/291包/两库/15头文件/新程序身份通过，退出0/stderr空，dmesg完整前后相同、available均685MiB/Swap0。
[内存结果](tools/pose-v1/MIXED-CONTENT-R4-MEMORY-RESULTS.md)、memory-independent-review.json及memory-check.acceptance.json已保存。
未完整Session或前向、content_capture=false，不证明实际输入更新或NPU同步；用户下一步仅r4命令F一次300秒apply-only并完整回传，核验前不内容前向。
后续参考：前置SDK复制路径保持，但不同CSI同输出根因仍须逐次实际Tensor内容定位；代理仅本机分析未操作板端。

r4 apply-only验收更新：用户一次执行完整回传45项，退出0/stderr空；1181原节点及1173HardOp经七实际ZG组完整唯一追溯、固定成员/同步基线及八Host保持，十快照和汇总齐全。
291包/SDK/程序/设备及RAW/PS身份一致，dmesg完整前后相同，available685→686MiB/Swap0；无桥执行/模型结果/content目录，content_capture=false。
[apply结果](tools/pose-v1/MIXED-CONTENT-R4-APPLY-RESULTS.md)、apply-independent-review.json及apply-check.acceptance.json已保存。
用户下一步仅r4命令G一次180秒308内容前向并完整回传，读取真实caller/Input0/桥暂存和结果；当前未验证真实Session数据更新，r3故障仍未修复结论。
后续参考：新诊断身份下部署保持，后续即使提前停止也应保存实际Tensor内容，不能以缺少完整17记录强行重试补全。

r4单样本内容验收更新（2026-10-06）：用户一次完整回传69项，ARM Icraft/CustomOp3.39.0、新程序/291包/设备基线匹配，退出0/stderr空/内核前后相同。
308/frame6首次forward的实际caller及真实Input0返回各10800个FP32与固定输入逐位一致，17份Host内容253760字节全有限。
七ZG组和六计算Host执行、八ADDR→CPTR搬运115360字节，4300完整输出与r3单样本逐位一致；提供输出writeback未触发。
forward207.07742ms、含取证IO210.97278ms、初始化26507.59282ms，仅单次诊断观测，不作持续性能。
[单样本结果](tools/pose-v1/MIXED-CONTENT-R4-ONE-RESULTS.md)、内容/独立复核及mixed-one.acceptance.json已保存。
下一步用户仅r4命令H一次300秒同Session三帧及重复308内容取证，提前停止也完整回传，不重试或改变ready/cache。
后续参考：首次Input0内容已确认，尚不能判定连续输入更新；r3故障未知，诊断IO可能影响时序，不能作自动修复或数值/性能结论。

r4三样本内容异常分析完成（2026-10-06）：用户一次回传130项、四次forward结束后退出1“不同CSI全部输出相同”；68内容1015040字节全有限、291包/ARM3.39.0/程序/设备/RAW/绑定及内核保持。
每次真实caller/Input0与当前输入一致；调用1最早未响应在ZG9185→TopK188暂存边界，调用2/重复308前段变化而后段582/649及最终输出仍首帧。
重复308的前段与第一次不同；五适配节点对实际捕获输入由NumPy重算28输出/52000FP32逐位一致，原Gather未完整内容捕获。
[失败分析](tools/pose-v1/MIXED-CONTENT-R4-THREE-FAILURE.md)、内容复核及mixed-three-failure-review.json已保存，不生成三样本验收，约40ms后续耗时不作性能通过。
后续参考：不能再归因于caller未更新或这五个CPU内核数学错误，优先核对跨帧PS/NPU交接、完成状态、搬运及内存复用；根因尚未证明。
MIXED-CONTENT-R5-READINESS-PLAN.md是待批准状态/时序取证候选，未修改运行源码、SDK或ready/cache策略，停止重跑及正常数值/显示/性能。

</details>

r6跨帧同输出故障修复完成（2026-10-06）：代理按用户全权执行授权完成运行库审查、FPAI GCC9.4/CMake3.24.2构建、SFTP、Lite各阶段和独立核验。
r5计数首次0→745，次帧仍745并累加1222，ARM ZG等待使用固定本帧阈值，旧计数导致提前完成判定；caller/Input0与五CPU数学保持正确。
仅mixed_check.cpp每帧使用官方Device::reset(1)清FPGA状态、确认0，输出就绪/固定745后再下一帧；同一Session、SDK/模型/RAW/BOOT及原CPU/桥/预处理/融合保持。
r6构建、Host107/59,600值、离线、内存、apply、单和三全部通过；三帧131回传/68内容1,015,040字节/76状态及1173覆盖匹配，四次0→745。
三帧分数和姿态分别不同，重复308全部捕获及4300输出逐位一致，跨Session单帧也一致；真实CPU28输出/52,000FP32由NumPy逐位一致。
程序SHA256f826fc31441caf09ef22d94561672023737ab4c330ba22ec0159ecf7f77e144a，ARM Icraft/CustomOp3.39.0及设备25122301/icore24160628保持，所有阶段内核前后相同，available717→718MiB/Swap0。
[完整结果](tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md)、[完成核验](tools/pose-v1/evidence/mixed-20261006-frame-state-r6/completion-review.json)、新mixed-three.acceptance.json及完整ONNX12900值误差已保存，SSH/SFTP会话已关闭。
分数最大差0.00304520/0.00355411/0.01011199，同槽坐标1.32329577/2.03372848/1.34546995，各端最佳坐标0.01611638/0.01987362/0.02760744模型单位。
未宣称同槽候选身份/MPJPE/物理标定或数值容限通过；前向206.6–208.2ms及含取证IO约210–212ms不作持续5Hz/延迟通过。
后续参考：帧级执行计数和握手生命周期必须明确，固定745仅用于当前模型与融合基线；旧失败、私有字段编译错误和早期部分回传保持，正常数值比较只在新三样本门禁通过后执行。

#### 难点、处理依据与当前状态

| 难点与表现 | 已确定的原因或处理路径 | 当前状态与后续参考 |
| --- | --- | --- |
| Windows开发环境与参考路线 | VS路径含前导空格，另开的CMD不继承开发环境；回原窗口后C++可用但Windows SDK未识别。Lite全CPU又在Matmul绑定失败 | Windows SDK/CPU Matmul缺口保留；独立Conda ORT直接参考已通过，不阻断正式Matmul走NPU。见[参考结果](tools/pose-v1/ONNX-REFERENCE-RESULTS-20261006.md) |
| Windows/Linux换行及命令环境 | SHA清单CRLF将尾随\r当作文件名；拆行或变量未设置造成参数错误；登录shell的set -e遇到失败test会退出SSH | 使用LF字节清单、完整命令、显式路径和独立子shell，失败保留目录；不要用删除旧目录/跳过门禁来处理。见[CRLF诊断](tools/pose-v1/CRLF-CHECKSUM-FIX.md) |
| 构建假设与SDK接口差异 | FPAI无python3；Array::get_mutable返回Object*，应使用Array::set；PowerShell遇stderr曾截断真实编译错误；r5误读私有字段 | 审计放在主机、完整捕获日志再看退出码、使用实际头文件及公共API，新身份重构建；未安装容器Python或改SDK。见[编译修正](tools/pose-v1/CPU-ADAPTER-COMPILE-FIX-20261006.md) |
| Host算子注册和布局缺口 | 五节点缺TopK/GatherElements/ScatterND注册；便携内核拒绝merged_distr，安装CustomOp或仅设目录不能证明支持 | 应用侧最小注册/全有效临时描述适配，原Gather保持；107例/59,600值通过。只支持已验证FP32规格，不泛化到任意布局。见[CPU验收](tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md) |
| SDK部署后绑定ID变化 | 原1173HardOp仍在原图中，实际部署合并为七ZG组；按原8622直接找绑定产生误报 | 使用真实绑定＋merge_from＋固定同步表追溯完整唯一覆盖，不降低覆盖要求，不把组数或同步层数当原算子数。见[r6来源](tools/pose-v1/MIXED-FRAME-STATE-R6-SOURCE.md) |
| 三样本输入不同却输出完全相同 | caller/Input0正确，CPU数学正确；r5层计数跨帧累加，旧计数提前满足SDK本帧完成阈值 | r6帧边界SDK reset(1)、计数0→745、输出就绪确认；三帧不同/重复首帧所有内容逐位一致。当前范围已解决；失败时约40ms不作性能结果。见[r6结果](tools/pose-v1/MIXED-FRAME-STATE-R6-RESULTS.md) |
| ONNX与板端候选数值对照 | 同槽坐标最大差约1.32–2.03，各端最佳坐标最大差约0.016–0.028（原始单位）；本轮追加分析板端同分相邻项29/30/31，ONNX为1/2/0 | 排名/候选身份尚未证明，不能把大差异都归于排序，也不能仅用最佳小误差宣称通过；扩大固定样本后再讨论容限。见[离线分析](tools/pose-v1/evidence/next-phase-20261006/existing-evidence-analysis.json) |
| 有效吞吐与取证开销 | 四次带取证forward中位207.230065ms，另测预处理中位5.781265ms；相加约213.01133ms，超出5Hz的200ms预算约13ms | 这是提示性预算，不是持续基准；先测最小日志而保留SDK profiling/同步，再按拆分决定优化。不得将显示刷新或重复旧输出计入推理更新率 |
| HDMI720p60与双路配套 | 参考默认1080p，当前25122301工程/寄存器/像素时钟配套不明确；软件改宽高不能证明720p60，VPU驱动存在不代表RTSP可用 | 仍待配套及实屏/编码验证，目标不擅自降低，不写候选显示寄存器或替换BOOT。见[HDMI审查](tools/pose-v1/HDMI-STATIC-AUDIT.md) |
| 预处理人工相位边界 | 300真实样本逐位一致，但人工±π周期误差2.333111/2.693437rad仍失败，用户明确降为非阻断诊断 | 保留失败，不能把真实样本通过扩大为普遍数学等价；后续真实CSI相位异常仍需停止分析。见[300样本结果](tools/pose-v1/RESULTS-300.md) |

#### 下一阶段准备实际完成（2026-10-06）

代理仅读本机既有回传和固定样本，新增[prepare_next_phase.py](tools/pose-v1/prepare_next_phase.py)并实际生成已有数值/排序/时间预算分析。
从预处理已通过的300份记录，按九组各第一/中间/最后确定27候选；[JSON](tools/pose-v1/evidence/next-phase-20261006/proposed-27-cases.json)/[TSV](tools/pose-v1/evidence/next-phase-20261006/proposed-27-cases.tsv)记录case、真实frame_id、路径及SHA256。
27份CSI、固定输入与Host输出身份一致、参考有限；仅候选选择，不是27样本ONNX或Lite模型验收。
[下一阶段具体方案](tools/pose-v1/NEXT-PHASE-PLAN-20261006.md)已编写：E0运行核心→N1九组数值扩展→P1低取证基线，H0本机配套资料并行；E1网络/渲染及视频在结果审查后实施。
本轮未修改r6运行源码、创建新Conda/依赖、交叉编译或接入板端；新28次推理/33次性能运行、容限及视频配置尚未批准执行。

### 对后续开发的参考

下次唤醒先读[恢复入口](tools/pose-v1/RESUME-20261006.md)，以最新快照和产物身份续接；历史“当前/下一步”不作执行入口。整体百分比只针对回放首版工程估算，训练旁支、实时采集终版与数值/视频验收分开记录。

先固定输入和身份，再将CPU注册/Host桥、SDK数据内存、Session部署、真实前向分开核验，可定位跨PS/NPU边界失败。
SDK拷贝到Host不等于NPU同步已证明；ADDR/BOTH不解引用，区域/缓冲区或融合编号不明确就保存失败讨论。
仅为临时内核描述去除已验证冗余分布，模型声明、原Gather和NPU分配保持。

ONNX基线可直接支持部署数值比较，报告全部槽位的最大/平均绝对误差、RMS、P95、逐位一致性及最佳候选变化。
相同槽位不能推定同一候选身份，模型原始单位不代表物理标定/MPJPE，三样本不代表全测试集精度。
下一轮先固化正确帧生命周期、扩大固定样本和测量低日志开销；性能与数值各自有证据门检，不用一种通过替代另一种。
旧阶段快照已折叠保留，当前操作入口以r6结果及新计划为准，不执行历史“下一步”命令。
误差容限必须依据实测再讨论；超时、OOM、总线/SDK异常、非有限或身份变化均停止，不自动重试/复位/改模型。
三样本完整PS/NPU模型工程已通过；部署数值容限、HDMI/RTSP、≥5Hz/延迟和30分钟闭环仍待验证，首版尚未完成。

## 2026-10-05至2026-10-06：CPU算子最小注册适配与Lite独立数值验收

### 工程内容总结

最新验收（2026-10-06）：用户已完成r2交叉编译、Lite测试及完整回传，代理直接文件核验通过。
107用例（18正常、89异常拒绝）、12条注册前后记录匹配；22份输出共59,600个float32值
与NumPy参考逐位一致、全有限、最大差0。五个缺失节点已补齐init/forward并在原规格前向通过，
原Gather实现保持并通过；包282项/回传40项哈希、程序/模型/SDK身份一致，ldd解析完整，退出0/stderr空。
已完成的是固定Host内存/全有效分布的独立候选门检，仍未接入正式模型或验证NPU数据交接。
完整总结及适用限制：[CPU-ADAPTER-RESULTS-20261006.md](tools/pose-v1/CPU-ADAPTER-RESULTS-20261006.md)，
独立证据：[cpu-adapter-independent-review-20261006.json](tools/pose-v1/evidence/cpu-adapter-independent-review-20261006.json)。
下文保留交付、失败、批准修正及逐阶段记录；其中未编译/待回传均为当时状态。

针对ARM Icraft/CustomOp 3.39.0已查明的TopK、GatherElements、ScatterND注册缺口，
按用户批准范围交付[隔离模块](software/pose_v1/src/host_cpu_adapter.cpp)、
[独立检查器](software/pose_v1/src/host_cpu_adapter_check.cpp)及独立CMake目标。
显式注册五个缺失节点的三类函数，禁止覆盖原注册；Gather原后端参与单独测试，CPU Matmul不补齐。
复用SDK明文内核，检查FP32规格、轴、参数、Host存储和全有效分布，只清除临时TensorDesc的分布信息。
原推理源码/CMake和固定ZG模型哈希保持，没有接入正式混合推理器或更改SDK、权重、BOOT。

交付NumPy固定合成参考生成、FPAI独立交叉编译、Lite受限CPU运行及回传复核脚本，
设计覆盖107个用例（18个正常、89个拒绝）和22份正常输出；这些数量为设计，尚未生成或运行。
已完成SDK签名与真实六节点规格的静态审查、Python AST和PowerShell语法检查；shell为LF。
**没有交叉编译或算子前向验收，也没有访问板端设备。** 构建和测试由用户执行，失败即停止讨论。
交付身份及静态检查见[evidence/cpu-adapter-source-delivery-20261005.json](tools/pose-v1/evidence/cpu-adapter-source-delivery-20261005.json)，
逐条命令见[CPU-ADAPTER-COMMANDS.md](tools/pose-v1/CPU-ADAPTER-COMMANDS.md)。

### 对后续开发的参考

可复用的路径是“核对实际ARM注册→固定原包/头文件身份→应用侧隔离注册→真实规格的独立数值参考”。
完整明文后端注册文件包含大量既有注册，不能整体引入；ICRAFT_CUSTOM_DIR也不能替代实际函数注册验收。
本阶段仅接受Host内存和全有效分布，不证明NPU内存同步、去填充、完整模型Session或性能可用。
用户先完成测试包及构建，代理核对后再实板CPU测试；通过后仍须讨论正式PS/NPU交接和推理器接入。
CPU Matmul浮点参考缺口、完整推理数值门检与HDMI/RTSP仍单独保留，不能借本次源码交付宣布闭环通过。

2026-10-06执行反馈与复核补充：用户已生成107用例，实际测试包路径为
`.local/pose-v1-cpu-adapter/package/20261005`。代理只读核对282项清单哈希、18正常/89拒绝用例、
22份正常参考产物及5份构建文件/副本匹配；这仅验收打包身份，不是SDK前向数值通过。
用户构建显示GCC9.4.0/CMake3.24.2后，在容器python3执行处退出127，未进入CMake配置/编译。
具体日志与产物身份见[evidence/cpu-adapter-build-failure-20261006.json](tools/pose-v1/evidence/cpu-adapter-build-failure-20261006.json)。
构建脚本不应把未经核验的容器Python作为既有前提；已准备[修正候选](tools/pose-v1/CPU-ADAPTER-BUILD-FIX-20261006.md)，
应用/新构建尚待用户批准，未安装依赖、改生效脚本或执行Docker/板端测试。原失败目录和测试包保留。

2026-10-06随后批准及应用：用户明确同意该修正，Build-CpuAdapter.ps1已与审阅候选逐字节一致。
SDK版本查询仍在FPAI，六头文件/Host库由Docker cp -L导出、Windows PowerShell/.NET哈希核对；
原身份门禁保持，无新增依赖或候选C++/CMake变化。原脚本已备份，测试包/manifest及旧失败目录保持，
新构建记录会包含实际构建脚本哈希。生效脚本语法解析0错误；**尚未执行修正版构建、容器导出或算子测试**。
应用证据见[evidence/cpu-adapter-build-fix-applied-20261006.json](tools/pose-v1/evidence/cpu-adapter-build-fix-applied-20261006.json)，
用户从[命令B](tools/pose-v1/CPU-ADAPTER-COMMANDS.md)使用新标签`cpu-adapter-20261006-r1`开始。
该方法可将审计工具依赖放在已确认的Windows环境，同时核对真实ARM文件；仍需用户实跑确认Docker导出/编译，
不能仅凭修正或静态检查宣称算子和mixed通过。上述待批准文字为此前状态。

随后r1执行反馈复核：用户构建已通过SDK身份核验及CMake配置/生成，代理读取导出六头文件、
Host so与版本/源码副本并核对身份匹配。编译检查器时PowerShell Stop在原生stderr处中断，
本地日志未保存实际error正文，编译/链接未完成；未运行算子。
静态确认三处测试代码的Array::get_mutable()->at错误，Object*没有at，应使用Array::set；
这是源码API审查发现，不能声称已取得完整编译诊断或排除其他问题。
已交付[两文件修正候选](tools/pose-v1/CPU-ADAPTER-COMPILE-FIX-20261006.md)，
尚待批准，生效源码/脚本未改、未重编译。证据
[evidence/cpu-adapter-compile-failure-r1-20261006.json](tools/pose-v1/evidence/cpu-adapter-compile-failure-r1-20261006.json)。
后续参考：原生工具stderr不能自动等同于命令失败，日志应完整捕获并最终核对真实退出码；
容器审计通过也不能替代C++编译和实际Host数值验收。

随后用户批准两项修正，已按[审阅补丁](tools/pose-v1/CPU-ADAPTER-COMPILE-FIX-20261006.candidate.patch)
修正检查器三处Array修改及构建日志捕获。两生效文件与候选逐字节一致，原文件已备份；
SDK身份门禁、原生退出码门禁、注册模块及数学参考逻辑保持，旧测试包/manifest和失败目录未改。
生效PowerShell语法0错误；尚未生成r2包、交叉编译或测试，不能宣称已排除其他编译问题。
应用证据：[evidence/cpu-adapter-compile-fix-applied-r2-20261006.json](tools/pose-v1/evidence/cpu-adapter-compile-fix-applied-r2-20261006.json)。
用户按[更新命令A/B](tools/pose-v1/CPU-ADAPTER-COMMANDS.md)生成新身份包并以新r2目录构建，
代理核对新旧数据/参考产物及构建证据后再进行既定Lite测试；源码修正不能通过回写旧哈希掩盖来源变化。

2026-10-06 r2构建验收补充：用户生成新包并在FPAI以GCC9.4.0/CMake3.24.2、ARM Icraft/CustomOp3.39.0
完成配置、两文件编译及链接，日志无error/warning正文。代理只读复核282项包文件、5份源码/副本、
构建脚本/manifest与ARM程序SHA256，六份导出SDK头文件及Host库/版本全部匹配。
新旧281项非manifest文件完全相同；数学输入、参考、模型及板端脚本未变，身份更新没有改变测试内容。
程序为AArch64 PIE，SHA256 `8cf2017cedf6a97f98ce485d979239b659291f3c91d3a3d550382c1c94588622`；
ELF直接依赖含Host/XRT/XIR/Utils及标准库、没有ZG/AIU，无RPATH/RUNPATH。
证据：[evidence/cpu-adapter-r2-build-review-20261006.json](tools/pose-v1/evidence/cpu-adapter-r2-build-review-20261006.json)
及同目录cpu-adapter-r2-build-20261006-build.log/build-result.json/sdk-audit.json。
已完成的是用户交叉编译及产物复核，未运行ARM程序、未验收板端库加载/注册前向/107例数值或NPU。
下一步用户按[命令C](tools/pose-v1/CPU-ADAPTER-COMMANDS.md)一次受限Lite Host测试并回传完整证据。
后续参考：可复用“保留旧包/旧错误→新源码身份包→逐文件对照数据参考→ELF直接依赖检查”的追溯路径，
但编译/链接成功与直接依赖范围不能替代板端实际加载、间接依赖和算子数值验收。

目录前置说明补充：用户报告Lite测试子目录mkdir因No such file or directory失败。
原命令遗漏了历史父目录存在性的前置检查；已补充[命令C](tools/pose-v1/CPU-ADAPTER-COMMANDS.md)
中的只读ls检查及仅对父目录mkdir -p、对子目录普通mkdir的步骤，保持同一批准路径和禁止复用旧测试目录。
实际父路径未独立确认，不认定重启/清理为原因；代理未创建/传输/执行，目录成功和CPU测试仍待用户结果。

后续用户Lite运行反馈：截图显示已进入批准目录，输入/清单/程序存在、执行权限设置后
sh测试脚本及exit.txt均0，stdout报告107用例完成、stderr为空；summary标记cpu_candidate_tests_passed，
device_opened/full_model_executed/mixed_verified均false。记录为**用户执行及程序内部通过报告**，
尚未完成独立证据验收，本地没有完整回传；注册前后12条记录、22份实际输出和SDK/程序哈希仍待联查。
证据：[运行截图](tools/pose-v1/evidence/cpu-adapter-board-run-feedback-20261006.png)及同名JSON。
用户接下来执行[命令D](tools/pose-v1/CPU-ADAPTER-COMMANDS.md)，完整回传后再作CPU门检结论。
不重跑C、不依据摘要直接接入正式推理器；本次仍不是完整模型/NPU/双路闭环验收。

完整回传后最终复核：用户复核JSON与代理独立逐文件、逐用例及数值比较一致，上方最新验收成立。
两次主机报错来自命令被拆行，完整命令随后成功，不需要重跑算子。
对后续开发的参考补充：当前已证明标准类型的应用注册和临时描述适配能够解决本版本五节点CPU缺口，
但只覆盖HostDevice CPTR及全有效分布；真实NPU缓冲区/同步/搬运、完整Session、浮点参考和性能均须另验。
CPU Matmul参考缺口保持，不改变正式Matmul NPU分配；后续正式推理器接入先讨论批准。

## 2026-10-05：独立混合推理门检源码与命令交付、HDMI静态审查

### 工程内容总结

目标是在已通过的真实CSI预处理门检基础上，为2024 epoch442的PS/NPU混合推理建立独立核验程序。
平台为悟净Lite、运行FPGA版本25122301、板端Icraft/CustomOp 3.39.0；源码接口按本机3.39.0 SDK头文件及厂商导出目标审查。
新增`software/pose_v1/src/inference_check.cpp`和默认关闭的SDK CMake目标：离线检查、独立设备probe、
optimized Host参考和ZG330/Host混合推理，保留100候选的分数/姿态、实际后端回调、帧号、阶段耗时及失败记录。
无显式reset/check、自动回退、模型修改或视频设备动作。

编写用户执行的FPAI交叉编译脚本、Host独立DLL启动器、原三份已验收CSI/模型哈希打包工具、
ONNX参考及数值统计/回传校验工具，逐条说明执行位置、前置条件、产物和停止条件。
资料及入口：[INFERENCE-COMMANDS.md](tools/pose-v1/INFERENCE-COMMANDS.md)、
[inference_gate.py](tools/pose-v1/inference_gate.py)、[构建脚本](tools/pose-v1/Build-Inference.ps1)。

HDMI源码静态核对确认包装器默认RGB565/1080p，仅写帧缓存地址；本地参考RTL存在可写时序项和720p参数分支，
但与当前BOOT的工程身份、像素时钟及寄存器配套尚无充分证据。
已记录源码位置及垂直前后肩命名差异，见[HDMI-STATIC-AUDIT.md](tools/pose-v1/HDMI-STATIC-AUDIT.md)。

**完成范围是源码、命令交付和静态资料审查。** 按新分工，没有执行编译、软件测试、ONNX/Host/NPU推理、
Docker/SSH命令或设备初始化。SDK实际构建目录、Host编译工具和ORT依赖待用户查询。
没有新的数值/性能实测结果，不将本条记录解释为NPU或首版闭环通过；旧300份结果、模型及预处理源码保留。

用户随后执行A环境查询并提供截图，已核验FPAI GCC9.4.0、CMake3.24.2、Icraft arm64 3.39.0。
SDK只找到HostBackend配置，ORT未找到，Windows cmake/cl当前PATH不可见；
SDK后端包内容/命名和CustomOp状态需补查，不能判定运行库必然缺失或全机没有编译工具。
已提供只读补充查询命令，见[ENVIRONMENT-QUERY-20261005.md](tools/pose-v1/ENVIRONMENT-QUERY-20261005.md)。
此补充是用户操作后的部分环境核验，不是构建、推理或依赖安装通过。

用户再补查目录及已安装包文件后，已核验SDK配置目录`/usr/cmake`含Host/ZG330配置、aarch64导出及对应头文件/库；
FPAI Icraft/CustomOp均arm64 3.39.0、icraftmdzthirdparty arm64 0.1.1，状态均已安装。
已更新执行说明的SDK目录，可继续用户固定打包/交叉编译；尚无编译、链接或推理结果。
此前“仅Host配置/CustomOp待查”为早期查询状态；ORT缺失及Windows工具PATH不可见仍保留。

**用户交叉编译完成补充**：已完成原三份真实样本包以及FPAI配置/编译/链接，实际构建目录
`.local/pose-v1-build/inference-20261005-165059-043b0c40`。工具为GCC9.4.0/CMake3.24.2，SDK目录`/usr/cmake`。
二进制是AArch64动态链接PIE，SHA256
`d1006f9bd78050ffa484c64bf74fb62542d270c7acca5068e9da611a5bdc05e5`；声明Host/ZG330后端等运行库依赖。
代理读取实际日志和产物，7份源码记录、11份包文件大小/哈希、二进制哈希全部匹配；未代执行构建或软件测试。
复核证据：[cross-build-review-20261005.json](tools/pose-v1/evidence/cross-build-review-20261005.json)。
上文“未编译”为初次交付时的历史状态；现在仅传板/加载/离线接口及推理仍待执行，不把本次结果扩大为板端ABI或NPU通过。

**D阶段诊断补充**：用户已传板并核对程序哈希，匹配本次构建；ldd已列出的依赖均解析成功。
包校验失败为清单CRLF问题：文件名末尾均出现CR；代理只读检查本地清单为1043字节/11行CRLF，
定位到inference_gate.py默认文本换行写入。这是脚本遗漏，不是已证明的模型损坏或哈希不符。
仅交付[候选修正方案](tools/pose-v1/CRLF-CHECKSUM-FIX.md)，未改生产脚本/包、未重新校验或运行inspect。
包完整性及设备/推理验收仍未通过，修正执行待用户同意；二进制和模型不需因该换行问题重编译/更换。

**D阶段后续实板结果**：用户用新清单`files.lf.sha256`校验，11项全部OK且退出码0，
板端样本/模型包完整性通过；随后ZG图inspect退出码0。
证据：[板端校验及inspect退出截图](tools/pose-v1/evidence/board-checksum-inspect-exit0-20261005.png)。
graph-io.json、stages.jsonl、run-config.json及stderr尚未提交，离线接口验收仍待产物复核。
没有SDK设备初始化或推理结果；生产打包脚本候选补丁尚未应用，不能把板端清单处理当作脚本修复已完成。
前述校验未通过和inspect未运行为历史状态，已有inspect-zg应保留，不重复运行或覆盖。

**D阶段离线接口验收补充**：用户进一步提交产物内容，输入[1,180,60]，输出按分数[1,100]、
姿态[1,100,14,3]顺序，符合本次二进制的float32门禁；阶段started→offline_inspection_complete。
mode=inspect、device_init_allowed=false，stderr为空，目录仅graph-io/run-config/stages，无failure.json。
结合包校验和退出码0，D离线接口检查通过，证据：
[离线产物截图](tools/pose-v1/evidence/board-inspect-artifacts-20261005.png)。
此检查未加载RAW参数、执行模型或打开设备；下一阶段先核对timeout/并发占用及BOOT是否保持，不能扩大为NPU功能验收。
截图中的板端文件时间为Mar 13，不能作为本次操作的准确墙钟时间；按用户提交日期2026-10-05归档，未调整板端时钟。

**E前置查询复核补充**：用户查询/usr/bin/timeout，版本GNU coreutils 8.30；probe目录及三份日志均不存在，
首次未运行的结果符合预期。可见进程列表未见明显AI/HDMI/编码用户应用，kbase/mvx等为内核线程条目，
其名称不作为运行推理、编码或已发生故障的依据。证据：
[timeout和进程列表上半部分](tools/pose-v1/evidence/board-probe-preflight-20261005-1.png)、
[进程列表及目录查询](tools/pose-v1/evidence/board-probe-preflight-20261005-2.png)。
尚待用户确认BOOT/运行位流保持及无其他演示访问设备；未执行SDK初始化、模型推理或自动停止进程。

**E探测实际执行补充**：用户随后执行固定30秒、TERM后5秒kill-after的probe，退出码0；
device-version.json回报device=25122301，与既有运行版本一致，icore文本待进一步回传复核。
用户已保存probe.dmesg.log；证据：[probe返回及版本截图](tools/pose-v1/evidence/board-probe-exit0-20261005.png)。
检查器源码固定写出compatibility_passed=false，含义为兼容性尚待验收，不是SDK报错。
stdout/stderr、stages/run-config及内核日志内容尚未提交，E完整门检待复核；没有执行混合模型或DMA/NPU计算验收。
本次设备初始化由用户执行，代理仅审阅截图和源码，不重跑probe、修改标记或停止进程。
前述“probe未执行”为此前准备阶段状态。

**E初始化探测限定范围验收**：用户提交probe目录、运行配置、阶段、stdout/stderr及内核尾部，
阶段started→opening_device_not_readonly→probe_complete_requires_review，mode=probe/device_init_allowed=true，
目录无failure.json，stderr为空。stdout明确Device initialization successful；协议AXI、设备zg330aiu，
NPU=0x40000000、DMA=0x80000000、device=25122301、icore=FMSHZGV3TECH-AID - 24160628。
结合退出码0，Device::Open/version探测通过，证据：
[产物与初始化日志](tools/pose-v1/evidence/board-probe-review-20261005-1.png)、
[内核上下文上段](tools/pose-v1/evidence/board-probe-review-20261005-2.png)、
[内核上下文末段](tools/pose-v1/evidence/board-probe-review-20261005-3.png)。
提供的dmesg尾部未见探测相关总线/DMA错误；EXT4恢复与journal异常关闭/更换信息处于启动阶段，
不归因于probe，不自动执行文件系统修复。板端日志墙钟为2026-03-13，与当前归档日期不同，未调整板端时钟。
compatibility_passed=false是检查器固定待验收标记，保持原值；本次不能作为模型、Host/NPU计算或性能验收。
下一步数值参考仍受ORT缺失及Windows Host编译工具待确认约束，不自动安装或跳过参考直接进入mixed。

**Windows Host工具只读定位补充**：用户不确定安装情况后，代理只读检查文件/安装记录，找到
`D:\Visual Studio\ Visual Studio 2022\Community`中的MSVC14.44.35207 cl/link/nmake、C++头文件/库、
VsDevCmd.bat与CMake文件元数据3.31.6-msvc6。路径中第二层目录名开头有一个空格，不应手工删去。
这证明工具文件存在，未证明Windows SDK、开发终端初始化、CMake VS实例识别或Host编译通过；
默认vswhere和常见Windows Kits注册表入口未找到/未返回记录，不自动修复或安装。
已交付用户临时环境查询命令：[WINDOWS-HOST-ENV-CHECK.md](tools/pose-v1/WINDOWS-HOST-ENV-CHECK.md)，
静态证据：[定位记录](tools/pose-v1/evidence/windows-host-tool-discovery-20261005.json)。
代理未运行编译器、CMake或项目软件；ORT缺失及参考数值验收保持待处理。

**Windows终端首次启动排查补充**：用户命令截图中目录名漏掉开头空格，返回“系统找不到指定的路径”。
代理只读复核实际名称首字符为32，带空格VsDevCmd路径存在、不带空格路径不存在；
此失败不作为SDK缺失/编译器损坏的证据。已将同一查询步骤改为从真实目录项自动构造路径，
避免手写空格；用户终端初始化仍待执行/复核，代理未启动开发终端或修复安装。
证据：[路径错误截图](tools/pose-v1/evidence/windows-host-path-error-20261005.png)，
命令入口仍为[WINDOWS-HOST-ENV-CHECK.md](tools/pose-v1/WINDOWS-HOST-ENV-CHECK.md)。

**Windows查询窗口待确认补充**：用户自动定位启动后已见VS开发终端横幅；另一截图where cl未找到、
架构/SDK变量原样显示。这证明查询窗口没有相应环境，不足以确定初始化后的同一进程是否失败。
需先确认是否另开CMD：初始化只在当前子进程生效，另外打开的终端不会继承。
代理只读确认start/parse/winsdk/vcvars脚本存在，横幅v17.0为vswhere缺失时的默认值，
不作为安装版本或SDK缺失结论；未修改/修复安装，Host参考仍未编译或执行。
证据：[启动横幅](tools/pose-v1/evidence/windows-host-banner-20261005.png)、
[查询结果](tools/pose-v1/evidence/windows-host-unset-query-20261005.png)。

用户随后明确第二张查询是在另外打开的CMD中执行，未继承原初始化环境；此前窗口歧义已澄清。
不能据第二张图判断原窗口初始化失败或SDK缺失，用户下一步回原窗口查询；未修复安装或开始Host构建。

**原开发终端实际查询补充**：用户回原CMD后where cl显示MSVC14.44.35207 Hostx64/x64，
目标x64、VSINSTALLDIR正确，CMake实际查询3.31.6-msvc6；环境继承问题已解除。
WindowsSdkDir未设置、WindowsSDKVersion仅`\`，有效Windows SDK尚未识别，Windows Host构建仍未执行。
代理只读核对4个厂商v10.0登记入口及5个常见Windows Kits目录未找到，不排除未登记自定义SDK目录。
证据：[原窗口工具及SDK查询](tools/pose-v1/evidence/windows-host-sdk-query-20261005.png)。
另静态核对已编译检查器包含无Device::Open的host参考模式，形成
[参考路线及ORT解析候选](tools/pose-v1/REFERENCE-NEXT-PLAN.md)供讨论，未执行或安装，候选不是完成成果。

**Lite Host已批准后的命令交付补充**：用户明确同意先用Lite Host作参考，代理已完成
[LITE-HOST-COMMANDS.md](tools/pose-v1/LITE-HOST-COMMANDS.md)的资源查询、固定三样本Host运行、诊断/回传命令及停止条件，
并更新执行路线记录。复用现有二进制、optimized模型和固定参考张量，未修改C++源码或重新编译。
当时仅完成命令/文档交付；后续用户资源查询已完成，Host执行仍待完成，不记为模型通过；
ORT预览/安装未批准，正式NPU/双路及误差门检保持，不能凭B批准跳过参考进入mixed。

**Lite Host资源前检复核补充**：用户截图显示总内存993 MiB、available 744 MiB、Swap 0，/tmp所在根文件系统剩余47G；可见进程未见明显其他推理/视频用户应用，目标输出前缀未发现旧文件。资源前检已完成，可继续已批准的一次300秒Host参考；峰值内存、算子支持、耗时及输出仍未验证。证据：[内存与磁盘](tools/pose-v1/evidence/lite-host-resource-query-20261005-1.png)、[进程与结果路径](tools/pose-v1/evidence/lite-host-resource-query-20261005-2.png)。代理仅审查及记录，未执行软件或设备操作。

**Lite Host首次执行反馈（未通过）**：用户随后执行一次已批准的受限Host参考，截图退出码1；[执行证据](tools/pose-v1/evidence/lite-host-exit1-20261005.png)。具体失败阶段与原因待日志，未取得可验收的参考数值，不将失败试跑写为模型通过。暂停重跑、覆盖目录及mixed，下一步由用户读取现有stdout/stderr、阶段/失败记录及内核上下文；代理未执行修复或改变源码/模型/环境。

**Host失败日志审查完成补充**：用户提交产物/日志截图，定位到Session创建时op_id=1 MatmulNode没有后端绑定，阶段输入验证→参数懒加载登记→failed_stop_no_retry；mode=host/device_init_allowed=false，未开始样本前向。内核尾部未见本次OOM、available 687 MiB；根因仍须区分板端库构建范围、依赖/注册及文件身份。已完成[失败审查](tools/pose-v1/HOST-BINDING-REVIEW-20261005.md)，证据为同目录evidence/lite-host-binding-failure-20261005-1.png至-3.png；未执行修复或新的软件/设备操作。正式混合图六个Host计算算子没有Matmul，本次失败不能扩大为NPU路线失败或数值通过。

**特殊问题协助与Host库只读审计完成补充**：用户授权一般软件操作仍自行执行，遇特殊问题代理可直接接入工具；已更新Agents.md并保留决策/变更审批。用户同时批准审计，代理SSH读取确认Icraft/CustomOp arm64 3.39.0、icraft包校验未报告差异，实际Host库与原始安装包SHA256一致，导出配置含CudaDefault、readelf存在。完整日志[board-host-library-audit-20261005.stdout.log](tools/pose-v1/evidence/board-host-library-audit-20261005.stdout.log)、同前缀stderr/退出码及[原包静态审查](tools/pose-v1/evidence/original-arm-host-package-review-20261005.json)。最终审计退出码0、stderr空；未执行模型、NPU初始化或修复。深层算子注册原因仍待验证，[注册探针](tools/pose-v1/HOST-REGISTRY-PROBE-PLAN.md)仅为待批准方案，不记为完成成果。

**独立CPU注册诊断完成补充（更新上述候选状态）**：用户批准后，代理在FPAI GCC9.4/CMake3.24.2/ARM Icraft3.39.0交叉编译独立探针、传Lite新目录并运行一次30秒受限查询。退出码0、stderr空，5项回传哈希匹配；探针32,744字节、SHA256 4106daf64086e478b7540788eab52d4551680cb11f8b8b104a4f582d86d6d05c。Matmul无init/forward注册，正式ZG图的188/437 TopK、192 GatherElements、582/649 ScatterND同样无注册，442 Gather有注册。定位出全CPU参考及混合图PS部分的注册阻断，mixed保持停止；没有执行模型/算子前向或访问NPU。原源码、推理二进制、模型/SDK身份保持，结果[HOST-REGISTRY-RESULTS-20261005.md](tools/pose-v1/HOST-REGISTRY-RESULTS-20261005.md)，证据[review.json](tools/pose-v1/evidence/host-registry-20261005/review.json)。成功范围为诊断本身，不是模型部署/首版验收。

**Matmul执行目标静态核对补充**：原仓库quantized图130个Matmul含op1均为@zhuget(330)，adapted图132个也为ZG目标；最终ZG图的CPU计算节点无Matmul。此前CPU Matmul失败属于optimized图全CPU数值参考路径，未把正式部署矩阵计算迁到CPU，也未证明NPU不支持。此补充仅核对编译目标，未修改模型或执行NPU；具体见上述注册结果文档的路径澄清。

### 对后续开发的参考

先固定输入和模型身份，再分离设备初始化、Host参考和实板完整混合执行，方便定位接口、后端或数值差异。
注册探针可在不访问设备、不做前向的情况下核对实际XIR后端能力；库内通用计算代码或包完整性不能替代注册查询。此次五个ZG Host节点缺注册，不能仅换CPU参考平台就认为混合推理畅通；先核对官方注册/加载机制并讨论配套方案，Gather有注册也仍须前向数值验收。
Host与ONNX使用同一参考张量；Lite必须从原CSI做PS预处理，保留真实相位标量/周期门检。
六个Host算子和ZG后端的运行路径须有证据，分数/坐标容限待实测讨论，不能只凭可画出骨架验收。
诊断回调/写盘会影响耗时，三样本结果不能代替连续性能和30分钟稳定性测试。

此次交叉编译证明所用arm64 SDK声明和导出目标能编译/链接本检查器；动态库还须在Lite解析并验证实际加载。
构建日志中的`shared object`与`NOW PIE`组合是Linux PIE可执行程序的表示，不能仅据该词判为错误库文件。

Windows生成供Linux使用的校验清单须明确换行格式，并校验实际生成的新清单；
包哈希通过与离线程序退出码0分别证明文件身份和本次命令返回，图接口/阶段产物仍须独立核对。

普通PATH和安装记录查询无结果时，可核对自定义安装目录及真实工具文件；临时开发终端再确认SDK/架构。
运行库安装、文件存在、工具可调用、能编译和模型数值通过是不同层次，不能相互替代。

HDMI画面尺寸与视频扫描时序/像素时钟应分别核验；可编程RTL线索不能当成当前位流的寄存器写授权。
后续软件操作由用户执行，代理依据日志迭代核心程序；新依赖、启动配置、模型或FPGA工程变更另行讨论批准。

## 2026-10-01：悟净 Lite 流水灯 FPGA 开发全流程验证

### 工程内容总结

**目的与结果**：通过独立 PL 流水灯，验证“编写代码 → 行为仿真 → Procise 综合 → 布局布线与时序检查 → 生成位流 → JTAG 下载 → 实板观察”。各阶段已完成，用户现场确认“四颗 LED 按预期循环”，本次功能验收通过。

**平台与工程**：悟净开发板 Lite，目标器件 `JFMQL30TAI676H`；原生 FPGA 实现使用 `C:\FudanMicro\Procise` 下的 Procise `2025.1.1 temp / SVN 32494`；纯 RTL 行为仿真使用现有 Vivado 2019.1 的 XSim。工程位于 [FPGA/lite_led_chaser](D:/FPGACompetitionProject/FPGA/lite_led_chaser/README.md)，不含厂商 IP。

**实现功能**：使用板载单端 100 MHz 时钟，每计数 25,000,000 个周期切换一颗 LED，按 PL_LED1→PL_LED2→PL_LED3→PL_LED4 循环，设计步长 0.25 秒、一圈 1 秒。25 位计数器初始为 0，四位灯状态初始为 `0001`；Procise 综合 EDIF 中核对了全部 29 个寄存器的 INIT。

板级连接依据 [JFMQL30TAI_LITE.pdf](D:/FPGACompetitionProject/Docs/开发板手册/JFMQL30TAI_LITE.pdf) 实际 PDF 第 9、10、21、22 页，用户已确认该图纸配套当前 30TAI Lite 板。

| 信号 | 引脚 | 电平/功能 |
| --- | --- | --- |
| 100 MHz 时钟 | AC14 | BANK12，LVCMOS33，约束周期 10 ns |
| PL_LED1 / `led[0]` | J1 | BANK33，LVCMOS15 |
| PL_LED2 / `led[1]` | M6 | BANK33，LVCMOS15 |
| PL_LED3 / `led[2]` | H7 | BANK34，LVCMOS15 |
| PL_LED4 / `led[3]` | J8 | BANK34，LVCMOS15 |

BANK33/34 的 VCCO 为 1.5 V。LED 经 NDS331N 低侧开关驱动，FPGA 输出高电平点亮；FDC 显式锁定上述引脚、电平和时钟，LED 使用 DRIVE 4、SLEW SLOW。

| 验证环节 | 结果与证据 |
| --- | --- |
| 自检行为仿真 | XSim 2019.1 通过；分频值 1、7、19 各检查 200 个周期，覆盖初始化、切换边界、单灯顺序和循环回绕；[仿真日志](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/sim_20261001_115631_342b3c/simulate.stdout.log) |
| 原生综合与实现 | Procise 综合、布局布线完成；LC 13/19650、GCDU 1/32、IOU18M 4/72、IOU33M 1/48 |
| 内部时序 | setup 裕量 4.740 ns、hold 裕量 0.170 ns；setup/hold 各 58 个端点，违例端点均为 0；无缺失时钟、未约束内部端点或组合环；[原生报告](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_120459_3fa8ba/rundir/lite_led_chaser_route.json) |
| 位流复核 | 目标器件、placed FDC 引脚/电平、寄存器 INIT、仿真/构建/当前 RTL 哈希均已核对；StartupClk=JtagClk，UnconstrainedPins=Disallow；[复核记录](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_120459_3fa8ba/build-review.json) |
| JTAG 下载 | Alinx 黑金下载器，实测序列号 `210512180081`；链中 `jfmql30` 为 part 0、IDCODE `0x9372c093`，`ps_dap` 为 part 1；2026-10-01 12:06 下载成功，STAT 回读 `0x40007ffc`；[下载记录](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_120459_3fa8ba/jtag_20261001_120606/program-result.json) |
| 实板功能 | 用户确认“四颗 LED 按预期循环”；没有使用仪器测量周期精度 |

最终位流：[lite_led_chaser.bit](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_120459_3fa8ba/rundir/lite_led_chaser.bit)，5,980,582 字节；SHA-256 为 `a443d8f4bfde85eedc9de0e0328680cbb5d06c364f1113c55b14c4c6f4475eec`。该文件已通过 Procise 下载到 FPGA 易失配置，掉电失效；本次没有写 Flash 或更新 BOOT。

**验收边界**：本次通过的是独立 PL 流水灯和纯 RTL 行为仿真。四个 LED 输出在原生时序报告中保留 `no_output_delay`（High）：它们没有外部同步采样协议，未伪造输出延迟或用时序例外隐藏该项。复旦微网表/布线后仿真、Linux、DDR、PS 应用、DMA、AI 模型及系统接口未由本次测试验证。流水灯全流程使用原生脚本完成，没有通过 MCP 执行。

### 对后续开发的参考

1. **已有可复现的原生起点。** [工程说明](D:/FPGACompetitionProject/FPGA/lite_led_chaser/README.md) 及 `scripts` 中的 `Simulate.ps1`、`Build.ps1`、`ReviewBuild.py`、`Program.ps1` 可作为小型纯 RTL 工程的流程参考。后续设计仍需自己的功能规格、自检仿真和原生实现报告；含 PS、DDR、AI 或专用 IP 的系统工程需另行核对流程。
2. **先从当前 Lite 原理图确认板级条件。** 本次实测可参考 AC14 时钟和四颗 LED 的引脚、电平、有效极性；不能仅根据 LED 的 3.3 V 供电推定 FPGA 输出应使用 LVCMOS33，也不能直接套用完整版开发板约束。其他外设须逐项核对封装、BANK 电压、时钟与接口要求。
3. **注意 Procise 的真实命令和目录行为。** 原生构建使用 `launch_run -stage bitstream`；JTAG 启动经用户批准显式设置 `bitgen lite_led_chaser.bit -g StartupClk:JtagClk`。本机 `launch_run` 完成后回到工程根目录，追加位流生成前应显式切到 `rundir`；否则会生成另一份同名文件。本次复核发现目录差异后停止下载，修正并重新构建才上板。
4. **下载器显示名与 Tcl 参数需要实测核对。** 本机显示 `DIGILENT/JTAG-HS1`，`init_chain` 实际接受 `usb-jtag-hs1`；大写显示名返回参数错误。`program_bit ... -part 0` 中的 0 是本次实际 FPGA 链序号，不是器件数量。更换板卡、下载器或连接方式后应重新枚举和扫链。
5. **以证据判断完成状态。** 保留原始日志、时序/约束报告、源文件与位流哈希以及用户现场确认。退出码为 0 或文件存在不足以独立证明成功；内部时序、外部接口时序、下载状态和物理功能应分别核对。LED 的输出延迟处理不应套用到后续有同步采样要求的接口。
6. **MCP 有可复用的后端基础，但收益仍需实测。** 已通过的 Procise 命令、独立作业进程、报告解析和产物检查可作为 Procise MCP 讨论依据。用户已同意优先讨论 Procise MCP，Vivado MCP 用于仿真和参考工程辅助；以现有 Vivado 2019.1 为准，资料中的 Vivado 2018 版工程仅作思路参考。后续应比较 MCP 输出与原始证据、错误/超时处理及操作效率，再判断实际价值。

MCP 初始状态补记（2026-10-01，原生流水灯完成时）：用户已自行接入 `vivado-mcp`；本会话已发现其工具，并成功执行只读 `list_sessions` 查询，返回“当前没有活跃的 Vivado 会话”。当时仅证明接口可调用；后续验证见下节。本条不将 MCP 接入记为流水灯全流程中的验证环节。

## 2026-10-01：Procise MCP 首版与 Vivado MCP 独立客户端验证

### 工程内容总结

用户明确批准首版范围后，新建 [tools/procise_mcp](D:/FPGACompetitionProject/tools/procise_mcp/README.md)，在 `.local/procise-mcp-venv` 独立安装官方 MCP SDK 2.2.0。七个限定工具实现环境探测、报告读取、流水灯异步构建、状态/日志、产物和复核。真实 stdio 客户端已完成 initialize/list/call 和一次通过复核的新 Procise 构建；内部时序、五引脚/电平、29 INIT、JtagClk、源码/仿真一致性通过，非法调用正确映射为失败。[协议证据](D:/FPGACompetitionProject/tools/mcp-validation/procise-stdio-validation.json)。首次 BGN `Disallow*` 误判已修正并保留失败记录。

首阶段新作业为 `build_20261001_164532_c8ce42`；用户随后批准日志 BOM 识别适配和复验，最新 `build_20261001_170101_78f11a` 已用独立 MCP 新仿真完成完整复核。新位流均未下载。原来已上板的位流、复核和用户观察记录保持原状态；本次没有 Flash/BOOT 操作。首版也不提供任意 Tcl/JTAG、取消或服务重启恢复。

Vivado MCP 当前聊天的 XPR 离线解析已与原始 XML 核对；未改安装的独立 stdio 客户端已通过 Vivado 2019.1 会话、Tcl 错误后继续调用和经现有脚本执行的 XSim 自检。[独立协议证据](D:/FPGACompetitionProject/tools/mcp-validation/vivado-stdio-validation.json)。当前聊天原先启动失败，经逐项批准的诊断确定两个架构环境变量为空，厂商启动器误选不存在的 32 位程序；仅给测试子进程补 AMD64 后，当前聊天会话、版本、错误恢复和 XSim 自检也通过，已关闭测试会话。[当前聊天证据](D:/FPGACompetitionProject/tools/mcp-validation/vivado-live-validation.json)。长期配置未修正。

### 对后续开发的参考

1. 独立作业可复用原生 Procise 后端；MCP 能整合入口和状态，但不能直接替换 Vivado 可执行路径，也没有受控性能/准确率提升结论。
2. 报告适配必须保留原始值和失败记录。EDA 默认值标记、缺字段、错误正文与外层状态不同步，都可能造成误判。
3. 区分独立协议客户端、当前聊天工具发现、后端完成、产物复核和实板功能。成功状态只能覆盖实际验证的阶段。
4. PowerShell 5.1 新 XSim 日志为 UTF-16；批准的 BOM 识别适配已验证 PASS/ERROR 文本保留，并用新 MCP 仿真通过完整复核。编码与工具外层状态都应与真实日志交叉检查。

证据和长期修复讨论候选集中在 [RESULTS.md](D:/FPGACompetitionProject/tools/mcp-validation/RESULTS.md)，根资料索引为 `REFERENCES.md` 第 14 节。Procise 项目配置已批准并写入、CLI 读取正确，但用户选择暂不重载，当前聊天 Procise 调用验收保留待办。Vivado 仅实施已批准的临时子进程修正，不把本次通过扩展为持久配置、GUI/IP 或厂商网表仿真已验收。

## 2026-10-01：Vivado MCP 长期架构配置

### 工程内容总结

用户本轮明确要求实施此前讨论的长期方案，已仅在用户级 Codex 配置的 `[mcp_servers.vivado.env]` 增加 `PROCESSOR_ARCHITECTURE="AMD64"`，避免变量缺失时厂商启动器误选不存在的 32 位 Vivado；其他配置原始字节保留，原文件已备份。读取实际 Codex 配置的新 stdio MCP 进程直接启动 Vivado 2019.1，并回读 AMD64，通过后关闭测试会话，未使用临时启动器。[修改及备份记录](D:/FPGACompetitionProject/tools/mcp-validation/vivado-permanent-config-change.json)、[验证证据](D:/FPGACompetitionProject/tools/mcp-validation/vivado-permanent-config-validation.json)。

### 对后续开发的参考

架构标识只配置在 Vivado MCP 的子进程环境，不修改系统环境或 EDA 安装。配置写入时已有聊天 MCP 进程尚未重启，当时 Procise 暂不重载的选择仍有效；新服务验证与聊天加载状态应分别记录。用户随后自行重载两个服务，并完成下节的当前聊天验收。本节保留配置写入时的范围，不追溯扩大当时验证结论。

## 2026-10-01：MCP 协作流水灯 LED1→3→2→4 开发与实板全流程验证

### 工程内容总结

用户报告已重载 Procise/Vivado MCP，并明确批准 [具体方案](D:/FPGACompetitionProject/tools/mcp-validation/led1324/PLAN.md)，随后明确授权新位流下载。已完成 **Vivado MCP 写入源码 → XSim 2019.1 自检 → Procise MCP 原生综合、布局布线 → 生成位流 → 产物复核 → Procise 原生 JTAG 下载 → 用户实板观察**，各阶段通过。目标为悟净 Lite / `JFMQL30TAI676H`；Vivado 按长期配置直接启动并回读 2019.1/AMD64，无临时启动器；Procise 环境探测为 2025.1.1 temp / SVN 32494，七工具均实际调用。下载环节为原生 Procise，未增加 MCP JTAG 能力。

复用 [lite_led_chaser 工程](D:/FPGACompetitionProject/FPGA/lite_led_chaser/README.md)，修改前将旧 RTL/testbench 备份至 `revisions/led_1234_before_1324`。当前灯序为 LED1→3→2→4→1，仍使用原 100 MHz、25,000,000 周期/步、0.25 秒单灯步长，既定 FDC 和所有执行脚本未改。testbench 以独立预期表检查分频 1/7/19 各 200 周期，实际状态 `0001→0100→0010→1000→0001`，1996 ns 正常结束并打印 PASS。

| 环节 | 结果 |
| --- | --- |
| 仿真 | 当前聊天 Vivado MCP 经 `run_tcl exec` 驱动已有 XSim 脚本；[日志](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/sim_20261001_182621_aa641e/simulate.stdout.log) |
| Procise 实现 | 作业 `5c5f8f383cd74afa87915adc67921a80`，目录 `build_20261001_183334_5f3fc1`，状态 reviewed、退出码 0；LC 11/19650 |
| 内部时序 | setup/hold 裕量 5.962/0.192 ns，各 58 个端点，违例均 0；无缺失时钟、未约束内部端点或组合环；四 LED 的 `no_output_delay` 保留 |
| 位流复核 | 五引脚/电平、29 INIT、JFMQL30TAI676H、JtagClk、当前/仿真/构建 RTL 哈希一致；[复核记录](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_183334_5f3fc1/build-review.json) |
| 原始证据 | MCP 时序/时钟/检查计数等于原生报告；产物大小/哈希等于磁盘；[独立核对](D:/FPGACompetitionProject/tools/mcp-validation/led1324/verification.json) |
| 新位流下载 | 18:50（北京时间）由 Procise 原生 JTAG 下载到 `jfmql30` part 0，退出码 0、SVF 成功，STAT=`0x40007ffc`；[下载与现场确认](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_183334_5f3fc1/jtag_20261001_184939/program-result.json) |
| 实板功能 | 用户确认“灯序和速度均符合预期”，LED1→3→2→4→1，约 0.25 秒/步、单灯循环；未用仪器测量周期精度 |

最终 [lite_led_chaser.bit](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_183334_5f3fc1/rundir/lite_led_chaser.bit)：5,980,582 字节，SHA-256 `285356540f63f5b1a150827777f8e5e411843718976590db0cb39739b5ef7c18`。**同一份新位流已下载并通过用户实板观察**，详细下载记录见下节。为 FPGA 易失配置，掉电失效，未写 Flash/BOOT；未进行整份配置读回。原 LED1→2→3→4 上板证据保留。MCP 服务/配置与 EDA 安装未改，本次 Vivado Tcl 会话已关闭。

### 对后续开发的参考

1. 重载后的当前聊天入口已实际验收，可由 Vivado/XSim 验证纯 RTL 行为，再由 Procise 实现复旦微目标；源码哈希把仿真和位流关联起来，不能仅凭两个工具各自返回成功认定衔接正确。
2. Procise 的原生时序、placed FDC、INIT、位流设置及产物摘要仍是实现依据。与原始报告对照可核验 MCP 适配层；本次时序/资源值与旧灯序不同，不将差异归因为 MCP 提升性能。
3. 原上板记录、独立 SDK 测试与新聊天验证应保留各自源码/产物对应关系。新位流上板须另行讨论批准，不能继承旧版本的肉眼验收结果。
4. 首版仍限当前流水灯工程；没有通用工程、任意 Tcl、下载、取消或重启恢复能力。含 IP/原语、PS/DDR/AI 或高速外部接口的设计须继续核对适配，且本次不证明网表/布线后仿真或完整接口时序。
5. 本次用的是自写纯 RTL，**没有使用 Vivado 现成 IP**。其成功证明前端行为仿真与 Procise 原生实现能够衔接，不能据此认定 Vivado IP、DCP、XCI 或加密源码已经适配复旦微；现成 IP 的复用需另行核对实际综合源码、依赖及厂商迁移流程。

完整步骤与实际返回见 [led1324/RESULTS.md](D:/FPGACompetitionProject/tools/mcp-validation/led1324/RESULTS.md)，索引见 `REFERENCES.md` 14.2。

## 2026-10-01：新灯序位流 JTAG 下载与实板验收

### 工程内容总结

用户在 MCP 位流阶段完成后明确要求“请你将新位流下载上板进行实际验证”。下载前重新核对同一份位流、当前/构建/仿真 RTL、testbench、执行脚本、器件、时序、INIT 和 JtagClk，未重新生成位流。使用原有 `Program.ps1` 经 Procise 原生工具下载，不修改 MCP 服务或配置。

2026-10-01 18:50（北京时间），Alinx/DIGILENT JTAG-HS1 序列号 `210512180081`；重新扫链确认 `jfmql30` part 0 / IDCODE `0x9372c093`，PS DAP part 1。下载退出码为 0，SVF 成功，STAT 回读 `0x40007ffc`，scan/download stderr 为空；位流下载前后 SHA-256 均为 `285356540f63f5b1a150827777f8e5e411843718976590db0cb39739b5ef7c18`。

用户现场确认 **“灯序和速度均符合预期”**，对应 LED1→3→2→4→1、约 0.25 秒/步、同一时刻单灯。新灯序实板功能验收通过，至此“Vivado MCP 写入代码与 XSim 行为仿真 → Procise MCP 综合/布局布线/位流及复核 → Procise 原生 JTAG 下载 → 用户实板观察”完成。下载属于 FPGA 易失配置、掉电失效，未写 Flash/BOOT；未用仪器测量周期精度，也未整份配置读回比对。

证据：[下载与用户确认](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_183334_5f3fc1/jtag_20261001_184939/program-result.json)、[原始下载日志](D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_183334_5f3fc1/jtag_20261001_184939/download.stdout.log)、[板上验证记录](D:/FPGACompetitionProject/tools/mcp-validation/led1324/board-validation.json)。新构建复核记录补充了本次观察与下载入口；旧灯序上板记录、源码备份和原位流保留。

### 对后续开发的参考

1. 同一份经仿真/原生实现核对的代码与位流，现已有新灯序的实板功能证据；下载前确认哈希和重新扫链可避免误用同名旧文件或错误目标。
2. 下载工具成功、STAT 回读与用户观察提供不同阶段的证据。LED 灯序和约定步长通过，不等于仪器精度测量、完整配置读回或其他接口功能验收。
3. 目前可复用 MCP 前端仿真/后端构建，再用既有 Procise 原生脚本进行明确授权的下载。下载并未通过 MCP，首版 MCP 仍无 JTAG/Flash 工具；增加这些能力或扩展到其他设计须先讨论批准。

资料索引见 `REFERENCES.md` 14.3，完整当前工程结果见 [led1324/RESULTS.md](D:/FPGACompetitionProject/tools/mcp-validation/led1324/RESULTS.md)。

## 2026-10-01：Vivado 真实 xlconcat IP → Procise 原生实现 → Lite 实板验证

### 工程内容总结

**目标与结果**：在此前纯 RTL 流水灯已通过的基础上，验证“使用 Vivado 现成 IP，由 Vivado MCP 生成/编写/仿真，再由 Procise 原生综合和生成位流，最后下载 Lite”。用户明确批准 [xlconcat 最小方案](D:/FPGACompetitionProject/tools/mcp-validation/ip-reuse/PLAN.md)，全流程已完成；用户现场确认 **“灯序、速度和单灯状态均符合预期”**。

**平台与实现**：新建独立 [lite_led_ip_bridge 工程](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/README.md)。前端为当前聊天 Vivado 2019.1 MCP / XSim；物理目标为悟净 Lite / `JFMQL30TAI676H`，综合/布局布线/时序/位流与 JTAG 均由 Procise `2025.1.1 temp / SVN 32494` 原生批处理执行。`xc7z030ffg676-2` 只用于 IP 生成/仿真元数据，未作为实板器件；本次未扩展固定旧工程的 Procise MCP，也未改 MCP 配置、EDA 安装、数据库或加载 JFM hook。

Vivado MCP 实际创建 `xilinx.com:ip:xlconcat:2.1` / Rev.3，配置四个 1-bit 输入，生成完整 HDL 和 XCI；源码闭包为顶层 → 生成的 `led_state_concat` 综合包装器 → 厂商 `xlconcat_v2_1_3_xlconcat`。将 state[3]/[2]/[0]/[1] 接到 In0/1/2/3，使 dout 参与灯状态更新，仍是 LED1→3→2→4→1、100 MHz、25,000,000 周期/步、0.25 秒步长。原已验证的 AC14/J1/M6/H7/J8 与 LVCMOS33/LVCMOS15 约束逐字节复用。

**没有用自写 IP 替身或 stub 代替厂商 IP。** 仿真与 Procise 使用同一份生成的综合包装器和未修改厂商 HDL，当前/仿真/构建源码及 XCI 哈希一致。前端 checkpoint=0，`synth_1`/`impl_1` 最终均 `Not started`，本次全部综合由 Procise 执行。原纯 RTL 工程及其上板证据保持。

| 环节 | 结果与证据 |
| --- | --- |
| 真实 IP 与源码 | 包装器/库无新增原语、加密或包含文件依赖；参数和三模块闭包核对；[来源与哈希清单](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/source-manifest.json) |
| Vivado MCP / XSim | IP 全部 16 种输入通过独立真值表；流水灯分频 1/7/19 各检查 200 周期，初始化、步进、单灯和回绕通过；1996 ns 正常结束；[仿真日志](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/runs/sim_20261001_193106_688cd5/simulate.stdout.log) |
| Procise 原生实现 | 构建 `build_20261001_193157_bef06d`；LC 11/19650、GCDU 1/32；setup/hold 裕量 5.962/0.192 ns，各 58 端点、违例 0；[原始实现报告](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/runs/build_20261001_193157_bef06d/rundir/lite_led_chaser_route.json) |
| 位流复核 | 五引脚/电平、29 INIT、JFMQL30TAI676H、JtagClk、全部设计源码一致性通过；综合网表无遗留 IP 黑盒、单元引用均有定义；四 LED 的 no_output_delay 保留；[复核记录](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/runs/build_20261001_193157_bef06d/build-review.json) |
| 下载与实板 | 19:34（北京时间）重新扫链，经 `usb-jtag-hs1` / `210512180081` 下载到 jfmql30 part 0 / IDCODE 0x9372c093；退出码 0、SVF 成功、STAT=0x40007ffc；用户确认灯序、速度和单灯状态通过；[下载与用户确认](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/runs/build_20261001_193157_bef06d/jtag_20261001_193337/program-result.json) |

最终 [lite_led_chaser.bit](D:/FPGACompetitionProject/FPGA/lite_led_ip_bridge/runs/build_20261001_193157_bef06d/rundir/lite_led_chaser.bit) 为 5,980,582 字节；SHA-256 `00c833bb65fec1573ecf0a8cf59c45c50cff76ab7f0a3398696c43be4f608c56`，已下载并通过用户实板观察。原始报告字段/磁盘哈希与复核、源码三处一致性和旧工程保留核对见 [verification.json](D:/FPGACompetitionProject/tools/mcp-validation/ip-reuse/verification.json)。

验收为 FPGA 易失配置、行为仿真、原生内部时序和用户肉眼观察；没有 Flash/BOOT、布线后仿真、仪器周期测量或整份配置读回。Vivado IPI-only/checkpoint 属性提示及 Procise 未使用端口等日志保留，厂商源码未修剪；说明见 [RESULTS.md](D:/FPGACompetitionProject/tools/mcp-validation/ip-reuse/RESULTS.md)。

### 对后续开发的参考

1. **这个简单明文 RTL IP 的交接路线已实测可行。** 先由 Vivado 生成并审核真实综合源码和依赖，再使用同一份源码仿真和 Procise 原生实现，哈希清单关联各阶段；不能只交 XCI、DCP、stub 或可仿真的模型就认定硬件实现完成。
2. **IP 兼容须逐核、逐配置判断。** 本次 xlconcat 只是组合拼接，综合网表中已无独立 IP 单元引用，不能推广到加密计数器、FIFO/BRAM/Clocking/DSP、DMA、HDMI 或 AXI 系统。后续需核对语法、完整源码、原语、初始化/复位、时序与约束，并按项目规范讨论适配方案。
3. **综合职责要准确记录。** 本次 Vivado 仅生成/仿真，Procise 执行实际综合；资料里的 JFM OOC/EDIF 路线还包含 Vivado 前端综合及 hook，不应与本次混称，也未由此次测试验收 2019.1 的完整 JFM 迁移。
4. **MCP 收益是入口与证据整合。** 本次新工程使用 Procise 原生批处理，首版 Procise MCP 仍固定旧工程，无 JTAG/Flash 能力；扩大工程范围或增加能力仍须讨论批准。Concat 实现的 LC/时序恰与此前同灯序 RTL 相同，不构成 MCP 或 IP 性能提升证据。
5. **保留小型独立试验。** 新工程、真实生成产品、来源清单、自检、原生报告、位流及本次用户确认均独立保存，适合后续 IP 适配方法参考；复杂工程仍需自己的功能与接口验收。

完整结果见 [ip-reuse/RESULTS.md](D:/FPGACompetitionProject/tools/mcp-validation/ip-reuse/RESULTS.md)，资料索引为 `REFERENCES.md` 14.4。根目录 Agents.md 已明确统一采用“工程内容总结＋对后续开发的参考”记录完成的开发/验证。


## 2026-10-01：SD 镜像校验失败的只读核对

### 工程内容总结

目标：针对用户 imageUSB 写入 SD 卡后 MD5/SHA1 校验失败的截图，先排查本地镜像自身完整性，不执行重写、格式化或板端操作。平台为 Windows 10；配套 imageUSB.exe 文件版本为 1.3.1002.0。镜像总长 31,914,983,936 字节，首部为 imageUSB 专用 512 字节头；其后数据长 31,914,983,424 字节，包含 MBR、1 GiB FAT16 分区和 28,000,000,000 字节 Linux 类型分区。

已完成：顺序读取全部镜像数据（跳过 512 字节头），312.28 秒完成 MD5/SHA1 计算，得到 `9AFB0B00F198933AFAE1D90657E924A3` / `0A4A3A1A5736EF8783FE6C2AC5D73213EA1A730B`，与镜像头和截图 Image 值均相符。因此本地镜像的数据与自身内置校验值一致，未证明与另行提供的厂商权威摘要一致。当前 Disk 3 / USB 序列号 121220160204 的两个分区起始和大小与镜像 MBR 相符；直接只读打开 PhysicalDrive3 被 Windows 权限拒绝，未完成卡扇区抽样或全盘读回。用户说明标称 64GB、已失败两次、校验期间未打开 E/F，首次尝试格式化后取消（取消阶段尚未明确）；商品图标示 VDISCO，读卡器型号仍未明确。未确诊卡损坏、假容量、读卡器问题或系统修改数据。

证据：[只读核对记录](D:/FPGACompetitionProject/tools/sd-image-validation/20261001-source-check.json)。没有下载/更新工具、重写/格式化 SD 卡、进行容量写入测试或启动开发板；源镜像未修改。

### 对后续开发的参考

1. imageUSB 格式不能仅凭 .bin 扩展名认定是裸磁盘镜像；本文件需要跳过 512 字节头才能计算数据摘要或作为原始磁盘数据处理。直接交给未识别该头的裸镜像写入工具会导致偏移错误。
2. 镜像数据摘要与头内值相符，可排除当前文件相对其内置校验值的不一致；卡读回失败仍需取得实际差异证据。分区表相符不等于全卡数据相符，控制器报告容量不等于真实容量已验证。
3. 此镜像含 Linux 分区，Windows 的格式化提示不能作为该分区损坏的独立证据；格式化可能改变待验证数据。后续重写、容量测试或工具变更须先讨论确认方案与目标，不能把本次只读排查当作执行授权。

## 2026-10-02：Lite 无串口输出与 SD 启动文件异常的只读定位

### 工程内容总结

目标：对用户插入未开启写后校验的 64GB SD 卡后“COM7 无输出，D18/D19/D20/D21/D8 常亮”进行排查。Windows 10、悟净 Lite、Procise 2025.1.1 temp / SVN 32494；源为既定 imageUSB 格式镜像。已完成 REFERENCES/B1/B4 启动、UART、LED 核对，COM7 CP210x 枚举和 115200/8N1/无流控接收；用户关闭占用会话后成功打开串口，150 秒捕获覆盖现场断电重启，收到 0 字节。原生只读 JTAG 扫链正常、STAT=0x40001f0c；未依据其他厂商位定义解释该寄存器。

按源 FAT16 目录/簇链提取 9 个启动文件的 SHA256，与卡 E: 文件相比仅 FSBL 匹配，8 个不匹配。BOOT.bin 大小均为 7,023,552 字节，3,445,904 字节不同；源首部 fe ff ff ea，卡首部为类似 FAT 目录的 IMAGE 数据。uEnv.txt 1,499 字节中 1,496 字节不同，卡中不是源启动文本。用户安全弹出并重新插拔 USB 读卡器后，独立重新枚举和复读仍为 8/9 不匹配，BOOT 等 7 文件摘要发生变化。用户随后补充教程要求参考 BOOT 替换，已将其指定 Lite 目录 BOOT.bin 作为额外比较目标：源 SHA256=ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef，卡 SHA256=6ec99ec782642a5053178fdd2e6f696f69a030724ae866dcd91516ced84d238b，2,254,275字节不同且卡当前首64字节全零。不能仅用 BOOT 与原镜像不同作为异常证据；其与指定参考也不同、启动头无效及其他文件异常为修正后的依据，见 reference-boot-comparison.json。用户确认没有备用读卡器，且在本次插卡启动之前已经执行指定参考 BOOT 替换。此结果确认当前启动介质内容异常、无法作为有效 SD 启动镜像使用，是已定位的启动阻断项；卡、读卡器、写入流程或文件系统异常的底层归因尚未完成，尚未验证修复后启动，未宣称板卡损坏或假容量。

证据：[诊断报告](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/RESULTS.md)、[串口/JTAG 记录](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/diagnostic-status.json)、[源文件摘要](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/source-boot-manifest.json)、[逐字节比较](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/boot-byte-comparison.json)、[拔插后复读](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/card-after-replug.json)。PhysicalDrive3 只读打开仍被权限拒绝，未进行全盘扇区或真实容量验证。本次未主动改写卡文件、格式化、更新工具/永久配置、重置 PS、下载 FPGA 或写 Flash/BOOT；Windows 挂载访问可能更新文件系统元数据，不将跨挂载摘要变化单独等同于随机读错误。

### 对后续开发的参考

1. 写入完成且跳过校验的提示不能当作启动介质验收；文件名/大小及分区表正确也不能替代启动文件内容摘要比对。此卡已具体复现 BOOT 头无效，优先解决介质问题后再核验剩余启动/串口问题。
2. 从 imageUSB 镜像中跳过 512 字节头、按真实 FAT16 簇链计算源文件摘要，可用普通文件访问权限检查关键启动文件，不需要全盘原始访问；不能据文件级比对宣布 Linux 根分区或全卡容量正常。
3. 独占串口、先接收再由用户冷启动、保存原始字节和时间日志，可排除终端占用和打开太晚，但零字节不能独立证明 UART 硬件损坏。
4. 更换读卡器只读比对、后续完整容量检测或重制均需区分目的与范围；本次诊断许可不扩展为覆盖写卡、格式化或板端修复批准。不同读卡器归因与成功启动仍待验证。



### 用户重制后的复核补充（2026-10-02 16:45）

用户重新制作后仍未进行写后校验，并明确本次尚未替换参考 BOOT；因此以原镜像全部文件为预期。相同读卡器/卡的两分区布局仍匹配，普通文件摘要仍8/9不匹配。用户不在电脑旁，本次USB拔插未完成；补充 Win32 FILE_FLAG_NO_BUFFERING 只读文件数据复核，使用本地参考uEnv控制文件确认方法摘要正确，再读9个卡文件仍仅FSBL匹配。BOOT.bin全部7,023,552字节和设备树全部15,996字节均为零，uEnv为非正常文本；卡/读卡器/写入链路异常仍成立，底层归因未完成。

证据：[本次复核报告](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/remade_20261002_164505/RESULTS.md)、[无缓存读取](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/remade_20261002_164505/unbuffered-file-comparison.json)。NO_BUFFERING只绕过Windows文件数据缓存，未绕过文件系统元数据/硬件缓存；普通与无缓存内容不同时须分别记录，不直接认定随机硬件错误。未进行全盘、Linux根分区、真实容量或上板验收；没有改写SD/BOOT、格式化或板端操作。本次验证结果为不通过，不将重制写入完成提示当作验收。

### 更换绿联读卡器后的复核补充（2026-10-02 19:17）

用户更换读卡器并重新制作，确认依然跳过校验且本次尚未替换参考BOOT。实际USB序列号000000000819、Generic STORAGE DEVICE USB Device，与旧设备不同；卡容量报告和两分区布局仍匹配。完成普通及无缓存文件读取、用户USB安全弹出/重插后的重新枚举和复读；仍仅FSBL匹配、其余8个不匹配。初读无缓存BOOT/DTB等全零；重插后BOOT不再整份全零，但首64字节仍全零、摘要c1969b87c628b890b871f7dcf77dcc746df5e48526d68f79e37398732b314c33且不匹配，DTB/uEnv头也异常。源镜像四个关键文件重新读取均与既有摘要相符。当前读卡器变化没有解决问题，不能仅归因旧读卡器；卡/软件/写入链路具体归因、全容量及实板启动仍待验证。

证据：[新读卡器复核报告](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/new_reader_20261002_191749/RESULTS.md)、[重插后无缓存读取](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/new_reader_20261002_191749/unbuffered-file-comparison.json)、[源关键文件重新核对](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/new_reader_20261002_191749/fresh-source-check.json)。本次未改写SD/BOOT、格式化、全容量写入测试或板端操作。既有MEDIA-TEST-PLAN.md已更新新读卡器身份，仅作为待批准方案，未执行。制作应恢复写后校验；不能用品牌/报告容量或写入成功提示替代数据验证。

### 用户H2testw结果分析补充（2026-10-02）

用户自行运行H2testw并提交文本/截图：E:当前约1GiB FAT分区，测试可用950MiB，115MiB正确、835MiB丢失/错误（约87.9%），报告12.4MiB覆盖、822.5MiB损坏及2.9MiB地址别名，首错测试数据偏移0x07300000=115MiB。本次是局部分区可用空间测试，不是清卡后全64GB测试，115MiB正确也不证明真实物理容量。结合更换读卡器后系统文件异常，确认当前存储链路写读严重不一致，优先怀疑卡本身质量/控制器/容量异常，未单独确诊假容量或精确故障部件。

证据：[用户测试及分析](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/user_h2testw_20261002_193901/RESULTS.md)、[原文与结构化记录](D:/FPGACompetitionProject/tools/boot-diagnostics/20261002/user_h2testw_20261002_193901/interpretation.json)。测试由用户执行，代理只读枚举当前新读卡器、保存证据与分析，没有格式化/写测试/重烧/板端操作。局部严重失败已足以拒绝当前介质可靠性；退换卡和其他设备交叉测试是建议，未写为已完成成果。

## 2026-10-02：更换 SD 卡后基本启动通过及项目状态同步

### 工程内容总结

目标：同步用户最新现场进度，更新当前 SD 启动状态并区分旧卡历史故障。平台/工具基线为悟净开发板 Lite、既定 icraft_v3_ubuntu20.04_aarch64_sd_image.bin 镜像；开发工具继续沿用 Procise 2025.1.1 temp 和 Icraft 3.39.0，本次没有调用 EDA/Icraft 或核验板端软件版本。

用户明确报告：已更换 SD 卡、完成 SD 启动卡制作和上板验证，串口正常输出信息，能够登录进系统。上述基本启动/串口登录由用户现场确认通过；代理本轮已同步 Agents.md、REFERENCES.md 第 15 节、旧卡诊断报告顶部说明及本条记录。证据来源为当前聊天用户陈述，已保存为 [新卡现场确认记录](D:/FPGACompetitionProject/tools/sd-image-validation/20261002-new-card-board-confirmation.json)，未伪造串口日志或磁盘测量。

旧卡异常与 H2testw 失败证据保留，不能套用于新卡；旧卡精确故障仍未确诊。新卡实际分区/文件系统、全容量、启动组件哈希和板端 runtime 未独立核验；AI/模型功能未由本次基本启动覆盖。

扩容状态：用户选择扩大系统分区，要求代理仅提供具体命令与逐条说明，由用户实际执行；随后确认在悟净 Lite 已启动的板载 Ubuntu 中通过串口执行。当前尚未扩容/验收，实际设备名、文件系统和工具可用性待核对，不把命令方案写成完成成果。代理本轮只编辑项目说明，没有修改 SD 分区、安装板端软件或执行设备命令。

### 对后续开发的参考

1. 后续基本 Linux 使用可从用户已确认可登录的板载系统开展，不再因旧卡记录将新卡基本启动视为未通过；调用设备、安装/部署或更改配置仍按当前任务授权范围处理。
2. 用户现场确认与代理直接测试分别记录；成功登录证明基本启动和串口登录路径可用，不替代 runtime、AI、模型、全容量及扩容验收。
3. 扩容应先核对实际根设备、文件系统、分区起始/末尾和连续未分配空间，再区分扩大分区与扩大文件系统。板端在线流程与本机离线流程不能混用；用户执行后的输出和重启结果另行补全。

### 板端查询结果补充（2026-10-03）

用户通过串口执行既定四条只读查询并提交截图，已确认根设备 /dev/mmcblk0p2，ext4，挂载选项 rw,relatime；mmcblk0=58.3G，p1=1G，p2=26.1G。df 根文件系统26G、已用6.3G、可用18G、使用率26%。现有 /usr/sbin/resize2fs、/usr/sbin/sfdisk，未找到 growpart。上述为用户提供的命令输出证据，更新 REFERENCES.md 15.1 和 [结构化记录](D:/FPGACompetitionProject/tools/sd-image-validation/20261002-new-card-board-confirmation.json)，截图保存为 [板端查询截图](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-board-preflight.png)。

分区表具体扇区布局和 sfdisk 版本仍待核对；扩容尚未执行/验收。代理本轮只核对用户输出、查询官方手册并补全文档，没有连接串口、安装软件或改写分区。后续可复用 findmnt 的实际根设备定位与 df 的文件系统容量对照；不能仅凭卡的 lsblk 总容量推定根文件系统已扩容，也不对正在挂载的根分区执行离线 fsck。

用户随后补充 [实际分区表截图](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-partition-table.png)，更新上述待核对状态：sfdisk 2.34、DOS/MBR、ID 0x370deffb、总122167296个512字节扇区；p1 start/size/type=2048/2097152/e，p2=2101248/54687500/83（末扇区56788747）。已完成布局与长度计算核对，形成 [用户执行命令及逐条说明](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-expand-root-COMMANDS.md)，目标p2 size=120066048、end=122167295、约57.25GiB，REFERENCES.md 15.2及结构化记录已同步。分区表备份、预演、正式写入、重启读取边界及resize2fs均为待用户执行步骤，不写为板端完成。后续复用须重新取得实际磁盘扇区和分区边界；只扩大末尾、保留起始及类型，并区分卡上的分区表与内核已加载边界。

### 系统分区扩容验收补充（2026-10-03，更新上述待执行状态）

#### 工程内容总结

目标：利用新SD卡尾部连续未分配空间，扩大悟净Lite板载Ubuntu的第二分区及ext4根文件系统。平台为既定icraft_v3_ubuntu20.04_aarch64_sd_image.bin启动系统，实际根设备/dev/mmcblk0p2；分区工具sfdisk（util-linux 2.34），文件系统工具resize2fs 1.45.5（07-Jan-2020）。操作由用户通过串口以root执行，代理提供逐条命令、核对截图并记录结果；未使用Procise/Icraft执行本次扩容。

用户明确确认“已经成功完成扩容”，并提交 [扩容成功串口截图](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-expansion-success.png)。截图直接支持的结果如下：

- 登录后的`cat /sys/class/block/mmcblk0p2/size`返回120066048，与本卡目标分区长度一致。
- `findmnt -no SOURCE,FSTYPE,OPTIONS /`返回`/dev/mmcblk0p2 ext4 rw,relatime`，根分区仍正确挂载且可写。
- `resize2fs /dev/mmcblk0p2`实际执行已挂载根文件系统的在线扩容，报告`old_desc_blocks = 2, new_desc_blocks = 4`，随后确认文件系统现为15008256个4KiB块。
- 文件系统总字节数15008256×4096=61473816576，与分区长度120066048×512一致，即约57.25GiB，文件系统已覆盖扩大后的分区。
- 用户执行`sync`后，`lsblk`显示mmcblk0约58.3G、p1约1G、p2约57.3G且挂载到/；`df -hT /`显示ext4总容量57G、已用6.3G、可用48G、使用率12%。扩容前对应为26G、已用6.3G、可用18G、使用率26%。

验收结论：用户执行并以现场截图确认本次SD第二分区和ext4根文件系统扩容通过；本次实际板端内核支持该根文件系统的在线扩容。截图记录了登录后的长度核对、在线resize和最终容量，预演、分区表备份及正式写表退出码未包含在本张截图中，不将其写成代理独立采集验证。没有全容量写读测试、扩容后额外重启或长期稳定性证据；不将此次通过扩大为AI/模型、runtime兼容性或其他板卡/镜像的验收。

证据入口：[扩容前查询截图](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-board-preflight.png)、[原始分区表截图](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-partition-table.png)、[本次具体命令](D:/FPGACompetitionProject/tools/sd-image-validation/20261003-expand-root-COMMANDS.md)、[新卡及扩容结构化记录](D:/FPGACompetitionProject/tools/sd-image-validation/20261002-new-card-board-confirmation.json)。本补充更新同一工作此前的“扩容待执行/验收”状态，保留准备阶段和旧卡历史记录。

#### 对后续开发的参考

1. 可复用流程为：确认实际根设备/ext4和连续尾部空闲空间→备份/预演→只扩大第二分区长度、保留起始→正常重启加载分区边界→核对内核长度→resize2fs在线扩大文件系统→lsblk/df验收。分区扩大与文件系统扩大必须分别验证。
2. 120066048等扇区数仅适用于本次已核对的SD卡及分区布局；换卡或镜像重新制作后重新查询和计算，不直接复制本次固定长度。
3. 当前根目录可用空间约48G，可供后续板端文件和软件使用；容量扩展不提升PS DDR内存容量、NPU算力或SD写读速度。重刷原始镜像可能恢复原小分区布局，之后需重新核对是否扩容。
4. 成果来源应继续区分用户执行/现场截图与代理直接操作；在线扩容的实测适用条件是本次内核和ext4配置，不对正在挂载的根分区执行离线e2fsck。

## 2026-10-03：Lite SSH通信、板端Icraft/CustomOp安装及FPAI容器进度同步

### 工程内容总结

**目标与完成内容**：同步用户最新开发环境，核对资料并更新后续执行上下文。平台为悟净Lite、既定SD启动Ubuntu系统、Windows10主机；主机Procise/Icraft继续采用既有版本。用户已完成以下操作：

1. 使用SD卡启动悟净开发板，网线连接主机，在MobaXterm中通过SSH进行开发和通信。
2. 将 [指定30TAI&100TAI目录](<D:/Dowload from Chrome/嵌赛资料/Icraft/Icraft_V3.39.0安装包/30TAI&100TAI/30TAI&100TAI>) 中的板端Icraft开发工具传输到板上并完成安装；随后明确确认CustomOp板端包也已安装。
3. 在本机搭建Docker交叉编译环境、配置相关工具链；随后明确确认 **FPAI是容器名**。

上述环境准备和SSH使用状态由用户确认，代理没有执行或独立重测。代理本轮先查REFERENCES.md E1及原始自述文件，只读解析本地四份deb的control：Icraft/CustomOp的onchip包均为3.39.0、arm64，amd64包均为3.39.0、amd64。已更新Agents.md、REFERENCES.md基线及第16节，保存 [进度与用户澄清](D:/FPGACompetitionProject/tools/development-environment/20261003-progress.json) 和 [本地安装包元数据](D:/FPGACompetitionProject/tools/development-environment/20261003-package-control.json)。

**验收范围**：环境搭建/安装完成按用户报告记录；本地包架构/版本来自代理只读核对。尚无板端实际包版本/安装路径、容器镜像与编译器/sysroot版本、“交叉编译→板端运行”或AI模型推理的独立测试输出，不将其写为已通过。代理本轮没有连接SSH、操作Docker、安装软件、编译、部署、下载FPGA或修改板端配置；此前SD扩容结果保持。

### 对后续开发的参考

1. 当前可从用户已确认可用的板载Ubuntu/SSH通道和已安装工具继续讨论板端开发，MobaXterm提供实际终端/通信入口；SSH地址、账号与板端路径需使用用户提供或后续核验的值。
2. 本地onchip包是arm64板端角色，amd64包按资料用于主机侧交叉编译；后续容器和板端分别核对实际版本/库，不能以安装包目录存在替代安装状态，也不能把FPAI容器名当成镜像来源。
3. 环境配置完成与编译产物可运行是不同证据。后续具体验证宜关联工具链/依赖、目标架构、传输产物和板端运行输出；具体操作方案仍依项目规范先讨论批准。
4. 保持环境对象清晰：Windows执行既有Procise/Icraft任务；本机FPAI容器承担用户配置的交叉编译；Lite运行板端程序；远程Ubuntu服务器仍承担此前说明的算法训练。板端SSH不能推定训练服务器SSH已验证，koala仍与比赛无关。

资料索引见 [REFERENCES.md第16节](D:/FPGACompetitionProject/REFERENCES.md)，本次没有选择新的参考位流、模型、接口或技术路线。

## 2026-10-03：2026姿态模型迁移实现、门检与10轮训练启动

### 工程内容总结

目标：落实用户批准的26版pose-only迁移方案，解决旧26版分化/细化参数趋近零及精度不佳的问题，并开展首轮10轮对照实验。平台为远程Ubuntu `gpu-server`、`PersonInWIFI` Python环境、PyTorch1.13.1+cu117/MMCV1.5.3/MMDetection2.25.0，四张RTX A5500（GPU1–4）；本次不涉及FPGA/Icraft部署。

已完成独立注册类、配置、迁移/优化器/诊断、门检、启动和最终汇总脚本，项目副本见[实现说明](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/README.md)，服务器新增文件位于`opera/models`、`configs/wifi`和`tools/pose26_transfer`；旧代码、权重、结果均保留。已从24版epoch442迁移169个张量，重新初始化STE、14个独立残差分化分支、三层vanilla refine及优化器；分化Linear权重和偏置N(0,0.001²)，整个refine正常初始化，坐标回归末层为零。只保留14关节姿态，不引入mesh/SMPL。

已验收：迁移逐元素一致；关闭STE后粗输出误差0；人物/关节和置信度排序索引；细化损失可反传至分化及姿态分支；4卡每卡8的短程3步、恢复到6步及参数范数一致。24版全7824帧同口径复评**123.085352129mm**。首次索引门检测试值导致sigmoid饱和并列，已修正测试数据并保留失败证据，未修改网络排序。证据见[单项门检](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/evidence/gates/unit_gate.json)、[四卡门检](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/evidence/gates/ddp_gate.json)、[基准复评](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/evidence/baseline/evaluations.jsonl)、[启动审计](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/evidence/prelaunch-audit.json)。论文对应及未公开细节见[PAPER_AUDIT.md](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/PAPER_AUDIT.md)。

正式10轮于21:59启动，尚未完成/验收精度。配置为AdamW迁移lr2e-6/新增lr2e-5、矩阵wd1e-4并排除指定参数、clip0.1、分类/坐标2/70、FP32、seed0、四卡每卡batch8/worker4、固定学习率10轮。结果目录`Z:\Person-in-WiFi-3D-repo\result\tpami2026_transfer_20261003`，实时查`pipeline-status.json`、`train.stdout.log`、`branch_diagnostics.jsonl`；每轮评估见`evaluations.jsonl`。流水线设置为第10轮后汇总并停止，失败则停止，不自动重试/延长。当前“完成”范围限于实现、门检、基准复评和启动，不能提前宣称优于123.09mm。

### 对后续开发的参考

- 迁移需同时核对张量哈希/映射、实际导入入口、解析配置和前向等价性；服务器`source_snapshot`保存源码/配置/数据列表。四卡短程和正式训练输出隔离，不把门检优化器状态带入实验。
- 零初始化坐标末层使初次反传的新分支梯度为零属于预期；一次更新打开回归头后，使用仅细化损失检查连通性。保持注意力正常初始化，仅分化MLP近零，避免误将整个refine缩小。
- 参数范数、裁剪前后梯度、查询差异、同配对细化前后误差能帮助区分优化器衰减、梯度过小和分支无效；数值健康不能代替泛化精度评估。
- 原指标依赖GT匹配全部100候选，不能作为最终部署人数选择的验收。当前10轮是迁移修正有效性实验，不等同论文完整从零复现；结束后先讨论再决定后续训练。

### 首轮实际评估（2026-10-03 22:10快照）

第1/10轮完成，四卡一致性、全7824帧评估及`best_mpjpe_epoch_1.pth`保存通过，训练已进入第2轮。MPJPE **126.41057mm**，高于24版基准123.08535mm约3.32522mm；固定最终匹配的粗/细化1/2/3分别126.06887/126.24047/126.33473/126.41057mm，首轮细化尚无收益。单/双/三人104.90486/126.34861/153.58244mm。分化/细化注意力L2分别1.357471858/92.75375147，未观察到旧实验的参数趋零。当前记录不是最终10轮结论，不自行调整参数或延长实验；首次best仅表示本实验已完成轮次中的最佳，不代表超过24版。

项目证据副本：`tools/pose26-transfer/20261003/evidence/evaluations.jsonl`、`epoch_parameter_checks.jsonl`、`branch_diagnostics.jsonl`。这些为采集时快照，实时结果以服务器目录为准。

### 10轮结束及结果验收补充（2026-10-03 23:52，更新前述进行中状态）

#### 工程内容总结

正式10轮、28,110步已于23:42完成并停止，训练/监督进程均退出。最佳第9轮122.873803893mm，24版基准123.085352129mm，降低0.211548236mm（约0.172%）；最终第10轮124.680599441mm。10轮7824帧评估、10次四卡一致性、563条有限诊断、126份当前源码/快照哈希、配置哈希、指标CSV、最佳/最终权重哈希与元数据均独立核验通过，曲线可视检查通过。

单/双/三人最佳为100.32099/123.27283/150.64941mm，对照99.66472/123.11501/152.52611mm；单/双略退步、三人降低1.87670mm。第9轮同配对粗预测122.79552→最终细化122.87380mm，细化增加约0.0783mm。逐关节完整表、配置与命令、曲线和产物入口见[最终结果](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/RESULTS.md)。最佳权重已复制至[本地保留目录](D:/FPGACompetitionProject/.local/pose26-training/20261003/best_mpjpe_epoch_9.pth)，SHA256 b567aa16e3e46be88cd9187cdc3af7d46085800d0c3df94a8404ae377d8bcca7，与服务器一致；最终epoch10仍保留服务器。

#### 对后续开发的参考

本轮未再现旧参数趋零，分化/细化注意力L2保持约1.358/92.757，梯度通路健康。但细化只有4/10轮改善误差，整体最佳改善仅0.212mm、单seed且波动明显，不能将此认定为稳定提升或分化分支贡献。当前只完成训练/结果核验，未进行消融、延长、ONNX/Icraft部署；下一步先讨论现有诊断、粗预测与STE影响及细化收益，获得明确同意后才执行新方案。旧基准和所有结果保留。

### 26版实验定时结果检查（2026-10-03）

#### 工程内容总结

用户确认每10分钟检查一次当前10轮训练，在正常运行时保持安静，完成/失败/异常或需处理时通知，结果核验及记录完成后停止。已用Codex应用工具创建当前聊天heartbeat“检查26版姿态迁移训练结果”（ID26、ACTIVE），并读回配置确认间隔、目标聊天和检查范围；不改变训练设置。任务包括检查结果/哈希/曲线、补全项目记录及完成后停用本项。证据说明见[MONITOR.md](D:/FPGACompetitionProject/tools/pose26-transfer/20261003/MONITOR.md)。首次定时检查已于22:27成功读取状态、评估及全部已记录诊断：第3轮进行中，已完成两轮评估，记录均有限、四卡检查通过，未发现需通知的异常；证据见同目录monitor-state.json。该检查不等于最终训练结果验收。

#### 对后续开发的参考

定时检查附着当前聊天并复用已授权训练上下文；它不重新启动训练。结果优先通过Z盘读取，网络/挂载不可用与任务失败分开判断。主机和应用需运行，后续停用仅针对ID26，不归档聊天，不更改其他自动化。固定10轮和重大变更先讨论的约束仍保持。

最终状态补充（2026-10-03）：10轮训练与结果核验、记录及通知完成后，已通过应用工具将ID26停用，并读回确认PAUSED。停止证据为`tools/pose26-transfer/20261003/evidence/automation-stop.json`；未延长或重启训练，未归档聊天或更改其他自动化。上文ACTIVE及首次检查均为历史状态。

## 2026-10-04：26版全新初始化、论文Adam配方500轮训练启动

### 工程内容总结

用户明确将后续训练改为从头500epoch，并确认选择论文Adam配方A。已在同一远程Ubuntu/PersonInWIFI环境（PyTorch1.13.1+cu117、MMCV1.5.3、MMDetection2.25.0）部署新隔离模块、配置、门检和启动/汇总脚本；00:41:21（北京时间）启动四张RTX A5500 GPU1–4正式训练。旧代码/配置、24版及10轮权重和结果未改；此前恢复第10轮到100轮的建议未执行。

新模型明确绕过迁移加载，模型与优化器全新初始化；保留STE、14独立残差分化分支、三层vanilla refine，分化Linear权重/偏置N(0,0.001²)，整个细化器正常初始化、坐标末层为零。仅14关节pose，不包含mesh/SMPL。Adam统一lr2e-5、betas(0.9,0.999)、eps1e-8、wd1e-4，无迁移分组/衰减排除；总batch32（每卡8/worker4）、FP32 seed0、clip0.1；500轮，MMCV step450/gamma0.1。论文第7页训练细节已可视核对，未公开细节与当前损失整体缩放/辅助监督明确列为实现选择。

已验收：禁止checkpoint读取的全新初始化；三层8头256维普通注意力；人物/关节及置信度索引；细化梯度通路；450轮学习率边界；4卡96样本3步参数一致和checkpoint有限；129份源码/配置/列表当前与source_snapshot及解析配置哈希；监督/torchrun和四个rank身份、GPU1–4实际负载与正式日志超过500步。短程更新未用于正式模型。入口和证据见[README](D:/FPGACompetitionProject/tools/pose26-scratch/20261004/README.md)、同目录evidence/gates及[startup-verification.json](D:/FPGACompetitionProject/tools/pose26-scratch/20261004/evidence/startup-verification.json)。

当前结果目录`result/tpami2026_scratch_20261004`，实时查pipeline-status.json、train.stdout.log和诊断/评估JSONL。当前完成的是实现、门检和启动，**500轮训练及精度尚未完成/验收**。用户明确选择暂不启用定时监测，旧ID26保持PAUSED，未更改自动化。训练内置异常停止门禁保留，不自动重试、改AdamW/参数或延长500轮。

启动后快照补充：第1轮2811训练步已完成，四卡一致性通过，首轮评估尚待核验。首轮末分化L2=0.003813、细化注意力L2=51.173392，数值有限、没有触发既有严重趋零门禁，但与初始化相比下降较快。证据`tools/pose26-scratch/20261004/evidence/first-epoch-training.json`；下文第501步数据为此前快照。

### 对后续开发的参考

- 从头训练不能只把resume_from设为None：旧模型init_weights内部仍会迁移24版。本次用独立注册类绕过migrate，并在单项门检禁止torch.load，正式hook再次确认优化器为空、epoch/iter=0；以后需检查实际加载路径。
- Adam耦合L2衰减与上一轮AdamW不同。第501步分化L2已从1.357186降到0.016044，仍有限且梯度非零，但快速缩小值得关注。旧退化尚未唯一确诊，不能静默改变用户明确选择的Adam配方或宣称长程风险已排除。
- 保留每轮全7824帧MPJPE、人数/逐关节及同匹配粗/细化误差，以及分支参数/梯度和四卡检查；原GT辅助100候选指标不是实部署人数检测验收。损失下降不等于精度或分化收益。
- 已记录无自动回查的状态；后续由用户请求查询或重新授权监测。正式训练结束后还需核对500轮评估/产物/哈希与最终进程状态，再按同一模板补全结果。当前未开展ONNX/Icraft/NPU/FPGA部署。

### 异常停止及当前结果核验补充（2026-10-04 09:08）

#### 工程内容总结

用户要求检查服务器训练日志，本次通过SSH只读取证（Z盘不可用）。训练实际上已于01:40:51在第6轮末触发`RuntimeError: Persistent branch collapse`自动停止；stage=failed_stopped，监督、torchrun及四个rank均退出，GPU1–4空闲。仅5轮完整7824帧评估，第6轮停止前完成训练步但未进行评估；500轮未完成，无final-report，不能记为训练完成。

5轮MPJPE依次479.294219、453.726498、439.551332、420.189946、438.772184mm；最佳第4轮420.189946mm，较已训练24版基准123.085352mm高297.104594mm。最佳单/双/三人406.525056/385.294528/491.487131mm；同匹配粗预测420.366988→最终细化420.189946mm，改善约0.177042mm。最佳checkpoint epoch4/iter11244、311125343字节、全部权重有限，SHA256 eaec533377d8098dab8fa35e6104c5330840fc7d0be0658ffdc669a794213361；129份源码/配置/列表及快照、解析配置哈希核对通过，最佳文件保留服务器。

退化证据：分化L2从初始化1.357186降至第4轮6.32e-8、第5轮7.30e-21，第6轮16851步抽检7.44e-38。最新分化/细化注意力裁剪前后梯度及分化残差RMS为0；细化注意力参数仍约32.17。338条诊断均有限，连续两轮严重分化趋零触发停止；第6轮末异常发生在参数检查JSONL/评估记录前，因此这些文件仅1–5轮。详细人数、14关节、阶段对照见[结果报告](D:/FPGACompetitionProject/tools/pose26-scratch/20261004/STATUS-20261004-0908.md)，原始状态/日志/评估/诊断与核验见同目录evidence/check-20261004-0906。

#### 对后续开发的参考

短程初始化/梯度/DDP门检通过仍不足以保证长程分支有效；损失下降和诊断有限也不能排除退化。本轮日志确认分化及细化学习通路逐步衰退，但尚未唯一证明Adam全局耦合L2/梯度裁剪等的因果，需先讨论隔离对照再执行。第5轮前的从零结果不能代表完整500轮性能或模型架构上限。当前已保存证据、更新记录，未改参数、恢复/重启训练或启用定时监测；后续修复/实验仍须先取得明确批准。

## 2026-10-04：首版启动配套审计与PS CSI预处理独立验证（阶段成果）

本项初始9用例与阻断描述为历史阶段；最新300份门检及运行身份核验结果补充于本项末尾。

### 工程内容总结

用户批准原始CSI回放→PS预处理→PS/NPU混合推理→单人骨架→HDMI＋RTSP首版，明确正式验收须NPU与双路通过。
本阶段新增[软件模块](software/pose_v1/README.md)、[实施工具](tools/pose-v1/README.md)和用户要求的`Logs`目录。
已实现C++17预处理、原始窗口格式和回放发送端、启动分区只读审计、可复现交叉构建、模型/源码哈希与数值检查；
未实现完整板端服务、混合推理或显示链路，不能记为首版完成。

FPAI实测为运行中的`ubuntu20.04:custom`容器，已有arm64 Icraft/CustomOp3.39.0与GCC9.4交叉工具链。
源码明确从当前worktree复制至容器临时目录，未改原项目挂载或工具链。用户另行授权Conda独立验证环境，
Python3.10.21、NumPy2.2.5、h5py3.16.0、PyWavelets1.8.0；在线安装遇TLS中断，随后缓存离线完成，不改证书或既有环境。

板端直接只读解析FAT16启动分区，9文件与源镜像大小/哈希均一致。但uEnv引用第二分区download.bit，前次根目录未找到，
运行AI_MATE版本、AI/HDMI接口映射仍未确认，按批准方案暂停相关设备访问，等待完整串口日志；未挂载、改BOOT/位流或访问未知寄存器。

定位并修正零幅值复数乘法带符号零的移植差异，原算法和模型未改。修正后9类输入在主机与真实Lite运行：
3份测试集CSI `S11_01_308/309/310`及常量/全零/随机样本的float32张量逐位一致；真实样本单次预处理
5.70319/5.78065/5.72649ms；非法魔数、截断、尾随记录、NaN输入均拒绝。
0.75rad斜坡最大差7.5051e-14，±π边界合成样本仍有最高6.24063差异，未忽略失败或自行放宽容限，总体门检未通过。
实板二进制SHA256 `65d44aa2aff5ffe2975300b27b1325dc7b25d5cb71cd6f85ee5076b4aa4a59b2`，新构建脚本复现同一哈希。

原始回放发送端另通过Windows本机TCP回环测试，强制碎片读取，3个真实窗口的原始I/Q及帧号字节不变；
只证明发送端契约，不代表板端收包或推理联调。π边界的标量angle替换离线诊断未解释差异，负结果同样保留。

完整证据和未完成项见[阶段状态](tools/pose-v1/STATUS.md)、同目录evidence；尚未执行模型推理、HDMI、编码RTSP或30分钟闭环。

### 对后续开发的参考

预处理须保留训练计算顺序、复数带符号零和token布局；将复杂运算简化为表面等价公式可能改变零幅值相位。
Python训练方法可通过AST隔离作参考，不必安装mmdet或调用GPU；当前参考依赖版本明确记录，但不代表训练服务器环境已重验。
一般样本一致不能覆盖π展开边界，需要继续定位并讨论处理策略；不能将大差异归为普通舍入。
交叉编译可用临时目录和二进制哈希核对，防止误用FPAI挂载的旧源码。
约5.7ms只覆盖预处理，不能推出NPU/双路端到端5Hz或500ms通过；启动文件一致也不能替代实际加载日志与接口确认。

### 工程内容总结（后续补充：300份门检与25122301运行身份）

用户批准固定9组300份真实CSI回放、幅度atol/rtol=1e-6、相位周期最大1e-5 rad门检，并将人工±π保留为非阻断诊断。
主机及真实Lite分别与Windows参考300/300逐位一致，实板/主机输出哈希全相同；幅度、相位标量及周期最大差都为0，
4类非法记录全部拒绝。人工±π周期最大2.333111/2.693437 rad仍失败，保留诊断，不修改原算法或模型。
实板预处理min/median/P95/max=5.64996/5.781265/5.8595/5.89993ms，非收包/推理/显示性能。
工具环境保持独立Conda参考及FPAI/GCC9.4，ARM二进制及原模型/生产源码哈希核验未变；3项数值策略测试通过。

新的板端只读审计确认用户换入BOOT与Lite 25122301包SHA256相同，仅BOOT改变，其他8文件保持旧身份。
FSBL日志确认下载PL，BOOT分区经32位字节序转换与同包.bit完整载荷对应，额外4字节尾随另行记录。
用户随后单独批准最小只读探测，回读0x4000001C=0x25122301，运行版本身份通过；没有改启动配置、SDK初始化、模型或视频操作。
板端Icraft/CustomOp查询为arm64 3.39.0；参考软件包标3.36.0，混合推理兼容性仍待核验。
HDMI参考默认1080p60且缓存包装器不配置720p时序，用户屏幕尚未连接，未进行HDMI/NPU/VPU/RTSP/30分钟闭环验收。
ADR_00第12节、Agents.md、REFERENCES.md 18.4及阶段说明已更新，旧证据保留。
全部结果、固定清单、包/程序哈希及后续条件见[RESULTS-300.md](tools/pose-v1/RESULTS-300.md)和同目录evidence。

### 对后续开发的参考（后续补充）

真实回放门检通过可解除当前预处理阻断，但不能覆盖任意人工边界或将来采集设备的数据分布。
周期误差适合相位比较，模型仍接收标量相位，须保留原始张量绝对差；真实标量大差仍先讨论。
位流身份核验可结合SD哈希、BOOT解码载荷、启动日志及运行版本，避免把uEnv二次加载失败误解为FSBL完全未加载。
SDK初始化可能包含设备设置，包/运行版本相符也不能替代六个Host算子与NPU实测；720p显示还需要实际时序和实屏证据。
本阶段完成的是门检和身份取证，完整首版仍未完成。

## 2026-10-04：首版架构决策 ADR_00 归档

### 工程内容总结

用户审查并明确批准全文后，新建根目录`ADR`及[ADR_00.md](ADR/ADR_00.md)，记录PS主导的原始CSI回放、PS/NPU混合推理、单人骨架与HDMI/RTSP双路输出方案。正文按已批准审查稿归档，仅将文档状态从待审查改为已批准归档，包含范围、数据契约、工具分工、验收目标、取舍和当前状态快照。REFERENCES.md第18节已增加入口，文档关联资料均可在当前项目中解析。此次仅作架构文档归档，未操作板卡、执行模型、处理阻断项或宣称完整首版通过。

### 对后续开发的参考

ADR_00作为首版架构决策基线，详细协议与执行证据仍由对应软件文档和阶段报告维护。后续讨论应区分已批准的架构目标与尚未通过的功能验收；位流配套、π边界、误差容限和扩大功能范围仍按既有审批规则处理。
