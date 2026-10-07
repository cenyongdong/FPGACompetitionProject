# 项目执行规范

- 独立RTSP首批完成（2026-10-07）：用户已审查动态骨架并要求继续。厂商live5552024.11.28/配套SSL头库复用，无新安装；程序454d21c24831f88a513747710540294914b6e2d4fddc8ed2993420bc28758fb2，r1缺头路径失败保留。首客户端未保活，10秒回收后88正确帧超时；仅补3秒GET_PARAMETER，新r3两会话各100帧、实际参数集/IDR加入/TEARDOWN/重连/NAL逐位/9000 ticks通过，200解码像素逐位r5。r4 OpenCV/FFmpeg直接RTSP另100帧通过。两60秒上下文exit0/dmesg同/BOOT与SDK保持/source及端口归还；stderr两/一行已证厂商RTCP诊断保持不为空。SPS实际video_signal_type_present_flag=0，显式色彩待处理。当前仅owned预生成码流，未在线VPU/NPU合并、整机/长期或HDMI；源码固定single-slice合同非通用AU。结果RTSP-RESULTS-20261007.md、evidence/rtsp-20261007-r3及r4-player/completion-review.json；新next-checkpoint当前入口，F0-INTEGRATION-PREP给已批准接续门检，不再索要阶段执行授权。原VPU/Engine数学/SDK/BOOT/帧协议保持，先真实三帧＋重复有限合并再网络/实时AU，HDMI配套未明不写。服务/SSH/SFTP关闭，无后台/自动化。

- 视频恢复与V2-A完成（2026-10-07）：用户恢复后r2保存MMU PC0x1888/FADDR0x20600000及完整cookie/所有权/Host复制证据；r3/r4单CAPTURE色彩拒绝未采用，r3错误接续encode也在REQ/STREAM前停止，历史保留。r5仅保留QUERYBUF opaque cookie用于QBUF，原MPLANE/格式/容量/复制/controls保持。新程序01965fa28f15b94893eebc8a3f540699454ef0623664cb0888b6b7933aef23d3，协商和独立两次各54提交归还/LAST通过，两179648字节H264逐位一致；主机54ID/27来源/756关节可见性通过，exit0/stderr空/dmesg同/BOOT及SDK保持。当前有限文件兼容修正有实测支持，不泛称所有驱动要求或页表内部根因；不是实时/RTSP/5Hz/长期通过。HDMI授权保持但实际时序/scanout/停止映射缺证，未写入1080p60。结果VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md及evidence/video-descriptor-20261007-r5/completion-review.json，新next-checkpoint为当前恢复点，旧暂停/失败保持历史。下一按批准计划审查动态样片、独立RTSP准备，实际NAL/PTS和owned AU；用户资料全部在本地，不反复索要未知资料。测试与SSH/SFTP已结束，无后台任务。

- 视频任务已恢复（2026-10-07）：用户明确要求继续中断任务，撤销上一条整体暂停。代理先读RESUME-VIDEO/暂停检查点并复核冻结身份，准备最小r2 QUERYBUF/QBUF/DQBUF/映射cookie/offset/所有权/poll取证；保持格式/码率/profile/队列数/复制/输入及旧r1失败，不重跑r1/猜复位或改BOOT。先只读设备状态与未完成download.bit来源核查，再新修订有界取证；异常保存停止。HDMI测试授权保持，配套不明不写寄存器，原推理模型/SDK/帧协议保持；旧暂停按历史理解。

- 视频阶段用户主动暂停（2026-10-07）：用户要求标记进度并在安全位置中断，等唤醒继续。新SDK无关有限VPU API/54帧候选已构建，27份ARM真实画面与54输入身份核验，协商exit0；真实编码r1提交9/归还3、仅3图像后exit1，内核H264ENC MMU ABORT，部分29879字节与全部失败证据回传，未动态/RTSP验收。失败后BOOT/SDK/三库与FPGAoperating保持，无重试/复位/换BOOT。HDMI只读DT/clock/fbdev/DRM/udma及发布包身份核对、离线1080p色条完成，时序/scanout/安全停止仍缺证，未HDMI写入/实屏。原SSH/SFTP已关闭，补查download.bit连接在认证前取消、该查询未执行。当前整体暂停，停止编译/连接/编码/HDMI/后台/自动唤醒，原HDMI授权保留但不在暂停期间执行。恢复先读VIDEO-SEQUENCE-RESULTS-20261007.md、evidence/video-sequence-20261007-r1/next-checkpoint.json与RESUME-VIDEO-20261007.md；先本机身份与失败复核、最小IOCTL/映射/所有权取证设计，再新修订有界验证，不重跑r1、猜profile/cache/延时/复位或把部分视频计通过。无新目标/自动化；等待用户明确恢复。

- 用户审查视频并恢复HDMI授权（2026-10-07）：用户已完成独立H264视频审查，要求下一步计划并明确允许HDMI测试，解除此前HDMI暂停。代理准备NEXT-VIDEO-PLAN-20261007.md：先真实27预生成骨架54帧文件与HDMI配套核查，再有依据的1080p60独立色条/换帧、capturePTS/NAL/色彩信号及独立RTSP，最后真实推理接入/双路。构建/传输/审计由代理，实屏OSD与画面需用户现场核对。HDMI参考宽高只分配udma/cache和写参考地址，不配置clock/timing，不据此猜写；BOOT/SDK/模型/RAW及帧协议保持，启动组件更换另给具体方案，独立阶段串行/有界/失败保留停止。本轮仅本机资料和计划，未新板测/时序切换；旧暂停按历史理解，新检查点video-next-plan-20261007.json。

- 独立VPU文件编码与主机审查完成（2026-10-07）：用户授权暂停HDMI并独立H264，代理实测r4 MVX720p NV12两planes/stride1280、H264一plane、两端601有限、10fps/2Mbps/Baseline读回；30帧MMAP输入正常STOP→LAST/归还，36717字节Annex-B/37649字节MP4回传哈希一致，主机OpenCV30ID/移动条/唯一图正确，两种文件解码逐位相同，exit0/stderr空/dmesg同/BOOT及SDK保持。程序8f713fc8d6c76a03053544634591448f1068ef0a392261023bf73d5b1538e8ce。保留清单CRLF、coded2x2顺序、默认coded色彩与裸流rate断言历史；未放宽720规格。编码独立预生成合成图不是新推理/RTSP/5Hz/长期。裸流PTS/ffprobe色彩未知，MP4 nominal10fps离线重建，后续RTSP需capturePTS/NAL边界和色彩依据。无新安装/HDMI或NPU初始化/寄存器/BOOT变化，显示目标1080p60仅目标并继续暂停。结果VPU-RESULTS-20261007.md及evidence/vpu-20261007-r1/completion-review.json；会话结束、新next-checkpoint恢复，旧“未编码/未接屏”按历史理解。

- HDMI新目标与独立编码授权（2026-10-07）：用户连接DELL E2421HN后报告不支持当前时序，明确HDMI目标改为1920×1080@60Hz并先暂停HDMI测试。代理可准备、执行有限独立H.264编码及上传主机审查；沿用已验证720p10fps CPU输入、实际V4L2协商/MMAP、完整身份与异常停止，勿初始化NPU/HDMI、写寄存器或修改BOOT/模型/SDK。PC截图不作板端时序证明；未接屏文字为历史，实际时序更改在暂停期间不执行。

- E1-C渲染与V0部分配套完成（2026-10-07）：用户核对进度后要求继续，并确认HDMI显示器未连接。代理完成1280×720固定视角/源BONES14条/显示层C2翻转，原坐标/数学/引擎/复制/模型/RAW/SDK/BOOT/帧协议保持，不导入GT、阈值、匹配/滤波或物理单位/解剖标签。Native/ARM四状态与8拒绝、真实27画面及RGB565LE/NV12/NV21逐位Native/NumPy通过；新467包/23来源构建、Host107/59600值、三帧2Hz网络真实推理＋本帧绘图通过，179/52/70完整回传，exit0/stderr空/dmesg保持。程序0fc63b8f64a78884538ab8c4cb4701ad5fc6046e11e44ad62f960cf5b8dd9533。绘图约11.94ms、三种诊断转换约88.85ms不作5Hz/长期。只读V4L2/query/sysfs显示MVX两端MPLANE，720p NV12/NV21/H264枚举存在；未S_FMT/REQBUFS/STREAMON、编码/RTSP/HDMI或写寄存器，HDMIclock/scanout配套仍未知。结果RENDER-RESULTS-20261007.md、V0-VIDEO-PAIRING-20261007.md及evidence/render-20261007-r1/completion-review.json；会话全部结束，恢复读新next-checkpoint，下一独立VPU按返回planes/stride/colorimetry门检，HDMI需匹配BOOT时序及接屏，不套参考单平面CAPTURE/固定SPSPPS或相机MMU修改。深度异构优化后置，旧待渲染文字为历史。

- E1-A/B首批完成（2026-10-07）：代理按批准路线完成隔离生产接口（无固定Tokens依赖、验证包装器保留）、TCP完整记录/单待处理槽位/单Engine及有界诊断。Native/ARM协议自检、411包/19来源构建身份、BOOT9/SDK一致；Host107/59600值、交替两入口8前向、3/27网络30前向共38成功全输出逐位此前板端，四阶段exit0/stderr空/dmesg保持。2Hz发送下无丢弃/拒绝，27帧到达至结果191.95180ms/P95 193.76084ms不作整机5Hz。程序402cac43ca9de6bccb3ddf41ea7069d351f6d2e8e4500f33c41940d0869cc50c，冻结旧源/模型/RAW/SDK/BOOT/数学/复制/帧协议保持；最小日志采样4帧/8192计时条目、有限CLI最多1000帧不是长期服务。r1编译函数名错误新r2修正；27首次就绪检查20秒/总120秒因控制延误超时124，七输出逐位一致。保留失败，仅外部新控制脚本与新目录300秒/90秒READY后一次修正通过，同包/程序/门禁未伪改。结果APPLICATION-RESULTS-20261007.md及evidence/application-20261007-r2/completion-review.json；会话/后台测试全部结束。下一恢复读新next-checkpoint，E1-C渲染/V0视频配套接续既有已批准路线；未经配套确认不猜寄存器/换BOOT，新依赖另定，深度性能优化后置。旧首批未运行文字为历史。

- 首版接入计划已批准并开始（2026-10-07）：用户明确“同意你的计划方案，请继续执行”，批准FULL-FLOW-PLAN-20261007.md路线。代理先执行首批E1-A生产接口与E1-B TCP回放；SDK/BOOT/模型/RAW/CPU数学/帧协议保持，单Engine串行、最新完整窗口槽位1、验证包装器保留固定参考。无新依赖，先SDK无关协议/队列自检→新ARM构建身份→Host107→生产/验证三帧重复回归→三/27帧网络结果对照；新修订保留失败与旧包，不重试同一失败运行或自动复位。源代码与有界日志修改属于此次接入；零拷贝/图/新内核优化仍后置。视频按后续配套/独立测试图/合并门检顺序，不因本批通过而宣称双路、整机或30分钟验收。

- 首版异构基线与延期优化决策（2026-10-07）：用户明确以当前异构方案先完成项目全流程，闭环后再考虑真实指针映射/零拷贝、图与自定义算子性能优化。ADR/ADR_01.md已记录注册/布局/跨域内存/融合/帧状态/性能及视频配套难点，保留lazy-r4显式SDK复制、CPU适配、Gather/Matmul分工与reset(1)最终就绪协议；164ms等待不归为已证实搬运，0.47ms可见复制不作全后端搬运上界。FULL-FLOW-PLAN-20261007.md规划E1-A生产接口→E1-B TCP→渲染→独立HDMI/编码RTSP→双路/30分钟，下一批建议仅A/B，具体实施与设备/视频配套另定。本轮仅本机文档整理，无新代码/构建/SSH/设备初始化；项目粗估69/100约65%–70%不因写方案增加。N2非阻断，旧暂停/待数值文字按历史理解，不以规划代替实施或验收。

- P2定位与消息优化完成（2026-10-07）：按用户profiling-off/单时钟性能任务，r3量到平均212.93086ms/4.69636Hz，CPU桥等待164.48ms、CPU forward29.59ms，复制仅0.47ms；ZG调用跨度不作纯NPU时间。新增隔离lazy-r4，仅CPU/验证助手各增加const char*消息重载共4行，所有原检查/计算/SDK调用/同步/缓冲区策略保持，原CPU/r2/r3/r6不改。Host107含拒绝、原三帧＋重复、3预热＋30计量通过；37次输出逐位r6、exit0/stderr空/dmesg相同。平均190.60146ms/P95 190.75409ms/最大190.80669ms/5.24655Hz，当前短期处理基线达5Hz但不含网络/渲染/编码，余量约9.4ms；整机/10Hz/长期未通过。程序4f7fe3597bb2aaaa69884a429062ce0c3977b63a30c328b8ce6c9f9e41ab84ad，352包/16构建。数值阶段按用户决定通过，原误差与query未证事实保留，N2非阻断。原perf_gate遗漏hashlib只以独立review_perf_stage供标准库绑定修正，不改数据/hash/规则、不重跑板测。结果P2-RESULTS-20261007.md及evidence/perf-20261007-lazy-r4/completion-review.json；会话关闭。当前性能任务已完成，后续未知窗口生产接口/网络/渲染/视频及算法、同步、缓存或模型变化另议。

- 用户数值验收与P2已批准（2026-10-07）：用户明确批准现有27样本数据精度阶段，接受候选排序颠倒解释，同时要求关闭SDK profiling、优先以单一时钟拆分forward内部各类开销并寻找优化方案。记录为用户基于现有证据的验收决定，不将算术精度/排名交换推断写成跨端query身份证明；PC/板端模型输入已逐位一致，不归因于已证实的传输损坏。代理可实施独立profiling-off计量候选并执行Host/原三帧回归及3预热＋30计量，原模型/SDK/BOOT/帧完成协议保持、失败停止、新目录保留r2。采用steady_clock记录Host、SDK等待/复制和ZG backend跨度，异步跨度不等同纯NPU耗时；数值原误差不改写，不新增ONNX中间输出/依赖或视频。具体改变算法、缓存、同步、并行或位流的优化方案仍据实测另议。

- E0/N1/P1及H0完成（2026-10-07）：用户恢复后代理完成r2本地/ORT复核、P1预热三帧先对r6的前置门禁、FPAI构建和Lite四阶段。Host107/12注册/22输出通过；E0四帧与r6逐位一致；N1 27＋重复28次、27套输出/476捕获/实际CPU364000值一致；P1三预热＋30计量33次全部与r6一致，每帧0→745、1173七ZG组/六计算Host保持。四阶段exit0/stderr空/dmesg相同，52/124/604/113回传；程序8970f692b8636e420ae972277fb2a45b79b844895e0664fd99d8352e4cf00192，351包、BOOT/模型/RAW/SDK/CPU/桥/预处理/r6/r1保持，profiling开启。ORT27独立86项及旧308一致；同槽坐标最大2.77697、最高分坐标2.67562模型单位，S52_18_317前两名交叉支持排名交换推断而ORT query身份未证，原误差未重排、容限未通过。P1平均214.85948ms/4.65420Hz、P95 215.49764ms，forward占93.72%，≥5Hz及整机/长期未通过。H0只读资料完成，720p/骨架/VPU配套仍未知，不初始化视频。结果RUNTIME-RESULTS-20261007.md、evidence/runtime-20261007-r2/completion-review.json；SSH/SFTP已关闭。原E0/N1/P1任务已完成，停止自动执行；NEXT-GATE-20261007.md的N2/P2及E1/视频/容限/新依赖/profiling改动未批准，需讨论后再执行。旧暂停/未板测文字为历史。

