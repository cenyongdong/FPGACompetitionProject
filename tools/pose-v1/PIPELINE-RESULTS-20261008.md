# 真实推理→骨架→H.264有限接入结果（2026-10-08）

同一进程中的真实PS/NPU输出、CPU骨架绘图和VPU编码已完成两次有限成功运行，其中第二次是在一次显式内存规整诊断之后。无规整的新进程重复启动失败。因此，**有限接入与内容一致性已核验，启动稳定性尚未通过**，不升级为实时/在线RTSP或整机验收。

## 实现与冻结边界

新增隔离`pose_pipeline_encode_check`、`vpu_pipeline_encoder`及准备/构建/运行/独立核验工具。程序SHA256为`13693d45f9f124a287f84647fe87b3a8d2bc7d8204a4a08036afd01399f8f086`，350项包载荷、21份构建来源、15份ARM SDK头文件均核验。GCC9.4/CMake3.24.2/Icraft与CustomOp3.39.0保持。

原Engine、CPU数学、显式SDK复制、Gather/Matmul分工、模型/RAW/BOOT、旧VPU文件入口及RTSP回放源保持。每帧仍使用已验收的reset(1)状态清除、0起始和最终745；不使用reset(0)或直接寄存器。

新接口传递拥有NV12字节的帧，以及拥有码流字节的packet。输入先完成Host复制再QBUF；输出先复制为独立CPU容器再归还驱动，QUERYBUF opaque cookie保留。仍分配六个原始/六个capture缓冲区，仅启动时提交两个明确标记的NoInput画面；收到实际VPU capture之后再创建Engine。该次序避免把近29秒模型初始化计入原文件编码25秒期限。

producer各次调用限60秒，codec有效时间限25秒/停滞5秒，整个combined阶段仍由180秒外部timeout约束；记录暂停的producer时间，不将串行停顿改写成编码吞吐。当前PTS为离线名义10fps，不是实时采样时钟。

## 成功证据

| 项目 | 核验结果 |
| --- | --- |
| Host回归 | 107例、12注册、22输出/59,600 FP32逐位参考一致，六个接口拒绝路径通过 |
| 同一Engine前向 | 308/309/310/308回归四次，再生产四次；每次10,800输入与4,300输出逐位此前板端参考，共120,800有限FP32 |
| 绑定与完成状态 | 1173 HardOp由七ZG组完整追溯，六计算Host与Input回调保持，八次均0→745 |
| 画面来源 | 四个新结果（帧6/7/8/6），各重复一次；三个不同源画面不同，重复首帧PPM一致 |
| VPU | 十提交/十归还/LAST/STREAMOFF通过；前两帧NoInput不算推理结果；十份NV12逐位NumPy重算一致 |
| 所有权 | 十二capture chunks含参数集/空LAST，owned packet拼接逐位完整H264 |
| 两次成功对照 | 全部提交NV12及37,317字节H264逐字节相同，各88份哈希回传通过 |
| 系统 | 两次成功exit0、stderr空、各自dmesg前后相同，BOOT/SDK身份保持 |

H264 SHA256：`7a8fdb2ed9c1381506fe9a4f26f20a0c4bf619231f661e83aa8532dcd5fa7407`。
MP4 SHA256：`59cf1cef864baeb8525d6daed345832b2af06f8a403c84dd53dab2532a91124f`。
主机完整解码十帧ID0..9、112次关节可见性检查通过；720p/名义10fps/1秒，视频属于有意重复的离散窗口展示，不是连续动作录像或真实10Hz更新。

[真实推理接入MP4](evidence/pipeline-20261008-r6/combined/results/encoder/review.mp4) · [画面联系图](evidence/pipeline-20261008-r6/host-video-review/contact-sheet.png) · [汇总核验](evidence/pipeline-20261008-r6/completion-review.json)

## 历史失败与修正

| 修订/阶段 | 实际失败与处理 |
| --- | --- |
| r1 | 初始构建保留；未板测。新增强BOOT/XRT身份预检后使用新r2 |
| r2 Host | exit139，新全局Case类型与冻结Host检查器不同布局，却生成相同vector弱符号。新助手改入匿名namespace；原Host源未改，nm证据保留 |
| r3 Host | 60秒超时124，23例全通过。独立无设备图解析探针量到2447.24ms/次，原Host107需要约264秒；恢复既有300秒预算，不改计算或拒绝规则 |
| r4 combined | 七次正确前向后，VPU固件map_protocol_v2的order7连续页分配失败，capture0，清理STREAMOFF均0 |
| r5 combined | VPU先有实际输出，Engine初始化28.34秒，八前向均正确、内核无新增异常；文件入口25秒总期限误计producer初始化，退出1。r6分开有界producer/codec时钟 |
| r6初次combined | 八前向/十编码通过；Engine初始化28.71秒 |
| r6新进程重复 | 模型初始化前即同类order7分配失败，两个NoInput提交/capture0，无NPU前向，清理成功；无repeat acceptance |
| r6规整诊断后 | 同程序/包在新目录八前向/十编码通过；Engine初始化29.32秒，码流与首次逐位一致 |

全部旧目录、程序和失败内容保持，不将成功门禁复制改名为失败阶段验收。

## 当前内存难点

失败堆栈明确到`mvx_mmu_alloc_contiguous_pages`→`map_protocol_v2`→固件初始化，申请order7（4096×128=512 KiB）、GFP_KERNEL/NO_RETRY/ZERO。失败时系统仍有大量MemAvailable，没有OOM killer；不能解释为普通内存耗尽或CPU算子数值错误。失败堆栈的高阶空闲块与CMA标记支持连续内存碎片方向，但不证明驱动内部全部根因。

确认无AI/视频/RTSP工作进程后，仅一次`timeout --signal=TERM --kill-after=5s 30s sh -c 'echo 1 > /proc/sys/vm/compact_memory'`，完整记录进程、dmesg、buddyinfo、pagetypeinfo、meminfo和vmstat。退出0，用时约0.193秒，dmesg不变；Movable的order10块0→8，order7块2→27。随后一次新目录运行成功。该操作按[Linux官方说明](https://kernel.org/doc/html/v5.12/admin-guide/sysctl/vm.html#compact-memory)尝试将空闲内存集中成连续块，会影响全局内存状态；本轮是诊断，不是生产修复，未写持久sysctl、drop_caches、重启或替换固件。GFP_NORETRY的有限回收行为见[内存分配说明](https://kernel.org/doc/html/v5.12/core-api/memory-allocation.html)。

下一需捕获REQBUFS前后/STREAMON前后的页分布与实际缓冲占用，再确定应用初始化顺序或配套驱动修正；不只凭初始化前页数预检宣称随后分配必然成功。保持VPU上下文常驻可避免服务内重复初始化，但不能解决首次启动失败，需分别验证。

## 接续边界

详见[下一门检](PIPELINE-NEXT-20261008.md)。优先做无行为变化的分配时序取证；之后有依据地选择最小修正，再进行单Engine/单编码器常驻、有界画面队列与真实PTS。当前不静默规整、不自动重试；失败记录后停止。在线RTSP、27帧争用、整机5Hz/30分钟及HDMI1080p60尚未通过。SPS显式色彩仍另列；HDMIclock/scanout/停止协议缺证，未写入。