- E0/N1/P1已恢复（2026-10-07）：用户确认Lite已开机并明确要求继续中断任务，撤销该任务暂停。代理按原批准范围先读取恢复检查点，审查源码/ORT参考并补P1测量前r6门禁，新包新构建保留r1，再逐阶段Host107→E0→N1→P1。原模型/RAW/SDK/BOOT、profiling及异常停止条件保持；H0本机只读，视频/E1及容限另议。旧暂停文字为历史，不扩大为新训练或视频执行授权。

- 全项目进度/恢复标记完成（2026-10-06）：当前用户仅要求整理进度，不解除此前E0/N1/P1暂停。根PROJECT-PROGRESS.md为全项目当前总览，约50%–60%仅首版工程管理粗估（主观工作包权重58/100），不是功能/数值通过率或剩余工期；实时采集终版和2026训练旁支另列。下次先读tools/pose-v1/RESUME-20261006.md及evidence/runtime-20261006-r1/progress-snapshot.json；先源码/参考复核并补P1测量前r6校验，用新修订/包/构建保留r1，再Host107→E0→N1→P1，视频另议。旧状态文件/README历史已折叠保留，暂停期间不连接、构建、推理或启用自动化。

- E0/N1/P1用户暂停（2026-10-06）：用户确认Lite已关机且不在现场，明确要求先中断任务，唤醒后继续。新隔离核心已交叉编译/构建身份核验，27样本＋重复ORT参考已生成；没有板端传输、Host107、新核心回归或N1/P1执行，不当作新工程/性能验收。停止连接重试、后台工作或自动唤醒；恢复先读evidence/runtime-20261006-r1/pause-checkpoint.json并完成源码/证据复核。原E0/N1/P1批准范围保持，待用户明确恢复。

- E0/N1/P1实施与执行方已批准（2026-10-06）：用户明确回复“同意，由代理执行”，批准NEXT-PHASE-PLAN-20261006.md。代理新增隔离运行核心、一次180秒原三样本＋首帧重复回归，既有Host107注册回归；通过后在既有ORT环境生成九组27固定样本＋重复参考、一次120秒28次板测；再做原三帧输出回归及一次120秒3预热＋30计量低日志基线。SDK profiling保持，模型/RAW/SDK/BOOT及r6源码程序保留，异常停止不自动重试；安全帧边界reset(1)沿用已验收协议，不作reset(0)。H0仅本机只读视频/骨架资料。新依赖、中间ONNX输出、误差容限、视频初始化及E1网络应用仍另议，批准不等于新阶段验收。

- 难点复盘与下一阶段准备完成（2026-10-06）：用户要求总结Done.md并准备后续推进，代理把r1–r5历史记录折叠保留，集中整理环境/换行/构建/Host注册布局/融合ID/跨帧状态/数值候选/性能/HDMI及人工边界难点。仅读既有证据，新增prepare_next_phase.py实际核验27候选（九组各首/中/末，来自既有300），生成排序/时间预算分析；板端相邻同分29/30/31 vs ORT1/2/0不证明排序为全部误差根因，带取证207.230065ms＋另测PS5.781265ms仅约213ms预算提示。NEXT-PHASE-PLAN-20261006.md推荐E0核心→N1 27＋首帧重复→P1 3预热＋30计量、H0本机资料并行。尚未新模型/板测/编译或修改r6运行源码；新阶段实施/执行方与容限待确认，上一轮代理全权故障修复不自动扩展为新视频/性能范围。当前27仅身份选择不是数值验收，SDK profiling保持，相关关闭或优化另据实测讨论。

- 跨帧同输出故障r6已解决并验收（2026-10-06）：代理按用户全权授权完成构建/传输/Lite全阶段测试。r5实测计数首次0→745、次帧745→1222，SDK本帧绝对阈值提前满足；仅mixed_check.cpp每帧安全边界调用官方Device::reset(1)清FPGA状态、确认0，输出waitForReady及最终745后才下一帧，不做reset(0)/直接寄存器/SDK模型BOOT修改或Session重建。r6构建/Host107/离线/内存/apply/单/三全部退出0；131三帧回传/68内容/76状态，四次0→745，三份分数和姿态分别不同，重复308所有捕获及输出逐位一致，五CPU实际52000FP32由NumPy一致，1173七组/六计算Host/Gather保持。程序f826fc31441caf09ef22d94561672023737ab4c330ba22ec0159ecf7f77e144a，SDK3.39.0/设备25122301/icore24160628/291包保持，内核各阶段前后相同。mixed-three.acceptance.json及完整ONNX误差已生成；数值容限/MPJPE/持续性能未验收，约206.6–208.2ms少量取证前向不作5Hz通过。结果MIXED-FRAME-STATE-R6-RESULTS.md及evidence/mixed-20261006-frame-state-r6/completion-review.json；旧r3/r4/r5失败和原检查器保留，不重跑历史包或扩展到HDMI/RTSP及无关训练。

- 当前混合推理难点执行方调整（2026-10-06）：用户明确将当前问题所有执行操作交由代理，要求优先排查并解决后报告。代理可直接执行当前问题的构建/传输/板端取证和有依据的最小修正验证，无需用户逐阶段代执行；保留旧证据和身份门禁，不将此授权扩展到无关训练、模型/权重更换、BOOT/位流替换或外部消息。原当前问题待批准取证的执行权限按此最新授权更新，修复结论仍须实测，不用猜测性配置或重复同一失败运行代替诊断。

- r4三样本内容异常复核（2026-10-06）：用户一次回传130项、四forward后退出1“不同CSI全部输出相同”，68内容1015040字节全有限、291包/SDK/设备/真实参数/1173覆盖及内核保持。每次caller/Input0与当前固定输入一致；309 Input0变化10431而ZG9185→TopK188暂存不变，310及重复308前段188/192/437变化但后段582/649和最终4300输出仍首帧，重复308前段不等首次。五适配节点对本次真实输入由NumPy重算28结果52000FP32逐位一致；Gather442未内容捕获不扩大验收。范围已缩至PS/NPU交接、完成状态/搬运/复用待查，未证明ready/cache或SDK故障。无三样本门禁，停止重跑/正常数值/显示/性能；原源码不改。结果MIXED-CONTENT-R4-THREE-FAILURE.md和evidence/mixed-20261006-content-r4/mixed-three-failure-review.json；MIXED-CONTENT-R5-READINESS-PLAN.md仅未批准候选，不执行reset/setReady(false)/sleep/重建Session等猜测修复。代理仅本机证据与SDK阅读，旧待三样本属历史。

- r4单样本内容验收（2026-10-06）：用户一次回传69项，291包/SDK/程序/设备身份一致，退出0/stderr空/内核前后相同。308/frame6/invocation0真实caller及Input0各10800FP32与固定输入逐位一致，17份Host内容253760字节全有限；七ZG及六计算Host实际回调，八ADDR→CPTR搬运115360字节，4300输出与r3单样本逐位一致。mixed-one.acceptance.json及独立内容复核已生成，单次207.07742ms不算持续性能，提供输出writeback未触发。仅用户MIXED-CONTENT-R4-COMMANDS.md H一次300秒同Session308/309/310/308内容诊断完整回传；失配保留部分记录停止，不自动重试/reset/cache/ready修改。连续输入问题仍未知，诊断改变时序不作修复证明，数值/性能未验收。结果MIXED-CONTENT-R4-ONE-RESULTS.md及evidence/mixed-20261006-content-r4/mixed-one-independent-review.json；代理仅本机分析，旧待单样本为历史。

- r4 apply-only验收（2026-10-06）：用户一次回传45项，1181原节点/1173HardOp经七实际ZG组完整唯一覆盖、八Host和固定成员/同步基线保持，十快照/汇总齐全；291包/SDK/程序/设备/RAW/PS身份一致，退出0/stderr空/内核前后相同，无模型forward/桥执行/content目录。apply-check.acceptance.json已生成，用户仅MIXED-CONTENT-R4-COMMANDS.md G一次180秒308内容取证并完整回传，17预期记录含caller/Input0/八暂存输入/七结果，提前输入失配停止时保留部分记录，不重试/改ready/cache或直接三样本。部署通过不证明真实Input0更新或r3故障修复；结果MIXED-CONTENT-R4-APPLY-RESULTS.md及evidence/mixed-20261006-content-r4/apply-independent-review.json，代理仅读本机文件，旧待apply为历史。

- r4 SDK内存验收（2026-10-06）：用户一次回传28项，两16KiB ADDR SDK数据缓冲区六回读/24,576有限FP32逐位一致含正负零，与r3一致；device25122301/icore24160628、291包/SDK/程序身份通过，退出0/stderr空/内核前后相同，未Session/forward、content_capture=false。memory-check.acceptance.json已生成；用户仅MIXED-CONTENT-R4-COMMANDS.md F一次300秒apply-only完整回传，1173原覆盖/八Host/固定七组保持，核验前不内容前向或复用旧门禁/重试/复位。SDK复制不证明输入更新或NPU同步，r3故障未定位。结果MIXED-CONTENT-R4-MEMORY-RESULTS.md及evidence/mixed-20261006-content-r4/memory-independent-review.json；代理仅读本机文件，旧待内存为历史。

- r4离线验收（2026-10-06）：用户一次完整回传32项，代理核验真实四RAW参数与r3一致、三PS输入32,400有限FP32与固定/ONNX/r3逐位一致、12注册及Gather保持；291包/15ARM头文件/两库/3.39.0及新程序身份通过，退出0/stdout及stderr空、内核前后相同，无设备/Session/NPU、content_capture=false。offline-check.acceptance.json已生成，用户仅MIXED-CONTENT-R4-COMMANDS.md E传新门禁，在BOOT/JTAG保持且无竞争访问时一次30秒SDK内存往返并完整回传；核验前不apply/forward或复用旧门禁。实际Session输入仍未取证，不作根因/修复结论；结果MIXED-CONTENT-R4-OFFLINE-RESULTS.md及evidence/mixed-20261006-content-r4/offline-independent-review.json，代理仅本机分析，旧待离线为历史。

- r4 Host及内容路径验收（2026-10-06）：用户完整回传52项，107例/12注册/22CPU输出59,600有限FP32与固定/r3逐位一致、94Host CPTR桥事件/Gather保持；附加两模式SDK Host读回和模拟Input0别名四正例与NumPy逐位一致、错期望负例false且实际数据不改、未分配/FP16读取前拒绝。五捕获216000字节/汇总阶段完整，291包/SDK/程序身份匹配、退出0/stderr空/内核前后相同，无Device::Open/Session/NPU。host-check.acceptance.json已生成，用户仅MIXED-CONTENT-R4-COMMANDS.md D一次30秒离线并完整回传，核验前不硬件/复用旧门禁/重跑r3；实际Session Input0尚未取证，不能称根因或修复通过。结果MIXED-CONTENT-R4-HOST-RESULTS.md及evidence/mixed-20261006-content-r4/host-independent-review.json；代理仅读本机文件，旧Host待验为历史。

- r4-final内容取证构建验收（2026-10-06）：用户GCC9.4/CMake3.24.2、ARM两包3.39.0完成五CPP编译/链接，代理核对291包/20来源/12构建副本/15ARM头文件/两库匹配。AArch64 PIE578960字节，SHA256ba8d53985fabdfdc12939d794825d31a0ee29bf9516567be5ba9356c515dcea7，直接Host/ZG依赖、无RPATH/RUNPATH；仅原JSON缩进warning147行已审查，无error。build.acceptance.json已生成，用户仅MIXED-CONTENT-R4-COMMANDS.md B/C新final目录传输＋Host107/附加纯Host内容测试并完整回传，不直接离线/硬件或复用旧门禁。SDK read/句柄API可编译不代表实际读回/Session内容或已修复，r3失败保持。结果MIXED-CONTENT-R4-BUILD-RESULTS.md及evidence/mixed-20261006-content-r4/build-review.json；代理仅读本机文件，旧未编译属历史。

- 连续输入内容r4批准后交付（2026-10-06）：用户明确“同意”输入内容取证方案，代理保存r3五源码/脚本备份，新增--capture-host-content、实际caller SDK读回、Input0返回逐位比较、桥现有复制后的Host暂存/计算结果捕获及invocation；仅有界Host CPTR FP32，不新增设备读/寄存器，不跨次保留诊断caller句柄，不改原wait/copy/ready、CPU数学/Gather/融合/模型/RAW/SDK。Host107后附纯Host捕获/别名模拟及错期望/未分配/FP16拒绝路径；本机模拟Host/一/四次正例及11异常/提前停止通过，不算ARM/Session结果。最终包package-20261006-content-r4-final为291哈希/12构建/20来源，初始中间包保留勿用。用户仅MIXED-CONTENT-R4-COMMANDS.md A标签mixed-20261006-content-r4-final编译，核验后按新身份Host/离线/内存/apply/单/三逐阶段；不重跑r3或猜测性reset/cache修复。交付MIXED-CONTENT-R4-DELIVERY.md、evidence/mixed-20261006-content-r4/delivery-review.json；未新编译/板测，诊断影响时序不能作性能/已修复结论。

- r3三样本异常停止（2026-10-06）：用户一次mixed-three回传61项，四次前向后退出1“不同CSI全输出相同”，无summary/验收。三PS输入不同且与固定/ONNX一致，309/310有10431/10445元素变化、ONNX全部分数/坐标变化；板端三个4300输出却与308首帧及之前mixed-one逐位一致。每次七ZG/六Host回调、32桥事件，身份/绑定/参数/内核正常、available均689MiB；回调不证明新帧内容，约39ms后续耗时不得作性能通过。保留三帧结果，停止重跑/正常数值验收/后续硬件显示，不伪造三样本门禁。MIXED-INPUT-FRESHNESS-DIAGNOSTIC-PLAN.md为待批准新r4内容取证，实际caller Tensor/Input0/已复制Host暂存及Host结果逐次捕获，不猜测性改cache/ready/reset/模型/SDK。当前根因未知，运行源码保持；结果MIXED-FUSION-R3-THREE-FAILURE.md及evidence/mixed-20261006-fusion-r3/mixed-three-failure-review.json，代理仅本机数据/SDK阅读。

- r3单样本混合工程验收（2026-10-06）：用户mixed-one完整回传51项，退出0/stderr空；308/frame6一次前向，七ZG组和六Host计算节点实际执行，八SDK ADDR→Host CPTR搬运115360字节，完整4300有限FP32输出/参数/输入/绑定/291包/SDK/程序/设备身份通过，内核前后相同。mixed-one.acceptance.json已生成；单帧forward204.64506ms不作5Hz/持续性能结论，本次适配结果Host返回、提供输出缓冲区writeback未触发。初步ONNX有差异（分数最大0.00304520、同槽坐标1.32329583、各端最佳坐标0.01611638模型单位），无精度/MPJPE/物理单位或候选身份结论。用户仅MIXED-FUSION-R3-COMMANDS.md H一次300秒三帧+同Session重复首帧并完整回传，核验跨Session/同Session重复及不同输入响应后全误差讨论；不重试/改容限/模型/SDK。结果MIXED-FUSION-R3-ONE-RESULTS.md及evidence/mixed-20261006-fusion-r3/mixed-one-independent-review.json；代理仅本机分析，旧前向待验为历史。

- 正式融合r3 apply验收（2026-10-06）：用户一次apply完整回传45项，退出0/stderr空/无failure；创建1181原绑定及部署后1181逻辑追溯完整，1173HardOp经七实际ZG组9185–9191完整唯一覆盖、固定成员及同步基线匹配，六计算Host与Input/Output保持，8622归9185。C++正式门检/本机独立复查及291包/SDK/程序/设备/RAW/PS身份通过，十快照/汇总齐全，内核前后相同；无forward/桥执行/模型输出。apply-check.acceptance.json已生成，用户仅MIXED-FUSION-R3-COMMANDS.md G一次180秒mixed-one/308完整回传，核验前不三样本/重试/复位/改模型或SDK。部署通过不宣称NPU计算、同步、数值或性能。结果MIXED-FUSION-R3-APPLY-RESULTS.md及evidence/mixed-20261006-fusion-r3/apply-independent-review.json；代理仅本机分析，旧待apply属历史。

- 正式融合r3内存验收（2026-10-06）：用户一次memory完整回传，代理核验28回传/291包/15ARM头文件/两库/3.39.0及新程序身份匹配，退出0/stderr空；device25122301/icore24160628、SDK ADDR PLDDR两16KiB六回读/24,576有限FP32逐位一致含正负零，内核前后相同。memory-check.acceptance.json已生成；用户仅MIXED-FUSION-R3-COMMANDS.md F一次300秒正式apply，1181原绑定/七实际ZG组1173完整唯一覆盖/八Host/固定成员与同步基线保持，完整回传核验前不forward，不自动重试/复位或复用旧门禁。SDK复制不证明NPU同步，新融合函数实际运行仍待Session门检。结果MIXED-FUSION-R3-MEMORY-RESULTS.md及evidence/mixed-20261006-fusion-r3/memory-independent-review.json；代理仅本机分析，旧内存待验证属历史。

- 正式融合r3离线验收（2026-10-06）：用户完整回传，代理核验真实四RAW参数与r2一致、两K=100及两份完整ScatterND索引网格；三PS输入32,400有限FP32与固定/ONNX/r2逐位一致、12注册和原Gather保持。32回传/291包/15ARM头文件/两库/3.39.0及程序e8d66113…e6c696a8身份匹配，退出0/stdout及stderr空、内核前后相同，无设备初始化/Session/NPU。offline-check.acceptance.json已生成；用户仅MIXED-FUSION-R3-COMMANDS.md E传新验收，在BOOT/JTAG保持且无竞争访问时一次30秒SDK内存往返并完整回传，核验前不apply/forward或复用旧门禁。结果MIXED-FUSION-R3-OFFLINE-RESULTS.md及evidence/mixed-20261006-fusion-r3/offline-independent-review.json；代理仅本机分析，旧离线待验证属历史。

- 正式融合r3 Host验收（2026-10-06）：用户完整回传后代理核验107例（18正常/89拒绝）、12注册、22输出/59,600有限FP32与固定及r2逐位一致、Gather保持；94桥事件均Host CPTR（84输入/10输出），45回传/291包/15ARM头文件/两库/3.39.0及程序e8d66113…e6c696a8身份通过，退出0/stderr空、内核前后相同。host-check.acceptance.json已生成；用户仅MIXED-FUSION-R3-COMMANDS.md D传新验收后一次30秒离线并完整回传，核验前不硬件/重跑/复用旧门禁。无设备初始化/完整Session/NPU，新融合追溯函数尚未ARM执行。结果MIXED-FUSION-R3-HOST-RESULTS.md及evidence/mixed-20261006-fusion-r3/host-independent-review.json；代理仅本机分析，旧Host待验收属历史。

- 正式融合r3构建验收（2026-10-06）：用户GCC9.4/CMake3.24.2、ARM Icraft/CustomOp3.39.0完成五CPP编译/链接；代理本机核对291包/17来源/11构建副本（含静态融合基线头）/15ARM头文件/两后端库匹配。AArch64 PIE555800字节，SHA256e8d66113ad3d9a34f9f210e5f7038560bc3dbfa681b9a057d748ff39e6c696a8，直接Host/ZG依赖、无RPATH/RUNPATH，仅旧JSON缩进warning143行且已审查，无error。build.acceptance.json已生成；用户仅MIXED-FUSION-R3-COMMANDS.md B新目录传输＋C Host107完整回传，核验前不offline/硬件或复用旧门禁。新API可编译不代表映射运行/正式apply/前向通过，代理未编译/板端接入。结果MIXED-FUSION-R3-BUILD-RESULTS.md及evidence/mixed-20261006-fusion-r3/build-review.json，旧未编译属历史。

- 正式融合追溯r3批准后交付（2026-10-06）：用户明确“同意”MIXED-FUSION-BINDING-FIX-PLAN.md，代理保存r2源码/核验器备份并应用修正。创建1181原绑定/1173HardOp全ZG，部署仅实际绑定七组经固定merge_from完整唯一覆盖1173，八Host保持；组ID/同一后端实例/同步表/基线变化拒绝，原层数0不当缺覆盖。保留快照、新增原到有效ID及汇总，核验器识别HardOpNode并独立复查，apply无forward范围保持。新C++/JSON基线、本机回放18异常＋非布尔标记拒绝、291包哈希/11构建/17来源/LF及AST通过；模拟记录不算ARM执行。原infer/CMake/CPU/桥/预处理/forward保持，未编译或板测。用户当前仅MIXED-FUSION-R3-COMMANDS.md A新标签mixed-20261006-fusion-r3构建，核验后Host→离线→内存→一次apply逐阶段，不复用旧门禁/重跑r2/直接mixed。交付MIXED-FUSION-R3-DELIVERY.md、evidence/mixed-20261006-fusion-r3/source-and-package-review.json；旧待批准为历史。

- 绑定快照r2取证完成（2026-10-06）：用户一次apply完整回传45项，身份/设备/RAW/PS和内核正常，Session创建及apply返回后仍退出1于原8622直接查绑定。十份快照显示创建1173原HardOp均ZG，部署七组9185–9191实际ZG绑定，merge_from恰好覆盖1173原节点一次，无遗漏/重复/额外成员，8622归9185；六Host及Input/Output保持。仅本机审计实际快照和九异常拒绝通过、完整原到组映射保存；428原条目layer_count0不作缺覆盖判据。未forward、不生成apply门禁；正式C++/gate未改，HardOp与实际HardOpNode识别差异待一起修正。MIXED-FUSION-BINDING-FIX-PLAN.md为新待批准方案，暂停新硬件/前向，不降低1173/六Host要求、不改SDK自动优化。结果MIXED-BINDING-R2-APPLY-RESULTS.md、evidence/mixed-20261006-binding-r2/apply-independent-review.json及binding-snapshot-audit；代理仅本机文件分析。

- 绑定快照r2内存验收（2026-10-06）：用户一次memory-check完整回传，代理核对28回传/290包/15ARM头文件/两库/3.39.0及新程序94a03a90…bd061248身份一致；退出0/stderr空，device25122301/icore24160628，两16KiB SDK ADDR PLDDR缓冲区六回读/24,576有限FP32逐位一致含正负零，dmesg完整前后相同。memory-check.acceptance.json已生成，用户按MIXED-BINDING-R2-COMMANDS.md G仅一次300秒Session创建/apply公共绑定快照取证，原1173/六Host门检保持，非0仍完整回传，不forward或自动重试/复位/降低计数。仅SDK设备复制通过，不证明NPU同步/完整绑定/数值；实际融合映射待分析。结果MIXED-BINDING-R2-MEMORY-RESULTS.md、evidence/mixed-20261006-binding-r2/memory-independent-review.json；代理仅本机文件分析，旧内存待回传属历史。

- 绑定快照r2离线验收（2026-10-06）：用户完整执行回传，代理本机核验32回传/290包/15ARM头文件/两库/3.39.0及程序94a03a90…bd061248身份一致，退出0/stdout及stderr空；真实RAW两个K=100、两份ScatterND索引与完整坐标网格一致，三PS输入32,400有限FP32与固定及ONNX参考逐位一致、12注册和原Gather保持。dmesg完整前后相同，无设备初始化/完整Session/NPU。offline-check.acceptance.json已生成；用户按MIXED-BINDING-R2-COMMANDS.md F传新门禁，在BOOT/JTAG保持且无AI/显示竞争访问时仅一次30秒SDK两16KiB内存往返并回传，核验前不apply/mixed，不重跑旧阶段或复用r1门禁。结果MIXED-BINDING-R2-OFFLINE-RESULTS.md及evidence/mixed-20261006-binding-r2/offline-independent-review.json，旧离线待回传属历史。

- 绑定快照r2 Host验收（2026-10-06）：用户完整回传后代理本机核验107例（18正常/89拒绝）、12注册、22输出/59,600有限FP32逐位一致，与r1已验收输出相同；290包/45回传/15ARM头文件/两库/3.39.0和新程序94a03a90…bd061248身份通过，退出0/stderr空，94次桥搬运均Host CPTR，dmesg完整前后相同。host-check.acceptance.json已生成；提前offline仅三预检文件/290OK，确认程序未启动，本机失败目录保存在offline-preflight-missing-gate。用户按MIXED-BINDING-R2-COMMANDS.md E传新Host验收、固定目录受保护改名保留板端预检后仅一次30秒offline并回传；不重跑Host/复用r1门禁/直接硬件。无Device::Open/完整Session/NPU/快照映射验收，代理未接入板端。结果MIXED-BINDING-R2-HOST-RESULTS.md、evidence/mixed-20261006-binding-r2/host-independent-review.json及offline-preflight-review.json；前述待回传为历史。

- 绑定快照r2构建验收（2026-10-06）：用户FPAI GCC9.4/CMake3.24.2、ARM Icraft/CustomOp3.39.0完成配置/五CPP编译/链接；代理核对290包项/10源码及副本/15头文件/Host＋ZG库/脚本/manifest匹配，快照源码与批准候选一致。新AArch64 ELF64 PIE 518712字节，SHA25694a03a903a4a97f229b1549dcbd1bade193d60dbb23753c1f030431fbd061248，直接Host/ZG依赖、无RPATH/RUNPATH，仅原142缩进warning且已审查，无error。build.acceptance.json已生成，可由用户B创建新20261006-binding-r2目录/传输后C仅Host107完整回传，核验再offline/memory/一次apply取证。公共字段编译通过不作实际快照/映射通过；不重跑旧r1/复用旧门禁/改SDK或直接mixed。代理只读本地审查，未Docker编译/程序/板端接入。结果MIXED-BINDING-R2-BUILD-RESULTS.md、evidence/mixed-20261006-binding-r2/build-review.json；旧新r2未编译为历史。

- 绑定快照r2方案已批准并应用（2026-10-06）：用户回复“同意方案”，mixed_check.cpp已与binding-snapshot候选逐字节一致，原r1源码已备份。仅Session创建/apply后读取完整绑定、运行/后端视图、ZG hardop_map/net_hardop/merge_from/sync索引，不再调用autoMerge，不改SDK/默认优化、原数学/前向/数据桥及严格1173＋六Host门检。新包package-20261006-binding-r2准备290项哈希通过，与r1的289非manifest载荷相同，13源身份只mixed_check.cpp变化，原CPU/推理器/CMake/模型/RAW/输入及旧r1二进制/失败目录保持。尚未新编译/测试/板端执行。用户按MIXED-BINDING-R2-COMMANDS.md先A新BuildTag mixed-20261006-binding-r2构建，代理审阅后新目录Host107/离线/内存各门禁，再一次300秒apply取证无forward；新验收不能用旧文件改名/改SHA，取证可能仍退出1，不自动接受或进入mixed。登录shell不单独set -eu，用独立sh运行，非0完整回传，不删目录/重试/复位。应用及静态证据evidence/mixed-20261006-binding-r2/source-applied.json与package-preparation.json。新正式融合覆盖核验仍须实际数据审阅；下述候选待批准为历史。

- apply-r1失败及SSH退出审查（2026-10-06）：用户在SSH登录shell直接set -eu，已有run-apply-check使test ! -e非0→errexit关闭登录shell。代理按特殊问题/日志权限SSH只读ls、SCP取回已有结果，35回传/290包及程序/SDK/上一memory身份通过；实际apply退出1，已session_applied，原HardOp8622未在预期backendBindings查到，bindings仅Input0一条，未forward/模型输出/桥搬运，完整dmesg前后相同。不可记为Session部署验收/NPU计算失败，不生成apply.acceptance或进入mixed。SDKautoMerge/merge_from支持合并追溯，但实际映射未知；仅加两阶段完整绑定/视图/ZG成员快照的候选MIXED-BINDING-SNAPSHOT-PLAN.md/.candidate.patch已准备，未应用/编译/运行。新核心修改/再apply方案须明确批准，保留1173＋六Host门检，不自动改SDK/计数/BOOT/模型/重试/复位/删目录。代理未SDK初始化或模型执行、口令未落文件；结果MIXED-APPLY-FAILURE-20261006.md及evidence/mixed-20261006-r1/apply-failure-review.json。旧当前应执行apply的文字在本次失败后暂停。

- mixed-r1 SDK内存往返验收（2026-10-06）：用户一次30秒memory-check完整回传，代理核对28回传/290包、15ARM头文件/Host＋ZG库/两包3.39.0/程序7cf761f1…52722a17及上一offline验收匹配，退出0/stderr空/阶段完整/dmesg前后相同。Device::Open成功，device25122301/icoreFMSHZGV3TECH-AID - 24160628；两16KiB缓冲区ADDR、AXIZG330AIPLDDRMemRegionNode、chunk16384/offset0。固定程序验证区域归属及非重叠；六输出/三模式24,576有限FP32逐位一致含-0/+0，最大差0。仅SDK Host↔设备搬运，无完整Session/模型前向/NPU生产者到CPU消费者同步或精度通过。memory-check.acceptance.json已生成，用户传入gates后在BOOT/JTAG保持及无竞争访问前提下，仅300秒apply-check（创建/apply/1173HardOp＋六Host绑定、不forward），回传核验再mixed-one；失败停止保存、不重试/复位/改配置。代理仅文件分析、未板端接入。结果MIXED-MEMORY-RESULTS-20261006.md及evidence/mixed-20261006-r1/memory-independent-review.json；旧memory未执行属历史。

- mixed-r1离线真实参数/PS验收（2026-10-06）：用户正式offline-check完整回传，代理核验32回传/290包、15ARM头文件/Host＋ZG库/两包3.39.0及程序7cf761f1…52722a17/上一Host验收身份通过。原RAW四参数已物化，TopK188/437 K=100；ScatterND582/649各50,400字节有限整数索引为完整100×14×3网格，未fixture替换。三CSI输入32,400有限FP32与固定/ONNX逐位一致，12注册/Gather保持；退出0/stdout及stderr空/阶段完整/dmesg前后相同。mode offline-check设备初始化false，无完整Session/前向；静态1173HardOp不作绑定通过。offline-check.acceptance.json已生成，用户传板并确认BOOT/JTAG未改变、无其他AI/显示占用后，可按已批准顺序仅30秒memory-check（SDK两16KiB、显式allow-device-init），回传核验后再apply。区域不明/身份变化/超时/OOM/总线/SDK异常即停，不重试/复位/改配置。代理仅文件分析，未板端接入。结果MIXED-OFFLINE-RESULTS-20261006.md及evidence/mixed-20261006-r1/offline-independent-review.json；旧offline未执行属历史。

- offline缺gate失败预检证据已审阅（2026-10-06）：用户报告Host验收已传板并回传失败目录，代理读取确认仅package-check/timeout-path/version三文件、290项全部OK、GNU timeout8.30，无results/exit/SDK审计/程序日志；与先前缺host-check.acceptance异常及runner门禁顺序一致，离线程序未启动。可由用户在/tmp/pose-v1-mixed-validation/20261006-r1用固定兄弟目录名保留改名，再执行一次30秒offline-check并回传；目录/验收/源目标检查失败即停，不覆盖，不重跑Host/自动硬件。代理未板端接入/执行/改源码。本次仅预检证据审阅，offline程序尚未验证、无offline.acceptance；evidence/mixed-20261006-r1/offline-preflight-review.json及MIXED-VALIDATION-COMMANDS.md。旧失败目录待回传为历史。

- mixed-r1 Host桥独立验收（2026-10-06）：用户完整回传，代理文件核验107例=18正常/89拒绝、12注册、22输出/59,600FP32全有限逐位一致最大差0；新三类桥实际搬运、五节点事件、指针均Host CPTR，Gather保持。包290/回传45哈希、15ARM头文件/Host＋ZG库/两包3.39.0及程序7cf761f1…52722a17匹配；ldd完整、退出0/stderr空、完整dmesg前后相同、available686→687MiB。host-check.acceptance.json已生成，用户可传板；此前offline预检失败目录仍需保留回传审阅，再固定子目录改名继续离线。仅新注册/Host暂存回归验收，无真实RAW/完整Session/Device::Open/NPU/部署数值或性能通过，不重跑Host/直接硬件。代理仅文件分析、未板端接入。结果tools/pose-v1/MIXED-HOST-RESULTS-20261006.md及evidence/mixed-20261006-r1/host-independent-review.json；下述待完整回传为历史。

- mixed Host运行/离线预检反馈（2026-10-06）：用户截图显示B文件已传板、host-check runner exit0；本机预期回传目录和host-check.acceptance.json均未取得，新107桥例/12注册/输出及身份未独立验收。用户提前启动offline-check，在加载gates/host-check.acceptance.json时FileNotFoundError；核对runner，此处在SDK审计和程序调用前，离线程序未执行。先用户回传run-host-check，代理核验生成验收后传入gates；不要重跑Host或执行硬件。失败预检run-offline-check已在门禁前创建，需要原样回传，确认无results/exit.txt并在Host验收后按固定子目录保留改名，再进入离线；不删除/覆盖、改runner/SDK/模型或绕过门禁。补充命令tools/pose-v1/MIXED-VALIDATION-COMMANDS.md，证据evidence/mixed-20261006-r1/host-offline-gate-feedback.json和host-exit0-offline-missing-gate-user.png，代理未接入板端。

- mixed-r1构建验收（2026-10-06）：用户FPAI GCC9.4/CMake3.24.2完成配置/五CPP编译/链接；代理主动读取日志/产物，290项包、10源码/副本、15ARM头文件、Host/ZG库/两包3.39.0及AArch64 PIE身份通过。程序SHA2567cf761f1dd7d1ca1bf8a1db1826e4d9b34574b1a8dc0ac662c987eed52722a17。唯一-Wmisleading-indentation是mixed_check.cpp142行版本JSON输出三语句同一行，if仅控制逗号，其余无条件输出符合预期；未改源码/包/脚本，不重编译。build.acceptance.json已生成，可由用户继续既定B传输后C仅host-check，回传再核验；新桥107例/SDK内存/完整Session/NPU/数值仍未通过。代理未执行Docker/编译/程序/SSH或设备访问。结果tools/pose-v1/MIXED-BUILD-REVIEW-20261006.md及evidence/mixed-20261006-r1/build-warning-review.json；下述新C++未编译为交付时历史。

- ONNX参考与正式混合候选（2026-10-06，用户已批准实施）：工程/数值分阶段，以ONNX直接对照Lite，不等待Icraft全CPU Matmul打通；正式Matmul仍NPU、Gather保持。代理获明确授权创建独立.local/pose-v1-onnx-conda并安装/运行本机CPU ORT1.23.2，固定Python3.10.21/NumPy2.2.5；三样本全部候选有限、首样本重复逐位一致、不同输入响应已验证，完整环境/依赖哈希与产物evidence/onnx-reference-environment-20261006.json。新增独立pose_mixed_check、SDK Host暂存桥、构建/分阶段/回传工具和新包；原推理器/CMake、三CPU实现文件及模型输入哈希保持。新C++尚未编译/板测，不能称mixed/NPU/精度通过。用户负责FPAI构建、传输、Lite运行；代理准备代码并主动审阅日志。顺序构建→107例Host桥→离线真实RAW/PS→30秒SDK两16KiB往返→300秒Session apply→180秒308→300秒三样本，每阶段回传核验文件同一包/程序匹配后继续；硬件必须--allow-device-init。区域/缓冲区/融合映射不明确或超时/OOM/总线/SDK异常即停止讨论，不自动重试/复位/改SDK/BOOT/模型/缓存策略。数值容限依实测讨论，不做GT/MPJPE/物理标定；HDMI/RTSP/5Hz/延迟/30分钟不含本轮结论。入口tools/pose-v1/MIXED-VALIDATION-COMMANDS.md、MIXED-VALIDATION.md；旧ORT未批准/CPU待讨论属于历史阶段。

- CPU最小适配Lite门检正式验收（2026-10-06）：用户完成r2交叉编译、Lite独立运行、回传及Windows文件复核，代理直接读取独立核验通过。107例=18正常/89拒绝，22输出/59,600个float32值与NumPy参考逐位一致、全有限、最大差0；12条注册记录匹配，TopK188/437、GatherElements192、ScatterND582/649补齐init/forward并前向通过，Gather442保持原后端并通过，CPU Matmul未补齐。新包282/回传40项哈希、程序/图/Host库、六SDK头文件/3.39.0版本匹配；ldd全解析，提交dmesg前后尾部相同，退出0/stderr空。程序SHA2568cf2017cedf6a97f98ce485d979239b659291f3c91d3a3d550382c1c94588622。仅固定FP32/全有效分布/HostDevice CPTR候选验收，未接入原推理器/创建完整Session/Device::Open/NPU/DMA/HDMI；实际NPU内存交接/CPU Matmul参考及完整mixed仍待讨论，不自动接入或运行。完整CPU-ADAPTER-RESULTS-20261006.md、evidence/cpu-adapter-independent-review-20261006.json和用户cpu-adapter-20261005-review.json。中途Windows命令拆行错误已由用户完整命令解决，勿重跑C；下述“待回传”是历史状态。

- CPU候选Lite运行截图反馈（2026-10-06）：用户截图显示在批准路径完成传输/运行，sh run-cpu-adapter.sh及exit.txt均0，stdout报告107例完成、stderr显示空，summary status=cpu_candidate_tests_passed/case_count=107，device_opened/full_model_executed/mixed_verified均false。这是用户程序内部检查报告；本地尚无完整回传目录，注册12条记录/实际22份输出/板端SDK和程序哈希独立联查未完成，不能提前宣布完整CPU门检或mixed通过。现在用户执行CPU-ADAPTER-COMMANDS.md D完整回传并文件数值复核；不要重跑C/覆盖目录/直接接入推理器。代理未连接板端或运行程序。截图和结构化反馈evidence/cpu-adapter-board-run-feedback-20261006.png/.json；此前目录未创建/运行未执行属于较早状态。

- CPU测试目录前置补充（2026-10-06）：用户报告mkdir /tmp/pose-v1-inference-20261005/cpu-adapter-20261005报No such file or directory/cannot create directory，推测历史父目录缺失，板端实际父路径尚未只读确认；不归因于重启或模型/SDK故障。已在CPU-ADAPTER-COMMANDS.md C补齐Lite SSH中ls检查、mkdir -p仅补同一批准父目录，再以普通mkdir创建独立子目录；若/tmp缺失/权限错误/子目录已存在则停止，不删除/覆盖。属于既有批准测试路径的前置说明补全，代理未创建目录、传输、接入SSH或运行算子；CPU数值/NPU仍未通过。

- CPU候选r2交叉编译复核通过（2026-10-06）：用户完成新包package/20261006-r2和构建cpu-adapter-20261006-r2，配置/两文件编译/链接通过，日志无error/warning正文。代理只读核对282项包哈希、5份源码/副本及实际脚本哈希、六ARM头文件/Host库/两包3.39.0，全部匹配；新旧281项非manifest文件相同，数学输入/参考未变。ELF AArch64 PIE SHA256 8cf2017cedf6a97f98ce485d979239b659291f3c91d3a3d550382c1c94588622，直接NEEDED无ZG/AIU、无RPATH/RUNPATH；板端ldd/注册前向和数值仍未验收。用户可按CPU-ADAPTER-COMMANDS.md C进入既有批准的一次300秒受限Host测试，原Gather保留、无完整Session/Device::Open/NPU/DMA/HDMI；完整回传核对后才判断CPU门检，不自动mixed。代理未生成包/编译/连接板端；证据evidence/cpu-adapter-r2-build-review-20261006.json。旧“r2未编译”为用户执行前历史，不能扩展为板端运行通过。

- CPU r2源码/日志修正已批准并应用（2026-10-06）：用户明确同意CPU-ADAPTER-COMPILE-FIX-20261006.md，已仅将检查器三处数组修改改为Array::set(-1,dims[-1]-1)，Build-CpuAdapter.ps1在原生命令日志捕获内临时Continue/转换stderr文本，finally恢复Stop，仍非0退出停止。两文件与审阅候选逐字节一致、原文件备份/evidence和旧测试包/失败目录保留；注册内核、SDK、模型和原推理源码未改，PowerShell语法0错误。用户下一步按CPU-ADAPTER-COMMANDS.md A生成新身份包package/20261006-r2，再B以标签cpu-adapter-20261006-r2构建；因源码身份变化本次必须新包，不回写旧manifest或跳过哈希。代理尚未生成r2包/执行Docker/编译/算子测试，不能排除其他编译问题；先回传新包/构建结果核对，再C。应用证据evidence/cpu-adapter-compile-fix-applied-r2-20261006.json，旧“候选待批准”是审批前历史；无CPU/NPU前向验收。

- CPU候选r1编译反馈（2026-10-06）：用户新目录cpu-adapter-20261006-r1已通过SDK身份审计、CMake配置/生成；代理只读核对导出六头文件、Host so/3.39.0版本及五份源码副本匹配。编译检查器mutate时PowerShell NativeCommandError中断stderr管道，本地log无error正文，未完成编译/链接。静态确认三处Array::get_mutable()->at用法错误：继承的get_mutable返回Object*，应使用SDK Array::set；不能排除其他编译问题。已准备CPU-ADAPTER-COMPILE-FIX-20261006.md和两文件候选补丁，拟仅修三处测试API及完整日志捕获、保留非0退出门禁，再由用户生成新身份包/标签20261006-r2构建。候选语法0错误但未批准/应用/重编译；现有源码、包、r1目录与日志保留，不直接进入Lite。证据evidence/cpu-adapter-compile-failure-r1-20261006.json；无算子/NPU/数值验收。旧“修正版未编译”是执行前状态，当前编译尝试仍未通过。

- CPU构建审计修正已批准并应用（2026-10-06）：用户明确同意CPU-ADAPTER-BUILD-FIX-20261006.md，生效Build-CpuAdapter.ps1已与审阅候选逐字节一致；仅用容器dpkg-query及Docker cp -L导出文件、Windows PowerShell/.NET哈希替换容器Python审计，SDK版本/六头文件/Host库身份门禁保持。原脚本备份evidence/Build-CpuAdapter.before-no-container-python-20261006.ps1，旧失败目录/测试包/manifest未改；构建记录新增实际脚本哈希。PowerShell语法0错误，未执行Docker/编译/板端测试。用户下一步直接按CPU-ADAPTER-COMMANDS.md B，复用实际包.local/pose-v1-cpu-adapter/package/20261005，显式新标签cpu-adapter-20261006-r1；不重做A，不覆盖旧目录。回传build.log/sdk-audit.json/build-result.json经核对后再C。CPU/NPU前向仍未通过；下述“修正待批准/生效脚本未改”为批准前历史，不能将应用修正当作构建通过。证据evidence/cpu-adapter-build-fix-applied-20261006.json。

- CPU候选构建反馈（2026-10-06）：用户已生成107用例测试包，实际路径.local/pose-v1-cpu-adapter/package/20261005；代理只读核对282项哈希、18正常/89拒绝用例、22份参考输出及5份源码/构建副本匹配。用户构建在SDK身份核验的docker exec FPAI python3步骤退出127，当前容器PATH找不到python3，尚未进入CMake/C++编译，没有CPU运行/NPU验收。原失败目录完整保留；候选CPU-ADAPTER-BUILD-FIX-20261006.md拟以Docker导出文件及Windows PowerShell/.NET哈希取代容器Python，保留全部SDK门禁、不安装依赖。候选脚本/补丁已准备、语法0错误，生效Build-CpuAdapter.ps1未改，未操作Docker/SSH/编译或测试。应用修正及用户新标签cpu-adapter-20261006-r1构建待批准；不重做/回写现有测试包或覆盖旧证据。下述“尚未生成”为交付时历史状态，候选算子前向仍未通过。

- CPU算子最小适配源码交付（2026-10-05）：用户明确批准CPU注册与最小适配方案，已新增隔离的host_cpu_adapter模块、独立检查器及tools/pose-v1/CPU-ADAPTER-COMMANDS.md。仅应用侧显式注册TopK/GatherElements/ScatterND，禁止覆盖既有条目，Gather保持原实现；限定当前ZG图的FP32规格、Host内存与全有效分布，仅清除临时内核描述的冗余分布。设计107用例/22份正常输出，尚未生成测试包、编译或运行，不能称为注册/数值通过。Python AST及PowerShell语法检查通过，板端shell为LF；原推理检查器/CMake及固定模型哈希保持。用户执行准备、交叉编译、传输和Lite CPU测试，代理审查日志；先A/B构建核验，再C实板测试，失败保存证据停止，不自动改SDK/模型/缓冲区策略。未接入正式推理器、不补CPU Matmul、无Session/Device::Open/NPU/DMA/HDMI；全CPU参考及完整mixed门检仍待解决，后续接入方案另行讨论。入口CPU-ADAPTER.md、REFERENCES.md 18.6及evidence/cpu-adapter-source-delivery-20261005.json。此前“新增算子方案未批准”为历史阶段状态，不扩展本次批准范围。

- 独立CPU注册探针验收（2026-10-05）：用户批准HOST-REGISTRY-PROBE-PLAN.md，代理按特殊问题权限完成FPAI GCC9.4/CMake3.24.2、ARM Icraft3.39.0交叉编译和Lite一次30秒受限注册查询。探针退出码0、stderr空、5项回传哈希通过；optimized op1 Matmul无init/forward注册；ZG六个Host计算节点中188/437 TopK、192 GatherElements、582/649 ScatterND也无注册，只有442 Gather有注册。全CPU参考及混合图PS部分均存在当前注册阻断，停止mixed，不把注册查询完成当成前向/NPU/数值验收。结果tools/pose-v1/HOST-REGISTRY-RESULTS-20261005.md及evidence/host-registry-20261005/review.json；探针SHA256 4106daf64086e478b7540788eab52d4551680cb11f8b8b104a4f582d86d6d05c。原核心源码/推理二进制/模型/SDK未改，无Session/Device::Open/RAW/算子前向。后续官方注册机制核对可读资料；加载插件、改链接/SDK/模型或新增算子实现等方案及执行须先讨论批准，不自动修复或重试。

- Host库只读审计完成（2026-10-05）：用户新增特殊问题代理直接工具协助权限并批准审计，代理SSH确认Icraft/CustomOp均arm64 3.39.0，dpkg -V icraft:arm64无差异、退出码0；Host库SHA256 d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130与原始onchip包一致，CMake导出含CudaDefault，readelf可用。完整日志tools/pose-v1/evidence/board-host-library-audit-20261005.stdout.log及同前缀记录，原包静态审查original-arm-host-package-review-20261005.json。未执行模型/设备初始化或修复，不能据库完整性认定Matmul支持；独立CPU注册探针HOST-REGISTRY-PROBE-PLAN.md为未批准候选，编译/运行及后续修复仍先讨论。口令仅用于SSH认证，不写项目文件/日志。

- Lite Host绑定失败已定位（2026-10-05）：用户日志显示Session::Create<HostBackend>/bindToBackendsByOrder在op_id=1 MatmulNode绑定检查失败；mode=host/device_init_allowed=false，输入已验证、lazyLoadParamsFromFile返回后failed_stop_no_retry，尚未执行样本前向。内核尾部未见本次OOM、available 687 MiB；不能凭此宣布ARM平台全面不支持或NPU混合路线失败。深层原因待实际库身份/依赖/注册审查；本机文档CPU支持不等于板端支持，安装CustomOp也不能直接证明标准Matmul注册。保持暂停重跑/模型或SDK修改/mixed，下一步只读审计候选待批准。审查tools/pose-v1/HOST-BINDING-REVIEW-20261005.md，截图evidence/lite-host-binding-failure-20261005-1.png至-3.png；软件仍用户执行。

- Lite Host执行未通过（2026-10-05，更新下述尚未运行状态）：用户执行一次已批准的300秒Host参考后截图退出码1；具体失败阶段和原因待stdout/stderr、stages/run-config/failure及内核日志复核，不能凭退出码判断OOM、算子缺失或模型问题。证据tools/pose-v1/evidence/lite-host-exit1-20261005.png。暂停重跑、覆盖输出、数值比较及mixed；只由用户保存/读取本次诊断，代理分析。任何修复/新路线先讨论批准，不自动改模型、依赖、Swap或SDK配置。未验收Host数值/NPU/双路，ORT解析/安装仍未批准。

- Lite Host资源前检复核（2026-10-05）：用户截图显示总内存993 MiB、available 744 MiB、Swap 0，/tmp所在根文件系统剩余47G；可见进程未见明显其他推理/视频用户应用，host-reference-20261005前缀无旧文件。可由用户继续已批准的一次300秒Host参考，峰值内存/ARM算子/耗时仍未知；超时、OOM或算子异常即停止，不自动重试、加Swap或改线程/模型。Host尚未执行，不记为参考数值或NPU通过；ORT解析/安装仍未批准。证据tools/pose-v1/evidence/lite-host-resource-query-20261005-1.png及-2.png，命令LITE-HOST-COMMANDS.md第2步。

- Lite Host参考路线已批准（2026-10-05）：用户明确同意先用Lite Host作参考，本阶段F2改为Lite ARM，复用已校验二进制d1006f9b…c05e5及optimized图/三份固定参考张量，不新增依赖/编译或调用Device::Open；先用户查询资源并交回，再按批准的300秒Host运行范围执行、回传完整输出/Host回调及哈希。命令`tools/pose-v1/LITE-HOST-COMMANDS.md`，范围REFERENCE-NEXT-PLAN.md。Host尚未运行，ARM支持/内存/耗时及数值待验证，不是全CPU部署降级或NPU通过；ONNX Runtime解析/安装本轮未获批准，仍暂停，mixed须参考数值有效后推进。原Windows Host方案因SDK未识别保留，不自动修复。代理只编写/审查及记录，软件命令由用户执行。

- Windows Host SDK未识别（2026-10-05，更新下述窗口待查询）：用户回原开发CMD后cl/x64/VSINSTALLDIR及CMake3.31.6-msvc6均确认可用；WindowsSdkDir未设置、WindowsSDKVersion仅反斜杠，有效SDK未识别。代理只读检查4个厂商Windows v10.0登记入口与5个常见目录均未找到，不能排除其他未登记目录；F2不构建、不手填INCLUDE/LIB/安装/修复。证据`tools/pose-v1/evidence/windows-host-sdk-query-20261005.png`。已准备`REFERENCE-NEXT-PLAN.md`讨论B复用已编译Lite host模式作为数值参考、A后续完善Windows SDK；另独立Conda CPU ORT1.23.2仅dry-run依赖预览，两项未批准/执行。CPU参考不是部署降级，不改变正式NPU/双路要求，输出误差仍须讨论；不因现有host模式可用静态结论就自行执行或跳过参考进入mixed。

- Windows Host查询窗口已澄清（2026-10-05）：自动定位路径后用户已显示VS开发终端横幅，另一截图where cl未找到、架构/SDK变量未设置；用户随后明确查询是在另开的CMD执行，其未继承原开发终端环境，不据此认定原窗口初始化失败/SDK缺失/安装损坏。代理只读确认start/parse/winsdk/vcvars脚本存在，横幅v17.0为vswhere缺失时的默认值，不作版本或编译验收。现在由用户回原初始化窗口查询，原窗口环境及SDK仍待验证；暂停F2及依赖它的mixed，不自动补PATH/安装/修复。证据`tools/pose-v1/evidence/windows-host-banner-20261005.png`及`windows-host-unset-query-20261005.png`，命令说明WINDOWS-HOST-ENV-CHECK.md。

- Windows Host工具文件已定位（2026-10-05）：用户不确定C++工具安装情况，代理只读找到`D:\Visual Studio\ Visual Studio 2022\Community`，第二层目录名开头有一个空格；含MSVC14.44.35207的Hostx64/x64 cl/link/nmake、C++头文件与库、VsDevCmd.bat及CMake文件元数据3.31.6-msvc6。不再把普通PATH查不到解释为机器没有工具；这不是实际启动、SDK完整、CMake VS实例发现或编译通过。默认vswhere及常见Windows Kits注册表入口未找到/未返回记录，不自动修复/重装。用户查询命令`tools/pose-v1/WINDOWS-HOST-ENV-CHECK.md`，证据`evidence/windows-host-tool-discovery-20261005.json`；仅用户临时进入x64开发CMD及查询环境，错误先提交，不编译/安装/切换生成器或运行模型。ORT缺失保持，F1/F2参考及mixed尚未执行。

- E初始化探测复核通过（2026-10-05，更新下述日志待复核）：用户提交完整probe产物及日志截图，阶段started→opening_device_not_readonly→probe_complete_requires_review，mode=probe/device_init_allowed=true，无failure.json，stderr为空；stdout报告Device initialization successful，AXI zg330aiu/NPU=0x40000000/DMA=0x80000000，device=25122301、icore=FMSHZGV3TECH-AID - 24160628。结合退出码0，E仅Open/version初始化探测通过；提供的dmesg尾部未见探测相关总线/DMA错误，启动时EXT4恢复、journal异常关闭/更换及其他启动提示保留，不归因于probe，不自动修复或改时间。未执行模型、六Host算子/NPU计算或数值/性能验收；compatibility_passed=false固定待验收标记保持。证据`tools/pose-v1/evidence/board-probe-review-20261005-1.png`至`-3.png`。下一步准备F1/F2参考，ORT缺失与Windows Host编译工具待确认；参考有效前不进入mixed，不自动安装依赖或转为全CPU部署。

- E探测执行反馈（2026-10-05，更新下述未执行状态）：用户实际执行固定30秒timeout的probe，退出码0，device-version.json的device=25122301，与基线一致；icore已显示、待文本日志复核，已保存probe.dmesg.log但内容未提交。compatibility_passed=false是检查器固定输出的待验收标记，不是SDK兼容性失败结论。stdout/stderr、stages/run-config及内核日志仍待复核，E尚未完整验收；不重跑probe或覆盖证据，不进入mixed。此结果证明本次Device::Open/version返回，不能扩大为DMA/NPU计算、完整模型、HDMI或RTSP通过。证据`tools/pose-v1/evidence/board-probe-exit0-20261005.png`；软件操作由用户执行，代理未连接SSH或初始化设备。

- E前置查询反馈（2026-10-05）：用户截图确认/usr/bin/timeout为GNU coreutils 8.30，probe及三份对应日志均不存在；可见进程列表未见明显AI/HDMI/编码用户应用，方括号kbase/mvx等内核线程不能据名称认定为故障或演示占用。截图不独立证明当前位流未改变或所有访问方均空闲；仍需用户确认上次0x25122301核验后未替换BOOT/通过JTAG加载其他位流、无其他演示使用设备，再进入既定E。未执行probe，不自动停止进程、重启或初始化。证据`tools/pose-v1/evidence/board-probe-preflight-20261005-1.png`及`-2.png`。

- D阶段离线接口验收（2026-10-05，更新下述产物待复核）：用户提交inspect-zg产物截图，输入[1,180,60]、分数[1,100]、姿态[1,100,14,3]及顺序符合检查器float32门禁，阶段started→offline_inspection_complete，mode=inspect/device_init_allowed=false，stderr为空且目录无failure.json。结合前述11项校验和退出码0，D阶段通过；未加载RAW参数、执行推理或调用Device::Open。证据`tools/pose-v1/evidence/board-inspect-artifacts-20261005.png`。E前仍须确认GNU timeout可用、无AI/显示并发占用且BOOT未再改变，用户执行软件命令；不因离线通过认定NPU兼容或双路显示通过，不自行终止进程、复位设备或重跑覆盖已有目录。

- 板端包校验更新（2026-10-05，覆盖下述CRLF阻断状态）：用户以`files.lf.sha256`校验11项全部OK、退出码0，板端样本/模型包完整性通过；随后运行ZG图`inspect`退出码0。截图尚未展示graph-io.json、stages.jsonl、run-config.json及stderr，离线接口验收待这些产物复核，不重跑已有inspect或覆盖目录。未进入SDK设备初始化或推理。证据`tools/pose-v1/evidence/board-checksum-inspect-exit0-20261005.png`；当前仅板端清单换行处理已由用户执行，生产打包脚本的候选修正仍未应用，不把截图当作代理修改脚本的授权。

- 板端校验清单CRLF阻断（2026-10-05）：用户D截图确认二进制哈希匹配、ldd列出的依赖均解析；sha256sum对11文件报尾随`\r`的No such file。代理只读确认本地files.sha256为11行CRLF，原因是inference_gate.py默认文本换行写入；不是已证明的哈希不一致或文件丢失。仅准备`tools/pose-v1/checksum-lf.candidate.patch`及`CRLF-CHECKSUM-FIX.md`，生产脚本和现有包未改，修正待批准；用户保留旧清单并生成LF清单后重新校验，全部OK前不继续inspect/probe/mixed。无需因此重编译、替换模型、安装SDK或改BOOT；后续软件操作由用户执行。

- 独立检查器交叉编译复核（2026-10-05，更新此前未编译状态）：用户完成三样本包及FPAI构建`inference-20261005-165059-043b0c40`，GCC9.4.0/CMake3.24.2、SDK目录`/usr/cmake`，配置/编译/链接通过；AArch64 PIE二进制SHA256 d1006f9bd78050ffa484c64bf74fb62542d270c7acca5068e9da611a5bdc05e5。代理只读核对源码记录7/7、包文件大小/哈希11/11、二进制哈希与日志匹配，未代执行构建或软件测试。现在由用户执行D传输、板端库解析及inspect离线检查，交回结果后再继续；尚未确认板端加载、SDK设备初始化或推理，不安装/改库/自动进入probe。证据`tools/pose-v1/evidence/cross-build-review-20261005.json`，命令`INFERENCE-COMMANDS.md`。

- 推理SDK补查确认（2026-10-05，更新先前“ZG330配置未找到”）：用户截图确认`/usr/cmake`含HostBackend/ZG330Backend配置及aarch64导出，包文件清单包含ZG330后端头文件、设备头文件、后端so与AIU库；FPAI icraft/customop均arm64 3.39.0，icraftmdzthirdparty arm64 0.1.1，状态均install ok installed。可继续已批准B固定打包、C用户交叉编译，SDK目录用`/usr/cmake`；不据此声明编译/运行兼容性或NPU通过，不因此前搜索缺项自动安装后端。ORT缺失、Windows工具当前PATH不可见仍待讨论；先提交构建日志复核，不自动进入设备执行。详细见`tools/pose-v1/ENVIRONMENT-QUERY-20261005.md`及新增截图证据。

- 推理环境查询反馈（2026-10-05，用户截图）：FPAI GCC9.4.0/CMake3.24.2/Icraft arm64 3.39.0已查询确认；SDK精确文件名搜索仅返回`/usr/cmake/icraft-hostbackend-config.cmake`，ZG330配置未找到，不等于已确诊NPU运行库缺失。独立Conda NumPy可找到、ORT未找到；Windows正确Get-Command cmake,cl无输出，只证明当前PATH不可见。原`*icraft*`查询不核验CustomOp，需补查包内容、实际后端命名及CustomOp状态；当前不执行构建/设备初始化，不自行安装或更换参考执行环境。见`tools/pose-v1/ENVIRONMENT-QUERY-20261005.md`及截图证据；后续软件命令仍由用户执行。

- HDMI配套资料补充（2026-10-05，用户确认）：用户没有另行持有的Lite25122301可编辑工程或720p60说明；参考包README/构建/API及示例配置检索未找到明确归属当前位流的720p60配置步骤，不能推断全部资料不存在。手册/原理图的720p建议不等于当前位流配置方法；HDMI时钟、寄存器及工程对应仍待核对，不自行配置或改首版目标。

- 独立混合推理门检准备（2026-10-05）：用户批准下一阶段方向，已编写2024 epoch442三样本的独立Icraft检查器、可选SDK CMake目标、FPAI交叉编译脚本、固定样本/模型打包、ONNX参考及数值比较工具，执行入口为`tools/pose-v1/INFERENCE-COMMANDS.md`。代理本轮仅编辑源码、静态审查和读取资料，未编译/测试/运行模型、操作Docker/SSH或初始化设备；实际软件/AI操作由用户执行。SDK CMake实际目录、Windows Host参考编译工具、ONNX Runtime依赖尚待用户查询；不自行安装。设备probe不是只读操作，probe结果需复核后再继续混合推理；六个Host算子执行与ZG330后端回调须记录，分数/坐标容限仍待实测讨论，不把退出成功或源码交付记为推理通过。HDMI静态审查发现参考RTL可写时序项，但当前25122301位流与这份工程、像素时钟及寄存器配套尚未确认，见`HDMI-STATIC-AUDIT.md`；720p60目标保持，未访问显示硬件或修改FPGA/BOOT。此前最小只读探测授权不扩大为任意硬件操作。

- 首版阻断项最新状态（2026-10-04，更新早期“位流未知/预处理门检未通过”）：用户批准固定9组300份真实回放与幅度atol/rtol=1e-6、相位周期最大1e-5 rad门检，原3份样本包含其中；主机及Lite与Windows参考均300/300逐位一致，实板/主机哈希一致，幅度及相位标量/周期最大差0，4类非法记录拒绝。人工±π按明确批准降为非阻断诊断，周期最大2.333111/2.693437 rad仍失败，不能标为通过；真实相位标量差>1e-5 rad仍须暂停依赖它的推理验收并讨论模型影响。原预处理、模型及ARM二进制未改。板端BOOT哈希与用户指定Lite 25122301单路PLIN+pHDMI包一致，仅BOOT变更，其余8文件保持旧身份；日志FSBL已下载PL、Linux启动，uEnv后续download.bit加载未确认，未修复启动配置。BOOT内载荷经32位字节序转换与同包.bit完整载荷对应，另有4字节尾随。用户随后明确批准最小只读映射，仅读取0x4000001C得到0x25122301，运行FPGA版本身份已核验；该授权不扩展为任意寄存器、SDK Open/reset/check或推理/显示。板端Icraft/CustomOp实测arm64 3.39.0，参考包标3.36.0，混合推理兼容性仍待实际门检；HDMI参考1080p60，包装器不设置720p时序，首版720p60保持，屏幕尚未连接。NPU/HDMI/VPU/RTSP/30分钟闭环未验收。最新见`tools/pose-v1/RESULTS-300.md`、`evidence/replay-300-summary.json`、`NEXT-GATE.md`及REFERENCES.md 18.4；后续初始化、模型/显示执行仍按既有审批及配套停止条件处理，不能因版本相符认定首版已完成。

- 分化零衰减10轮完成验收（2026-10-04 13:06，更新下述启动快照）：`tpami2026_diff_nodecay_20261004`于12:00:59完成10轮/28,110步并停止，监督/torchrun/4rank退出、GPU空闲。10次7824帧评估/四卡检查、563条有限诊断、134份当前源码/快照及配置哈希、最佳/最终权重及优化器有限性/元数据/分组/SHA256通过；最佳epoch6=344.787402826mm，epoch10=377.942666765mm。分化L2保留1.908233679，但第6轮15351步首次抽检分化/细化注意力梯度同时0，第7–10轮全部抽检均0；参数不归零不等于细化学习有效，现有范数门禁没有检测持续零梯度。最佳权重服务器`best_mpjpe_epoch_6.pth`，SHA256 4fb71e4a604cb064ec11a6d7de52a3190cd44ad1dc1d58c3a135bce947276def；最终SHA256 50a5ffa2b7e9e45dd6ac5d1797fe5af91f35203360b3fed772b812a9f9ac975d。前5轮同轮有改善也有退步，不能宣称稳定增益。结果见`tools/pose26-diff-nodecay/20261004/RESULTS.md`和evidence/completion-verification.json。实验已结束，禁止重复启动/自动延长/改门禁；后续排查和新技术方案先讨论批准。用户暂不监测及ID26暂停保持，未开展模型部署。

- 零衰减对照交付前快照（2026-10-04 10:25:28）：下述新10轮实验仍stage=training，第1轮1701步，分化L2=1.719859849，分化/细化注意力梯度和残差非零；无已记录错误、无完整评估，不能称为精度改善、10轮完成或已越过原第6轮退化点。最新只读快照`tools/pose26-diff-nodecay/20261004/evidence/progress-latest.json`，10:21:30第251步是此前启动核验。

- 分化分支零衰减10轮对照（2026-10-04，当前训练上下文）：用户批准上一轮建议的仅关闭Differentiation Branch衰减对照，已新增独立`opera/models/tpami2026_diff_nodecay.py`、配置`configs/wifi/petr_wifi_tpami2026_diff_nodecay.py`及`tools/pose26_diff_nodecay`；只有`bbox_head.transformer.joint_differentiators.`的56份权重/偏置wd=0，Refine Decoder、坐标回归及其他参数仍wd1e-4。保持全新初始化、Adam lr2e-5/betas(.9,.999)/eps1e-8、GPU1–4/每卡batch8/worker4、FP32 seed0 clip0.1、原模型/初始化/数据/损失和异常门禁；固定10轮后停止讨论。单项零梯度参数逐元素不变/索引/梯度及4卡96样本3步门检通过；旧129份源码未变，新正式134份源码/快照/配置哈希通过。10:20:27正式启动，监督70223、torchrun70234、rank70239–70242，操作前重新核对身份；10:21:30第251步分化L2=1.564861、梯度非零且记录有限，首轮评估尚未完成，不能宣称精度改善或10轮验收。结果`result/tpami2026_diff_nodecay_20261004`，优先查pipeline-status/诊断/评估；禁止重复启动、自动改配置/重试/延长。用户暂不监测及ID26暂停保持。本轮零衰减不覆盖整条细化路径，也不是重新启动旧500轮。入口`tools/pose26-diff-nodecay/20261004/README.md`、Done.md、REFERENCES.md 17.3。

- 500轮实验异常停止验收（2026-10-04 09:08检查，更新启动快照）：`tpami2026_scratch_20261004`实际于01:40:51在第6轮末触发`RuntimeError: Persistent branch collapse`自动停止，stage=failed_stopped，监督/torchrun/4个rank均退出，GPU空闲；500轮未完成，仅5轮完整7824帧评估，最佳第4轮420.189946174mm，最新第5轮438.772183994mm。分化L2第5轮7.30e-21，第6轮16851步约7.44e-38，分化/细化注意力梯度及分化残差为0；338条诊断有限，退化非已记录的NaN/Inf。最佳epoch4/iter11244权重有限，SHA256 eaec533377d8098dab8fa35e6104c5330840fc7d0be0658ffdc669a794213361，129份源码/快照及配置哈希通过；无final-report。Z盘本次不可读，已通过SSH取证，不把挂载问题作为失败原因。未重启/改参数/启用监测，用户暂不监测及ID26暂停保持；后续分析形成修复/新实验须先讨论批准。最新证据见`tools/pose26-scratch/20261004/STATUS-20261004-0908.md`及同目录evidence/check-20261004-0906；下述运行快照为历史状态。

- 500轮启动后快照（2026-10-04）：新`tpami2026_scratch_20261004`第1轮2811训练步已完成、四卡一致性通过，正在首轮评估，精度尚待核验。首轮末分化L2=0.003813、细化注意力L2=51.173392，有限但从初始化快速下降；未触发既有严重趋零门禁，不静默改参数。用户暂不启用定时监测的选择保持，证据见`tools/pose26-scratch/20261004/evidence/first-epoch-training.json`。

- 2026姿态500轮全新训练（2026-10-04，最新运行上下文）：用户明确改为从头500epoch并选择论文Adam配方A。新模块`opera/models/tpami2026_scratch.py`绕过迁移，模型/优化器全新初始化，不加载旧权重；保留已核对的STE、14残差分化、3层vanilla refine及近零初始化，只做14关节。单项/索引/梯度/无checkpoint及4卡96样本3步门检通过；129份源码/快照与配置哈希通过。00:41正式启动GPU1–4、每卡batch8/worker4、FP32 seed0 clip0.1，Adam统一lr2e-5/wd1e-4无衰减排除，step450/gamma0.1，固定500轮。结果`result/tpami2026_scratch_20261004`；监督/torchrun PID54209/54220，rank54225–54228，操作前重新核对身份。已超过500步，不代表完成/精度通过；分化L2已由1.357降至0.016，快速缩小但尚未触发既有严重趋零门禁。用户明确暂不启用定时监测，ID26保持暂停，不自行启用。禁止重复启动、自动改参数/重试/延长。此前恢复10轮到100轮建议未执行，旧10轮结果保留。入口及证据见`tools/pose26-scratch/20261004/README.md`、Done.md、REFERENCES.md 17.2。

- 2026姿态迁移10轮验收（2026-10-03，更新上述启动状态）：23:42已完成10轮/28,110步并停止，训练进程退出。最佳第9轮122.873803893mm，较24版123.085352129mm降低0.211548236mm；第10轮124.680599441mm。10轮评估、四卡一致性、563条有限诊断、源码/快照/配置及最佳/最终权重哈希通过；最佳权重在`.local/pose26-training/20261003/best_mpjpe_epoch_9.pth`，SHA256 b567aa16e3e46be88cd9187cdc3af7d46085800d0c3df94a8404ae377d8bcca7。单/双人略退步、三人改善；最佳轮细化仍增加约0.0783mm，不能将0.212mm微小改善视为稳定提升或分化贡献。当前训练已结束，禁止重复启动/自动延长；后续实验或部署先讨论批准。完整逐关节表及证据见`tools/pose26-transfer/20261003/RESULTS.md`、Done.md和REFERENCES.md第17节。

- 2026姿态迁移训练（2026-10-03，最新算法上下文）：用户明确批准`tools/pose26-transfer/20261003`方案并实施。`ssh gpu-server`、`/public/cyd/Person-in-WiFi-3D-repo`（映射`Z:\Person-in-WiFi-3D-repo`）已实际连接和执行；Python为`/home/ubuntu/miniconda3/envs/PersonInWIFI/bin/python`，与koala及Lite板端SSH不同。新隔离模块迁移24版epoch442的169个张量，新STE、14个残差分化分支、三层vanilla refine及新优化器；分化所有Linear权重/偏置随机近零std0.001，整个细化器正常初始化，坐标末层零初始化；只做14关节，不加mesh/SMPL。单项索引/梯度/迁移门检、4卡短程与恢复通过，24版7824帧复评123.085352129mm。正式GPU1–4、每卡batch8/worker4、FP32、AdamW分组lr2e-6/2e-5、clip0.1、seed0、固定10轮已启动，**启动不等于完成或精度达标**。新结果`result/tpami2026_transfer_20261003`，最新查`pipeline-status.json`、`evaluations.jsonl`、`final-report.json`；禁止重复启动，10轮后停止讨论，不自动延长。旧代码/权重/结果保留；后续方案和超参数变更仍须先讨论批准。见REFERENCES.md第17节、Done.md及上述目录README/PAPER_AUDIT。

- 首版系统实施（2026-10-04）：用户已批准PS原始CSI回放预处理→PS/NPU混合推理→单人14关节固定三维视角→HDMI＋H.264 RTSP；采用2024 epoch442，NPU与双路均须验收，≥5Hz/争取10Hz、板端画面P95≤500ms、播放器延迟另测。新增`software/pose_v1`与`tools/pose-v1`；用户明确授权Conda验证环境，位于当前worktree `.local/pose-v1-conda`，Python3.10.21/NumPy2.2.5/h5py3.16.0/PyWavelets1.8.0，使用缓存离线完成，不绑定koala或更改既有环境。已完成启动分区9文件与镜像哈希一致审计、GCC9.4 arm64交叉编译及真实Lite纯预处理数值测试；3份真实CSI在主机/板端float32张量逐位一致，约5.70–5.78ms/样本，四类非法记录拒绝。±π合成边界差异仍达6.2406，总体数值门检未通过、未放宽容限或修改展开规则。实际运行AI_MATE/HDMI配套仍未知，uEnv引用第二分区download.bit但先前根目录未找到，相关设备/寄存器访问已暂停，等待用户启动串口日志；不得替换BOOT/位流、尝试未确认的寄存器或全CPU/电脑推理替代。FPAI实际SDK/CustomOp为arm64 3.39.0，原挂载`D:\FPGACompetitionProject`，本次构建源码明确从当前worktree复制到容器临时目录。尚未实现/验收板端TCP服务、混合推理、绘图、HDMI/编码RTSP或30分钟闭环，不将回放发送端存在当作网络链路通过。用户要求已新建根目录`Logs`，实际日志未提供；证据见REFERENCES.md第18节、Done.md与tools/pose-v1/evidence。后续安装/启动配置/模型/FPGA变更仍先讨论批准。
- 参考触发器：遇到比赛要求、悟净 Lite 硬件、Procise/Icraft 工具链、AI 部署、FPGA 开发或系统联调问题时，先查阅根目录 `REFERENCES.md`，再按其中索引核对原始资料。
- 26版训练定时检查（2026-10-03，已结束）：用户确认每10分钟检查当前10轮实验，仅在完成/失败/异常或需处理时通知。当前聊天heartbeat“检查26版姿态迁移训练结果”ID=26已完成监测；10轮结果、权重/源码哈希、四卡检查和曲线已核验，项目记录已补全并通知。随后通过应用工具停用，配置读回为PAUSED，证据见`tools/pose26-transfer/20261003/evidence/automation-stop.json`、MONITOR.md及monitor-state.json。未延长、重启或改变训练参数，未归档聊天或更改其他自动化；此前ACTIVE及首次22:27检查记录为历史状态。后续训练方案仍须讨论批准。
- 歧义处理：在理解或执行过程中遇到任何模糊、不清晰、资料矛盾或缺失的地方，及时向用户提出并讨论，不自行决断；暂停依赖该结论的操作，可继续不受影响的阅读和整理，并记录用户确认结果。
- 决策与执行审批：根据分析结论形成的决策，必须在执行前与用户讨论并取得明确同意；任何认为重大的项目、技术决策及其执行也必须先讨论并取得同意。讨论时说明结论依据、拟采取的操作、影响与尚存的不确定性；未获同意不得执行依赖该决策的操作，不能把排查授权、用户沉默或笼统意向当作对后续修复、配置变更或实施方案的同意。
- **资料与日志直接读取权限（2026-10-06，用户明确授权）**：为加快开发进度，代理有权主动定位并直接查看开发与排查所需的各类文件，包括资料、源码、回传日志、报错信息及板子的日志等；无需逐个文件再次要求用户提供或取得读取同意，可通过已授权工具或连接只读获取并分析。代理应自行核对现有文件和证据，向用户说明结论及依据；涉及文件修改、程序执行、设备操作或重大项目/技术变更时，继续遵循既有分工、决策审批与阶段停止条件。
- **软件与AI分工（2026-10-05）**：为增强用户的项目理解和技术水平，一般情况下软件与AI方向的实际操作由用户执行，包括本机/交叉编译、软件测试、Icraft模型转换、板端推理、相关文件传输与部署，以及Docker或SSH中的对应项目命令。代理负责核心源码、构建配置、测试代码和脚本的编写、维护与审查，并分析执行结果；特殊问题按下述例外规范处理。
- **特殊问题协助例外（2026-10-05，用户明确授权）**：遇到工具链、运行时、板端联调等特殊问题时，代理可以直接接入并调用相关工具，帮助用户排查和解决问题，不再一律要求用户代执行相关命令。代理应说明操作目的、范围、过程、结果及证据，帮助用户理解。该例外调整执行方，不取消既有决策与执行审批、歧义处理及阶段停止条件；根据排查结论形成的修复方案、重大技术决策和配置变更仍须先讨论并取得同意，不把排查授权扩展为未批准的安装、模型或启动配置修改。
- **FPGA分工**：FPGA方向的仿真、综合、布局布线、时序检查、位流生成及下载上板由代理执行，包括通过Procise/Vivado及其MCP进行相关操作、读取日志、检查报告、查看和分析波形。具体工程方案、下载目标、下载方式及配置影响仍遵循既有决策审批规范；代理说明执行过程、结果及证据，帮助用户理解。
- **命令交付要求**：对于用户负责执行的操作，代理提供具体命令，注明执行位置、工作目录和必要前置条件，逐条解释目的、关键参数、预期产物、通过标准及失败停止条件。未确认的路径、版本或参数及时讨论，不自行填入。用户执行后，代理依据日志和产物核验，不将命令准备完成写成执行通过。
- **边界与权限衔接**：代理可读取资料、审查源码、编辑已授权文件和分析已有日志。涉及软件/AI与FPGA的混合脚本应拆分执行职责；边界不清时先讨论。历史自动执行授权不作为后续代执行软件/AI操作的依据；本次用户明确授权的“特殊问题协助例外”持续适用，其他例外须由用户明确授权。工具命令示例保留供对应执行方参考。
- 关键决策分析：面对用户提到的关键决策，必须以中立、客观的视角进行分析，不偏颇、不谄媚，一切以客观事实和可行性为准；区分已验证事实、推断与未知项，说明方案的适用条件、收益、成本及限制，不因迎合用户偏好而预设结论。
- 完成工作记录：每次完成项目开发或验证后，将对应工作写入根目录 `Done.md`，统一使用“工程内容总结＋对后续开发的参考”模板。工程内容总结应记录目标、平台/工具版本、实现内容、验证结果与证据路径；后续开发参考应说明可复用方法、适用条件和限制。已有同一工作的记录时优先补全、更新，避免重复；严格区分已完成、待验证和用户现场确认，不将分析或计划写成已完成成果。
- 当前基线：悟净开发板 Lite；Icraft 3.39.0；Procise 来自 `FMSH_Procise_2025.1.1_temp_202603201420_32494.exe`；板载镜像为 `icraft_v3_ubuntu20.04_aarch64_sd_image.bin`。参考位流尚未确定，不能自行选定；用户已确认 `Docs/开发板手册/JFMQL30TAI_LITE.pdf` 是 30TAI 配套原理图，查阅 `REFERENCES.md` B4 获取页码和引脚依据。MIPI BANK12 电平及 GPIO 网络名/BANK 对应仍存在资料冲突，相关接线或约束须先讨论核对，不自行决断。
- FPGA 平台规范：本项目以复旦微 Procise 为开发与实现目标；参考 Vivado/Xilinx 工程时可以借鉴 RTL、接口和设计方法，但必须核对复旦微器件、封装/BANK、原语、IP、时序库、约束转换、位流及调试工具的适配。Vivado 的器件识别、仿真或报告不能替代 Procise 的实现/位流/时序和实板验收；不得直接采用未经适配的 Xilinx IP、位流或底层假设。
- 已验证硬件状态（用户报告，2026-09-30）：Lite 已在无 SD 卡情况下完成开机和连线上板测试，使用 Alinx 黑金下载器，Procise 与 Vivado 均可识别芯片；不再将下载器连接/器件识别列为尚未验证。此结果不自动证明 Linux 启动、特定位流功能、DDR/AI 或模型已验证。
- SD 启动最新状态（用户现场确认，2026-10-02；2026-10-03 补充板端查询/分区表）：用户已更换 SD 卡、完成 SD 启动卡制作和上板验证；串口正常输出信息，能够登录板载 Linux 系统。当前新卡的基本 SD 启动/串口登录已通过，不再作为待验证项；此前校验失败、启动文件异常及 H2testw 严重错误的记录属于旧卡历史，不能套用于新卡，也不能据换卡后启动成功追溯确诊旧卡的精确故障。用户截图已确认根设备 /dev/mmcblk0p2、ext4、rw,relatime，mmcblk0=58.3G、p1=1G、p2=26.1G，根文件系统约26G；resize2fs/sfdisk 存在，growpart 未找到。sfdisk=2.34，DOS/MBR ID=0x370deffb，总122167296个512字节扇区；p1 start/size/type=2048/2097152/e，p2=2101248/54687500/83。新卡品牌/型号、全容量、启动组件哈希和板端 runtime 版本未核验；成功登录不等于全容量、AI/模型或系统分区扩容已验证。用户选择扩大系统分区，明确要求代理仅提供具体命令和逐条说明，实际扩容由用户在悟净 Lite 已启动的板载 Ubuntu 中通过串口执行。已形成备份/预演→sfdisk只扩大p2末尾→重启→resize2fs的逐条说明，目标p2长度120066048扇区（约57.25GiB）；这些为待用户执行步骤，未扩容/验收，未验证内核在线扩容支持。最新记录见 REFERENCES.md 第15节/15.1/15.2、Done.md 和 tools\sd-image-validation\20261002-new-card-board-confirmation.json，具体命令见同目录20261003-expand-root-COMMANDS.md。
- 原生 FPGA 测试（2026-10-01）：用户已批准 `FPGA\lite_led_chaser` 独立流水灯方案、XSim 2019.1 纯 RTL 行为仿真、Procise 全流程及生成位流后直接 JTAG 易失配置下载，并批准 StartupClk=JtagClk 修正；本次仿真、原生综合/布局布线/内部时序、位流复核和下载已完成，用户现场确认“四颗 LED 按预期循环”，全流程功能验收通过。总结见 `Done.md`，入口和证据见 `FPGA\lite_led_chaser\README.md`、`REFERENCES.md` 第 13 节；不能将其扩展为 Flash/BOOT 更新、AI 系统或 MCP 全流程已验收。本次流水灯未使用 MCP；后续接入状态见 MCP 基线相关条目。
- SD扩容后续验收（2026-10-03，更新前述“待用户执行/未扩容”状态）：用户已在板载Ubuntu串口终端执行并明确确认扩容成功，最终截图显示内核p2长度120066048个512字节扇区、根/dev/mmcblk0p2 ext4 rw,relatime；resize2fs 1.45.5完成在线扩容至15008256个4KiB块，与分区字节数一致。lsblk p2约57.3G，df根容量57G、已用6.3G、可用48G、使用率12%。本次分区/根文件系统扩容由用户执行并以截图验收通过，代理只核对和记录；无全容量写读、resize后额外重启或长期稳定性证据，不能扩大为AI/runtime验收。最新结果见Done.md同一工作补充、REFERENCES.md 15.3、tools\sd-image-validation\20261003-expansion-success.png和结构化记录。此前待执行文字为命令准备阶段的历史状态。
- MCP 与 Vivado 辅助基线（2026-10-01，初始接入历史状态；最新见当前聊天衔接验收）：用户同意优先讨论 Procise MCP，并将 Vivado MCP 用于仿真和参考工程辅助；用户已自行接入 `vivado-mcp`，本会话已发现工具且成功调用只读 `list_sessions`，返回无活跃会话，尚未通过 MCP 启动 Vivado 或运行仿真。Vivado 以现有 **2019.1** 为准，安装入口 `D:\Xilinx\Vivado\2019.1\bin\vivado.bat`；资料中使用 Vivado 2018 版的项目仅作思路参考，不将 2018 作为当前执行基线，不因旧工程的版本说明要求用户安装 2018 或自行升级/迁移工程与 IP。对 Procise MCP 的方向认可属于讨论范围，开发、安装和配置变更仍须先明确方案并获同意；已有 Vivado MCP 的辅助调用不能替代 Procise 原生实现与实板验收。
- MCP 首版后续验证（2026-10-01，首版阶段历史状态；最新见当前聊天衔接验收）：用户明确批准首版、独立 SDK `mcp==2.2.0`、项目配置写入、复核日志编码适配/复验，以及 Vivado 临时启动捕获和仅子进程 AMD64 验证。`tools\procise_mcp` 七工具真实 stdio 客户端通过；首版阶段作业 `build_20261001_170101_78f11a` 用 MCP 新仿真完成复核，未下载。`.codex\config.toml` 已写入，Codex CLI 已读取；用户选择“暂不重载”，当前聊天 Procise 工具发现/调用待后续验收，不自行重载。Vivado MCP 的 XPR 解析/原 XML 核对、独立客户端和当前聊天临时修正后的 2019.1 会话、错误恢复、经现有脚本执行的 XSim 均通过。当前聊天原先两个架构变量为空，厂商启动器默认选择不存在的 32 位程序；仅给测试子进程设 PROCESSOR_ARCHITECTURE=AMD64 后通过，测试会话已关闭，永久环境/安装及生效 Vivado 配置未改；长期修复仍须讨论批准。第三方工具 `[ERROR]` 正文可能伴随 `isError=false`，须同时核对正文/rc/产物。`ReviewBuild.py` 已批准支持 UTF-8/UTF-16 BOM 日志，批准脚本哈希已更新，不据此回写原上板记录。入口与证据见 `tools\mcp-validation\RESULTS.md`、`tools\procise_mcp\README.md` 和 `REFERENCES.md` 第 14 节。首版无任意 Tcl/JTAG/Flash，不承诺取消或重启恢复；超时不等于底层作业已取消。
- 项目目标：基于 Wi-Fi CSI（信道状态信息）实现 3D 人体姿态建模；滤波降噪、部分算子加速、高速 DMA、HDMI 骨架显示只是当前候选方向，不代表全部必须实现，不自行把候选项扩展为必做任务。用户要求当前将采集接口/格式、模型和算法规格留空，后续顶层架构设计时再讨论；不自行填入，不在当前阶段继续要求用户确定这些内容。
- 开发与训练环境（用户说明，2026-10-01）：本机为 Windows 10，用户倾向方案 A，即 Procise 与 Icraft 保留在 Windows；当前算法训练在远程 Ubuntu 服务器上进行，其文件目录已挂载到本机 `Z:`。本机另有双系统 Ubuntu，但不能据此把当前训练位置写成本机 Ubuntu。`Z:` 挂载只表明文件访问入口，不能据此认定 SSH、远程执行或服务器软件环境已经验证；具体项目目录与比赛核心模型仍待后续讨论。用户随后明确批准 Windows Icraft 独立依赖目录、两个官方 ZIP、启动器及第一阶段加载验证；该阶段已通过，见 `REFERENCES.md` I5。其余安装、配置、迁移与模型/设备操作仍遵循决策审批规范。
- 非项目环境边界：`koala` 及其训练模型与本次比赛项目无关。此前借用其中的 Windows CUDA DLL 仅用于经批准的临时诊断；不得将其模型、Python/PyTorch/CUDA 版本或训练设置作为本项目基线，也不得据此擅自把 Icraft 的长期运行绑定到该环境。
- Icraft 独立调用入口：第一阶段验证已通过，可在已授权任务中调用 `tools\Invoke-Icraft.ps1`，例如 `& 'D:\FPGACompetitionProject\tools\Invoke-Icraft.ps1' -IcraftArgs @('run', '--help')`。独立依赖位于 `.local\icraft-runtime\cuda-11.8.0`；启动器只给子进程补 PATH，并固定 Icraft 3.39.0、校验 DLL 哈希、保留日志。调用说明见 `tools\README.md`，验证证据见该依赖目录的 `verification-report.json`。不得将加载/帮助通过视为模型、GPU 或实板功能通过，也不得因启动器存在而推定模型编译/部署操作已获授权。
- 工具下载：用户确认本机没有 Vivado 2018.3，下载工作由用户负责；不得自行执行 Vivado 下载。当前辅助版本已确定为 2019.1，2018 版资料仅作思路参考；若后续出现确实依赖其他版本的新需求，先说明证据并讨论，不自行下载或升级参考工程/IP。

- Vivado MCP 长期配置（2026-10-01，配置写入时状态；后续重载验收见下一条）：用户本轮明确要求实施此前讨论的长期方案，已仅在 `C:\Users\cenyongdong\.codex\config.toml` 的 `[mcp_servers.vivado.env]` 增加 `PROCESSOR_ARCHITECTURE = "AMD64"`，其他配置逐字节保留，备份与证据见 `tools\mcp-validation\vivado-permanent-config-change.json`。读取 Codex 实际解析配置的新 stdio MCP 进程已验证：无需临时启动器，直接启动 Vivado 2019.1 并回读 AMD64，通过后已关闭测试会话。已有聊天 Vivado MCP 进程尚未重启，不能宣称已加载新配置；新启动/重启后才生效。此授权不扩展为系统环境、EDA 安装或 Procise 重载；Procise 仍按用户选择暂不重载。结果见 `REFERENCES.md` 14.1 和 `tools\mcp-validation\RESULTS.md`。

- 当前聊天 MCP 衔接验收（2026-10-01，位流阶段历史状态；后续上板见下一条）：用户已重载 Procise/Vivado MCP，并明确批准 `tools\mcp-validation\led1324\PLAN.md`。当前聊天 Procise 七工具均已调用通过；Vivado 2019.1 直接使用长期配置启动并回读 AMD64，无临时启动器。已先备份旧 RTL/testbench 至 `FPGA\lite_led_chaser\revisions\led_1234_before_1324`，通过 Vivado MCP 写入 LED1→3→2→4 新源码并驱动 XSim 自检，再经 Procise MCP 完成原生综合/布局布线/位流及复核；最新 `build_20261001_183334_5f3fc1` 对应 `sim_20261001_182621_aa641e`，内部 setup/hold 5.962/0.192 ns、违例端点 0，五引脚/电平、29 INIT、JtagClk、源码哈希和原报告对照通过。完整证据见 `tools\mcp-validation\led1324\RESULTS.md`、`REFERENCES.md` 14.2 和 `Done.md`。本轮批准止于位流复核，新位流未下载、未实板观察；旧 LED1→2→3→4 上板确认不得扩展到新灯序。构建/仿真/复核脚本、MCP 服务及配置未改；首版仍只支持当前流水灯工程，无任意 Tcl/JTAG/Flash、取消或重启恢复。遇到新工程/IP/接口或扩大工具范围仍须讨论批准，不因本次通过自动扩展授权。

- 新灯序上板验收（2026-10-01，更新前述“未上板”阶段状态）：用户随后明确要求下载新位流，已复核 `build_20261001_183334_5f3fc1` 的位流/源码/仿真哈希及当前 JTAG 链，用既有 `Program.ps1` 经 Procise 原生下载到 `jfmql30` part 0；位流 SHA-256 `285356540f63f5b1a150827777f8e5e411843718976590db0cb39739b5ef7c18`，2026-10-01 18:50（北京时间）完成，STAT=`0x40007ffc`。用户现场确认“灯序和速度均符合预期”，新 LED1→3→2→4→1 的实板功能验收通过。下载是 FPGA 易失配置，未写 Flash/BOOT；无仪器周期测量或整份配置读回。入口见 `REFERENCES.md` 14.3、`tools\mcp-validation\led1324\RESULTS.md`、新构建的 `jtag_20261001_184939\program-result.json` 和 `Done.md`。下载环节用原生工具，Procise MCP 服务/七工具未改，不能宣称 MCP JTAG 已验证；旧灯序记录仍保留。此授权仅覆盖本次明确的新位流，后续扩大功能、配置或写 Flash 等操作仍须讨论批准。

- 真实 IP 源码交接实板验收（2026-10-01）：用户明确批准 `tools\mcp-validation\ip-reuse\PLAN.md` 的 xlconcat 最小方案。独立 `FPGA\lite_led_ip_bridge` 已用当前聊天 Vivado 2019.1 MCP 生成真实 xlconcat 2.1 Rev.3（四个 1-bit 输入）、写入 RTL/testbench、以同一综合包装器/厂商 HDL 通过 16 种组合及分频 1/7/19 各 200 周期 XSim；随后用 Procise 原生批处理完成综合/布局布线/位流复核及 JTAG 易失下载。`build_20261001_193157_bef06d` 对应 `sim_20261001_193106_688cd5`，setup/hold=5.962/0.192 ns、违例 0，五引脚、电平、29 INIT、全部 HDL/XCI 哈希和 JtagClk 通过；位流 SHA-256 `00c833bb65fec1573ecf0a8cf59c45c50cff76ab7f0a3398696c43be4f608c56`，19:34 下载至 jfmql30 part 0，STAT=0x40007ffc。用户确认“灯序、速度和单灯状态均符合预期”。Vivado checkpoint=0，synth/impl run 未启动，全部综合在 Procise；当前 Procise MCP 仍固定旧工程，本次未扩展服务或配置。仅证明这个无器件原语依赖的明文组合 IP/具体配置能交接；不能推广到加密源码、FIFO/BRAM/Clocking/DSP、DMA、HDMI 或 AXI 系统，也不能以 MCP 替代适配。原工程和记录保留，无 Flash/BOOT；详细结果见 `REFERENCES.md` 14.4、`tools\mcp-validation\ip-reuse\RESULTS.md` 和 `Done.md`。后续 IP/工程/工具扩展仍须先讨论批准。

- 板端网络/Icraft与Docker交叉编译最新进度（用户确认，2026-10-03）：悟净Lite已通过SD启动，网线连接主机，用户已在MobaXterm通过SSH进行开发和通信；已将 `D:\Dowload from Chrome\嵌赛资料\Icraft\Icraft_V3.39.0安装包\30TAI&100TAI\30TAI&100TAI` 中的板端Icraft及CustomOp传输到板上并完成安装。本机Docker交叉编译环境已搭建、相关工具链已配置，用户明确 `FPAI` 是**容器名**，不是已确认的镜像名。代理只读核对本地安装包control：两份onchip包均为arm64/3.39.0，两份amd64包均为amd64/3.39.0；这不是板端或容器已安装软件的独立版本查询。板端实际包版本/路径、SSH地址、容器镜像身份/编译器/sysroot及“交叉编译→板端运行”尚未核验，不自行填写或据安装完成认定AI/runtime/参考位流配套和模型推理通过。板端SSH与远程Ubuntu训练服务器是不同对象，不能混用；当前训练位置和Windows Procise/Icraft基线保持此前用户说明。记录见 `REFERENCES.md` 第16节、`Done.md`、`tools\development-environment\20261003-progress.json`。本次进度同步不扩展为代理连接SSH、操作Docker、安装/部署或执行新的板端任务授权。

## 本机工具路径与调用方法

以下路径于 2026-10-01 核对。命令示例使用 Windows PowerShell；带引号的可执行文件路径须用 `&` 调用。构建目录、Tcl/TOML、模型和输入文件必须换成已确认的实际文件；下面的 `example`、`path_to_confirm` 均为占位示例，本次未创建这些目录或执行构建。详细资料索引见 `REFERENCES.md` 第 5、6 节。

### Procise：FPGA 主开发工具

| 用途 | 本机路径 |
| --- | --- |
| 安装根目录 | `C:\FudanMicro\Procise` |
| GUI 启动器 | `C:\FudanMicro\Procise\procise_launch.exe` |
| Shell 启动器 | `C:\FudanMicro\Procise\procise_sh_launch.exe` |
| Tcl 执行程序 | `C:\FudanMicro\Procise\bin\procise.exe` |
| 编程下载工具程序 | `C:\FudanMicro\Procise\bin\procise_jtag.exe` |
| 用户/约束/IP 等手册 | `C:\FudanMicro\Procise\documents` |
| Tcl 命令查找线索 | `C:\FudanMicro\Procise\conf\commands_*.xml` |

按需要选择一个启动器：

```powershell
& 'C:\FudanMicro\Procise\procise_launch.exe'
& 'C:\FudanMicro\Procise\procise_sh_launch.exe'
```

在 **Procise Shell 的 Tcl 提示符**中执行脚本，可使用 `source {D:/fpga_work/example/build.tcl}`；这不是 PowerShell 命令。工程路径不支持中文，后续需要构建工作副本时，按既有歧义处理规范先讨论路径布局并记录源码来源。

直接批处理调用 `bin\procise.exe` 时，需要为当前进程配置运行环境。下例依据本机手册及参考区 `FPGA_LED_Wujing_Full\build.ps1` 的调用方式整理；该参考工程是历史脚本依据，不能直接复用其板级引脚约束：

```powershell
$prociseRoot = 'C:\FudanMicro\Procise'
$prociseBuildDir = 'D:\fpga_work\example' # 替换为已确认、已存在的工作目录
$env:PATH = (Join-Path $prociseRoot 'dll') + ';' + $env:PATH
$env:APP_DIR = $prociseRoot
$env:TCL_LIBRARY = Join-Path $prociseRoot 'tcl8.4'
$env:ICTIME_HOME = $prociseRoot
$env:FMSH_DB = Join-Path $prociseRoot 'db'
$prociseJob = Start-Process `
    -FilePath (Join-Path $prociseRoot 'bin\procise.exe') `
    -ArgumentList 'build.tcl' `
    -WorkingDirectory $prociseBuildDir `
    -WindowStyle Hidden -PassThru -Wait `
    -RedirectStandardOutput (Join-Path $prociseBuildDir 'procise.stdout.log') `
    -RedirectStandardError (Join-Path $prociseBuildDir 'procise.stderr.log')
if ($prociseJob.ExitCode -ne 0) { throw 'Procise 返回失败，请检查构建日志。' }
```

这里修改的是当前 PowerShell 进程及其子进程的环境，不是系统永久环境。`build.tcl` 应位于工作目录；退出码还须结合日志、预期产物及报告检查，不能只凭退出码或位流存在宣布实现/时序通过。

原生 Procise **简单 RTL 工程**的 Tcl 流程示例（文件和顶层均为占位）：

```tcl
create_project -name example -device JFMQL30TAI676H
add_design_file -file example_top.v example_top.fdc
set_top -top example_top
save_project
load_design -stage_elaborate -no_hier
launch_run -stage bitstream
exit
```

- `save_project` 会将运行目录切换到 `rundir`；预期位流和报告应按实际脚本/工程设置查找，并保留日志。跨不同工程时，手册建议重新启动 Procise Shell。
- 本次实测 `launch_run` 完成后返回工程根目录；后续重新 `bitgen` 前须显式切换到 `rundir`，防止同名文件写到不同目录。流水灯脚本已按批准方案处理，`ReviewBuild.py` 核对最终报告、INIT、引脚、电平及文件哈希；当前已确认的 ASCII 工程目录是 `D:\FPGACompetitionProject\FPGA\lite_led_chaser`。
- Procise 使用 `launch_run -stage ...`；不能直接套用 Vivado 的 `launch_runs` 或 `vivado -mode batch -source ...`。上例也不能替代含 PS/AI、BD、网表或 JFM 迁移步骤的系统工程流程；这类工程须先查 `REFERENCES.md` D1–D5，再核对 IP、约束和专用步骤。
- 下载与在线调试按本机《编程下载工具使用手册》《Procise在线调试手册》操作。Alinx 下载器已能识别芯片，但品牌名称不能直接推定 Tcl 的 `cable_type` 参数；使用前核对工具实际识别结果。
- 本次实测 Alinx 下载器显示为 `DIGILENT/JTAG-HS1`，序列号 `210512180081`；当前 Procise 的 `init_chain` 接受 `-cable_type usb-jtag-hs1`，大写显示名返回参数错误。链中 `jfmql30` 为 part 0（IDCODE `0x9372c093`），`ps_dap` 为 part 1。已验证 `program_bit {已复核位流绝对路径} -part 0` 与 `read_reg -part 0 -reg STAT -read`；重连、换板/下载器或链变化时须重新扫链核对，不能永久假设目标总为 0。

### Icraft：AI 模型编译与运行工具

| 用途 | 本机路径 |
| --- | --- |
| 安装根目录 | `C:\Icraft` |
| 当前版本目录 | `C:\Icraft\CLI v3.39.0` |
| 当前版本链接 | `C:\Icraft\CLI`（本机符号链接指向 `CLI v3.39.0`） |
| CLI 程序 | `C:\Icraft\CLI v3.39.0\bin\icraft.exe` |
| 组件与组合命令配置 | `C:\Icraft\CLI v3.39.0\bin`、其中的 `comb.toml` |
| 本地文档 | `C:\Icraft\CLI v3.39.0\docs` |
| 自定义算子资料 | `C:\Icraft\CustomOp_v3.39.0` |

优先明确版本目录，并把该版本 `bin` 放到当前进程 PATH 首部：CLI 会通过 PATH 查找 `icraft-parse` 等子程序，仅写主程序绝对路径仍不足以保证子程序版本一致。初始化、版本和帮助查询：

```powershell
$icraftRoot = 'C:\Icraft\CLI v3.39.0'
$icraftBin = Join-Path $icraftRoot 'bin'
$icraftExe = Join-Path $icraftBin 'icraft.exe'
$env:PATH = $icraftBin + ';' + $env:PATH
& $icraftExe --version
& $icraftExe --help
& $icraftExe parse --help # 其他组件可用 optimize/quantize/adapt/generate/run 等替换
& $icraftExe docs         # 按需要打开本地文档
```

本次实际查询得到 Icraft `3.39.0`、CLI `3.39.0.0-431be90(2608211646)`；`Get-Command icraft` 当前也指向 `C:\Icraft\CLI\bin\icraft.exe`。后续应重新查询，不能假设链接/PATH 永远不变；不要通过带版本参数的 `--version` 调用擅自切换已确认基线。

命令格式为 `icraft <command> [config.toml] [--key value] [--dry_run]`。TOML 须紧跟命令名；单组件读取与命令同名的小节，命令行同名参数覆盖配置文件。模型相关路径若为相对路径，应从配置约定的工程工作目录执行，而不能假设它们相对 TOML 所在目录。

模型、输入规格、校准数据和配置已讨论确定后，可使用以下方式；当前阶段不据此创建模型配置：

```powershell
Push-Location -LiteralPath 'D:\path_to_confirm\model_project'
try {
    $icraftConfig = '.\configs\model.toml' # 占位；替换为已核对的 TOML
    & $icraftExe compile $icraftConfig --dry_run # 先打印命令；不执行编译
    & $icraftExe compile $icraftConfig           # 完整编译
    # 分步诊断时依次使用以下命令，选择完整或分步流程即可：
    # & $icraftExe parse $icraftConfig
    # & $icraftExe optimize $icraftConfig
    # & $icraftExe quantize $icraftConfig
    # & $icraftExe adapt $icraftConfig
    # & $icraftExe generate $icraftConfig
    # & $icraftExe run $icraftConfig # 须另行核对 [run]、输入和后端/设备条件
} finally {
    Pop-Location
}
```

- 本机 `comb.toml` 确认 `compile` 顺序是 `parse → optimize → quantize → adapt → generate`。实际分步脚本须检查每一步退出码和日志，失败即停止，不继续使用旧产物。保留成对 JSON/RAW、TOML、工具版本及日志。
- 悟净 Lite/30TAI 查 ZHUGE/ZG330 文档；本机 `parse --help` 的默认 target 是 `Buyi`，因此必须显式核对配置中的 `target = "zhuge"` 及后续适配/生成参数。不得将图像示例的形状、预处理或量化参数直接用于 Wi-Fi CSI。
- `run` 的 Host 验证与 ZG330 实板运行需分别配置；板端运行时、位流、服务、设备地址及输入未确定时，只记录命令形式，不自行填入。帮助输出成功不代表模型编译或板端部署已验证。
- Icraft 警告诊断（2026-10-01）：CLI 与直接调用 `icraft-run.exe --help` 均出现 `nvfuser_codegen_ic.dll` 加载警告，帮助正常输出且退出码均为 0。被点名的 DLL 实际存在；PE 导入依赖链中 `torch_cuda_ic.dll` 需要 `cufft64_10.dll`、`cublas64_11.dll`，`cusolver64_11.dll` 还需要 `cublasLt64_11.dll`，这三者在 Icraft bin 与当前搜索路径中缺失；直接加载相关现有库返回错误 126。
- 经用户明确同意的临时验证（2026-10-01）：仅在独立子进程中将 Icraft 3.39.0 bin 和 `C:\Users\cenyongdong\miniconda3\envs\koala\Lib\site-packages\torch\lib` 依次放到 PATH 首部，再执行 `icraft run --help`。该 Conda 环境的 PyTorch 为 `2.1.2+cu118`，包含上述缺失库；加入路径后警告消失、stderr 为 0 字节、退出码为 0，帮助正文与原环境逐字节一致。由此确认当前警告与 CUDA 依赖库的可发现性有关；本次只验证帮助命令级加载，未验证模型、Host/CUDA 推理或实板兼容性，未实施长期修复。后续复制 DLL、永久修改 PATH、安装 CUDA、更换 Icraft/PyTorch 或采用长期启动配置，均须先讨论并获得用户明确同意；不得将此次临时验证的同意扩展为这些操作的授权。

命令依据：[Procise 用户使用手册](C:/FudanMicro/Procise/documents/Procise用户使用手册.pdf) 第四节；Icraft 本地 [CLI](<C:/Icraft/CLI v3.39.0/docs/cli/index.html>)、[编译](<C:/Icraft/CLI v3.39.0/docs/start/compilation.html>)、[命令行参数](<C:/Icraft/CLI v3.39.0/docs/interface/cli_arguments.html>)；以及版本/帮助查询和实测记录。Icraft 独立组件与启动器第一阶段验证见 `REFERENCES.md` I5；Procise 原 LED1→2→3→4 流水灯构建及 JTAG 下载见第 13 节和 `Done.md`。模型编译/推理与 AI 系统部署仍未验证；MCP 独立客户端、长期配置及当前聊天新灯序仿真→Procise 位流复核的状态见第 14 节、14.1、14.2。当前源码为 LED1→3→2→4，新位流随后经用户明确授权下载并通过实板观察，见 14.3。
