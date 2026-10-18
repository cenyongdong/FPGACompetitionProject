# Wi-Fi 人体三维姿态项目技术实现汇报

状态同步：2026-10-18。已批准架构为PS＋NPU感知、PL本地HDMI与PC独立3D；r13三窗新推理→HDMI已通过，新应用未启动VPU／RTSP。D44首次reader与D45跨启动异常未解决，开发与上板整体暂停；PC历史回放独立完成，实时双路未联合验收。

| 现行主题 | 维护位置 |
|---|---|
| HDMI模块、CSR、帧所有权、工具适配与开发结果 | [INTEGRATION.md](../FPGA/hdmi_candidate/INTEGRATION.md) |
| 共享Engine、PS骨架渲染和RGB565显示应用 | [software/hdmi_demo](../software/hdmi_demo/README.md) |
| 难点处理与未证假设、最近实板暂停状态 | [DIFFICULTIES](../DIFFICULTIES.md)、[暂停汇报](../FPGA/hdmi_candidate/STARTUP-PAUSE-REPORT-20261018.md) |
| PC骨架协议与本机3D回放 | [software/pc_viewer](../software/pc_viewer/README.md) |

下文保留2026-10-13及此前VPU／RTSP演示的技术详录，旧流程中的“当前”“本轮”均指当时分支。其数学、输入和SDK资料仍按原范围使用；旧视频数据流与“HDMI未启用”不描述新HDMI应用。原演示源码位于[software/demo](../software/demo/README.md)，三／60窗口结果见[ADR_45](ADR_45.md)。

## 历史演示源码入口及2026-10-13重构回归

当前演示只使用[正式核心](../software/core/README.md)中的input/inference/diagnostics/display/video/stream，应用编排仍在software/demo。原pose_v1文件及测试保留作历史依据；新旧文件/导出别名/哈希见迁移映射原路径`tools/pose-v1/evidence/core-refactor-20261013-r1/source-migration.json`（当前文件缺失）。公共接口、数学、协议、SDK与固定模型保持。

2026-10-13实际完成11组本机检查、旧实现/原参考字节对照及ARM构建；Lite CPU107的22输出/59600 FP32逐位通过。新三窗口308/309/310全CSI/预处理/分数/姿态逐位旧参考，354编码、294主机GUI解码，全3来源及42关节核验；正常drain/LAST、两STREAMOFF和所有权回收通过，规整0、BOOT/SDK/内核相同。具体范围见[ADR_47](ADR_47.md)。下文2026-10-11三/60窗口数据仍是原独立演示证据，不累加成新的样本精度或吞吐验收。

## 1. 系统组成与数据流

```mermaid
flowchart LR
  A[主机预采CSI MAT目录] --> B[原始float64窗口回放]
  B -->|PIWCSI1 / TCP 39001| C[Lite PS完整窗口接收]
  C --> D[PS相位校正与token预处理]
  D --> E[Icraft PS/NPU混合Session]
  E --> F[100分数与100×14×3姿态]
  F -->|拥有值 / Unix域IPC| G[独立显示子进程]
  G --> H[RGB骨架与NV12]
  H --> I[常驻VPU H.264编码]
  I -->|拥有AU / 有界通道| J[live555 RTSP]
  J -->|RTSP/RTP over TCP 8554| K[主机FFmpeg解码 / OpenCV实时显示]
```

本机负责数据文件读取、原始数据回放和视频显示。CSI预处理、模型推理、候选选择、骨架投影和VPU编码均在Lite。没有使用主机推理替代板端，也没有将数据集GT叠加为预测。HDMI不进入该历史VPU演示路径；后续独立HDMI应用见文首。

Lite使用ARM64 Linux/Icraft3.39.0、ZG330架构NPU与MVX VPU。FPAI是已存在的交叉编译容器名；C++使用GNU++17，数学构建保留`-ffp-contract=off`。Docker负责构建，不在容器中模拟物理NPU成功。

## 2. 预采CSI输入与实时回放

演示读取`D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/data/wifipose/test_data/csi`。每份HDF5 MAT的`csi_out`是`[20,30,3,3]`，real/imag字段为float64。通过`transpose(3,2,1,0)`变为`[3 receiver,3 antenna,30 carrier,20 sample]`，保持原幅度与精度。

主机按文件名自然序读取，不读取keypoint文件。默认60窗口、2Hz，每个窗口20个时间样本；这模拟完整窗口到达，不宣称恢复原无线设备的真实采样时钟。源码调用既有公开`csi_io.load_mat/encode_window`，没有另写预处理或预测算法。

发送端以`perf_counter`的绝对计划时刻发送；明显迟到时停止，不以追帧突发掩盖调度延迟。帧号从1000000递增，源文件名与原帧名另存。源MAT/原始负载SHA256、实际发送时间和记录数保存，`sendall`成功仅代表发送完成，不等于板端已消费。

## 3. 传输契约、重组与输入所有权

一条PIWCSI1记录为32字节头＋86400字节负载。little-endian头含8字节magic、uint32版本1、uint32负载长度、uint64帧号、uint64发送端纳秒时间。负载为5400个复数的real/imag float64对。

板端按长度逐段`recv`，不把TCP分包边界当数据帧。非法magic/版本/长度、非有限数、中断记录和同会话非递增帧号拒绝。单待处理槽只能替换未开始的完整窗口；消费通过值转移，不让接收线程改写正在推理的窗口。

覆盖计数、收到/消费/返回、会话与拒绝分开记录。本版演示只建立一个输入会话，不自动重连或重发已接受的数据。完整记录到达时间取板端steady_clock；主机与板端时钟未同步，不能直接相减宣称端到端延迟。

依据：[原始协议](../software/pose_v1/PROTOCOL.md)、[接收源码](../software/core/input/tcp_receiver.cpp)。

## 4. PS端CSI预处理

输入是complex128，内部使用double计算，最后生成float32`[1,180,60]`。token顺序为receiver→antenna→time，每个token先30幅度，再30校正相位。

幅度分支对应训练db11小波处理。固定窗口只有20个样本、db11滤波长度22，训练的最大分解层为0，因此该规格下输出等于`abs(csi)`；这是对当前训练规格的精确实现，不推广为任意窗口可省略小波。

相位分支对首天线沿子载波unwrap；其他天线利用`arg(current × conj(previous))`及前一天线相位重建后unwrap，再按训练常数`2π×625`作线性校正。以训练等价的复指数重建并取arg回到包裹相位，保留零幅值和signed-zero行为，不能用表面等价的`atan2(m*sin,m*cos)`替换。

300个真实CSI窗口与训练方法逐位对照已通过；人工±π诊断的边界失败历史保留，不宣称所有人工输入的相位语义均已证明。源码与实测见[预处理](../software/core/input/preprocess.cpp)、[ADR_03](ADR_03.md)。

## 5. 模型转换、参数及输出接口

使用2024 epoch442 ONNX，Icraft ZG编译流程为parse→optimize→quantize→adapt→generate。公开apply后原1173个HardOp融合成七个ZG组9185–9191，按merge_from逐项唯一追溯原成员及后端绑定；不能将原ID变成零层误判为计算遗漏，也不重复autoMerge。初版多帧输出曾停留首帧，经完成计数观察改为安全帧边界reset(1)，而非重建Session；当前最终阈值745沿用。[融合与帧状态](ADR_05.md)。

部署保留配对JSON/RAW、真实参数和已有BOOT，既不更换模型也不以合成参数替代RAW内的K或ScatterND索引。

输入`[1,180,60]`；输出分数`[1,100]`和姿态`[1,100,14,3]`。模型每次产生100个候选，保存全部输出，然后以最高分槽选42个坐标显示；相同分数取最前槽。槽位只是输出位置，不能保证跨帧或跨ONNX/板端为同一身份。

坐标保持模型原始单位，不宣称米/毫米物理标定、多人匹配或MPJPE。当前展示单个最高分候选，没有增加NMS、置信阈值、时序平滑或GT辅助。

正式图SHA256：`75ffdc37b93dcb4913678991d6e7cf5cd0ab09c59653224d07c7434345acb8a0`；RAW：`3991a679282a4c6b014aece59b717910bc53fd14e67c0fac5fb9f93d4ae054d3`。

## 6. ScatterND不能在本图NPU分配时的处理

本图本来就是PS/NPU混合分工；解决方式是为缺失的CPU算子补应用侧注册与适配，保持已有NPU部分。不能把本图的实际支持情况推广为所有ZG型号/版本都不支持某算子。

| Host节点 | 实现方式 |
|---|---|
| TopK 188、437 | 显式应用注册，调用SDK common::topK |
| GatherElements 192 | 显式应用注册，调用SDK common::gatherElements |
| ScatterND 582、649 | 显式应用注册，调用SDK common::scatterND，仅当前reduction=NONE |
| Gather 442 | 保留SDK原注册与实现 |
| Matmul及其余HardOp | 保持NPU分配，未补全全CPU Matmul |

六个计算Host节点之外还记录Input节点0，因此运行日志Host回调为7，不能误称新增了第七个CPU计算算子。

Session创建前核对注册基线，发现已有或部分注册就停止，禁止覆盖SDK。初始化与forward回调直接编入程序，避免依赖CustomOp自动发现或仅设置`ICRAFT_CUSTOM_DIR`后假定成功。

CPU内核只支持当前图实际需要的FP32、轴、形状、K及索引形式。FP32表示的索引必须有限、精确整数、在边界内；不截断、取整、钳位或用晚值替换坏索引。原CPU107用例、12条注册记录、22输出/59600个FP32值独立参考通过，当前演示复用原数学实现，不把协议测试写成新Host107执行。

依据：[CPU适配](../software/core/inference/host_cpu_adapter.cpp)、[注册/桥](../software/core/inference/read_input_bridge.cpp)、[ADR_01](ADR_01.md)。

## 7. 布局和merged distribution适配

便携CPU内核拒绝带merged_distr的输入，而真实图有此声明。适配先核对轴合法、mask长度、每个有效位、FP32字节容量及当前row-major `*...C`布局。只有全有效的冗余分布声明，才在临时内核描述中去除，原模型声明不改。

没有开发通用去填充/重排；非全有效分布、拆分/packed布局等规格直接拒绝。输出保留原声明类型，SDK已提供输出缓冲区时必须逐项核对，禁止根据地址猜映射。原Gather仍由SDK实现，未把全部Host节点换成自定义内核。

## 8. PS/NPU内存交接与帧状态

设备ADDR/BOTH地址不当普通Linux指针直接解引用。桥核对dtype、region、chunk、offset、容量和所属Device，等待原SDK就绪条件后，通过公开`Tensor::read`写入SDK分配的自有Host CPTR，再执行CPU核。

CPU计算后，SDK提供目的输出时使用原`copyFrom`写回并setReady；没有提供输出时返回Host结果。Host输入及输出写回的SDK复制保持。此实现是有拥有值和明确边界的首版方案，仍有搬运/等待开销；没有完成真实指针映射或零拷贝。

同一Engine只由主线程创建、调用和销毁，异常后永久停止该Engine。每帧在安全边界沿已验证`reset(1)`协议清除状态，forward前计数0，最终745后读取完整输出。SDK profiling关闭，计时使用steady_clock。特定生产组/中间计数（例如192的234）及ready状态不是已证明的DDR写完成fence。

全CPU参考曾因Host Matmul缺注册停止，后以独立ONNX Runtime CPU环境直接对照板端，不将Matmul改到CPU部署。见[ADR_04](ADR_04.md)、[ADR_30](ADR_30.md)。

## 9. 线程、进程与有界队列

推理Engine保留在父主线程。SDK无关显示子进程在设备与工作线程建立之前exec，用Unix域socket和明确包头接收100分数/4200坐标，返回拥有NV12字节；单请求信用1，子进程不继承使用SDK/VPU对象。

显示结果队列容量2，编码画面队列容量2；仅未消费数据可覆盖，计数分开。编码线程独占一个VPU上下文，在10fps时隙采用最新画面，无新结果时显式重复，错过时隙不突发补帧。网络线程独占live555事件循环，不从推理或编码线程调用其对象。

AU通道容量8，以非阻塞self-pipe唤醒事件循环。满队列属于错误，不能任意丢P帧继续发送而破坏解码参考。发布前取得字节所有权，队列只表达数据契约，不暴露功能模块私有状态。

依据：[显示协议](../software/core/display/display_protocol.hpp)、[AU通道](../software/core/stream/access_unit_channel.cpp)、[ADR_09](ADR_09.md)、[ADR_15](ADR_15.md)。

## 10. 3D骨架如何变为可编码画面

使用固定正交显示：中心(1.75,1.75,3.4)、yaw30°、elevation20°、显示C2翻转、220像素/模型单位。投影只用于显示，不修改模型坐标。画布1280×720，绘制14关节、源码固定的14条骨连接、坐标辅助线、分数/帧号/状态面板。

RGB以CPU线段/点/文字光栅化生成，再用BT.601 limited-range整数矩阵生成Y以及2×2平均色度UV，输出连续NV12。编码小标记记录独立encoded_id，配合来源清单区分启动、真实结果和重复；它不是姿态标签。

渲染、RGB565/NV12/NV21已通过Native/ARM/NumPy位级核验。H264有损解码不要求RGB逐位相等；通过投影关节可见性、来源/ID、PTS和图像差异评估内容映射。SPS色彩信号未完整显式标定，不能把输入矩阵等同码流已声明BT.601。

依据：[渲染源码](../software/core/display/skeleton_render.cpp)、[ADR_06](ADR_06.md)。

## 11. 板端VPU H.264编码

通过`/dev/video0` V4L2 M2M的MPLANE接口协商：raw VIDEO_OUTPUT_MPLANE/NV12，coded VIDEO_CAPTURE_MPLANE/H264。本机实际raw两plane、stride1280；coded一plane。保持720p、10fps目标、2Mbps、Baseline及真实读回，而非直接套参考代码的单平面CAPTURE配置。

两端各请求并实际返回两个MMAP缓冲，映射总量约6.64MiB；从旧六缓冲约19.9MiB降低，改善但没有保证任意碎片条件首次启动。编码输入从拥有NV12复制到驱动缓冲；capture内容先复制为拥有packet，才归还驱动。

QUERYBUF返回的opaque cookie须按已验兼容方式用于QBUF，不能将看似offset的字段重新构造。早期误用触发MMU abort；cookie保留修正经有限重复码流逐位与动态骨架验证。驱动内部页表根因未完全证明，兼容修正不推广为所有V4L2驱动规则。

正常结束执行STOP/drain/LAST、归还全部raw缓冲和两STREAMOFF，再解除映射与close。异常执行abort STREAMOFF，不能将异常默认summary中的0计数当实际无编码，不能把前缀解码当正常drain通过。

依据：[VPU实现](../software/core/video/timed_resident_encoder.cpp)、[ADR_02](ADR_02.md)、[ADR_07](ADR_07.md)。

## 12. 渲染视频怎样推回主机

VPU实际Annex-B packet进入AU解析器，保存真实SPS/PPS和单slice图片合同；参数集、IDR及PTS由真实码流取得，不硬编码SPS/PPS。每个AU拥有slice字节，记录capture时间与VPU PTS后通过通道交给网络线程。

live555提供`rtsp://192.168.126.49:8554/pose`。DESCRIBE返回实际参数集，SETUP/PLAY建立H264 RTP，单slice大NAL按RTP分片规则交付。展示客户端使用RTSP/RTP interleaved TCP；RTP时钟90kHz，实际PTS差用于时间映射，不按推理帧号生成伪10fps时间。

客户端从可解码IDR加入，关闭时回收source。发送缓冲申请64KiB、Linux实际读回128KiB，错误由厂商库公共发送回调传播，全局停止慢/失败peer；保活和TEARDOWN/重连在此前独立RTSP门检验证过。旧未接guarded的程序不能回填这些保护结论。

主机OpenCV调用已有FFmpeg后端，用TCP拉取板端RTSP，显示实际解码画面；不把保存好的本机视频冒充实时回传。编码目标10fps与真实新姿态2Hz分别报告，重复画面不是更高推理吞吐。

依据：[网络实现](../software/core/stream/timed_guarded_rtsp.cpp)、[AU解析](../software/core/stream/h264_access_unit.cpp)、[ADR_08](ADR_08.md)、[ADR_10](ADR_10.md)。

## 13. 常驻与启动顺序

单演示进程内保留一个编码上下文和同一个Engine，窗口切换/重复画面不重新REQBUFS或重建Session。先实际VPU capture，再主线程创建Engine；SDK初始化限60秒。此处“常驻”是该有界生命周期，未安装长期systemd服务。

结束顺序为停输入生产→显示完成→编码drain→AU关闭及网络回收→workers join→保存证据→Engine销毁。异常则通知所有队列停止，保留首次Host错误/两轮晚源，清理自己的子进程与端口，不自动重新打开设备。

## 14. 为什么内存充足仍可能启动失败

已确认MVX固件存在order7、512KiB普通连续页申请；对应分配标志没有__GFP_MOVABLE。现有256MiB CMA空闲不能直接当该普通申请可用，扩大CMA还可能减少普通不可移动范围，因此尚未改内核/CMA/BOOT。

MemAvailable只是总体可用量，不表示有512KiB连续普通页。工程记录buddyinfo/pagetypeinfo/meminfo/vmstat和dmesg，区分CMA与Unmovable/Movable/Reclaimable高阶块。代理可按授权规整并记录前后/耗时，但规整无效即停止，不循环申请或清缓存绕过。

本轮演示首次启动前普通512KiB单位1，规整39.27594ms后仍1；VPU固件分配失败、Engine未创建。新门检会在资源仍不足时设备打开前拒绝。16单位为策略余量，非驱动保证；真正安全连续申请/永久首次启动仍待，不以一次重启成功替代可靠性验收。

## 15. 精度、性能与未解决数据问题

CPU107/59600值通过；原三帧、27样本和多轮2Hz全链逐位板端参考已有通过证据。独立 `.local/pose-v1-onnx-conda` 使用Python3.10.21、NumPy2.2.5、onnxruntime1.23.2 CPU wheel，依赖版本/下载哈希及环境报告保存；CPUExecutionProvider、顺序执行、线程数1、ORT_ENABLE_ALL，生成完整100候选输出。27样本部署数值阶段已由用户批准，保留同槽误差、最高分候选切换及身份未证明的限制；不是GT/MPJPE验收。

短期纯处理曾达平均190.60146ms/5.24655Hz；它不含整机全链。显示子进程后整机测量仍有4.99164849Hz，严格≥5Hz不能舍入判过。关闭SDK profiling后用单steady_clock分解等待/CPU/复制/显示/编码/网络跨度；异步跨度不是纯NPU时间，可见复制约0.47ms也不是后端总搬运上界。

高负载已出现首Host索引或更新值残留前一个输入的数据。本批独立ZG生产组inv94的DATA96全同上一B，INDEX正确，两轮四物理晚源读94080字节全正确；首次拥有指纹与错误文件一致，但指纹在保存后记录，缺早期即时采样。原文件未修补。它不能归因于ScatterND数学内核，也不能凭晚源正确认定缓存根因；生产完成、首次SDK/DMA读和Host存储责任仍待。

用户当前要求暂停该排查，演示保留异常保护。2Hz演示成功也不能宣布高负载根因已修、严格5Hz/30分钟/零拷贝通过。依据：[ADR_01](ADR_01.md)、[ADR_14](ADR_14.md)、[ADR_30](ADR_30.md)、[ADR_44](ADR_44.md)。

## 16. 本轮演示源码与验收状态

软件位于software/demo；CMake锁定实际框架来源与别名、15 SDK头和189厂商头/库，构建输出新目录，旧源码/二进制/失败均不覆盖。模型/大码流/返回原字节留本机并以SHA清单绑定，提交保留源码和文本证据。

实际验证的ARM程序SHA256为 `82201e97547504ccd0c883191dbbb9e05957e378a77de0cbda5006c6f5d987e0`，构建 `.local/pose-v1-build/demo-20261011-r5`，成功运行及回传证据为 `tools/pose-v1/evidence/demo-20261011-r4`。Native/ARM TCP七拒绝、所有权/碎片重组/断连/重复/闲置合同通过；旧CPU107数学与12注册/59600值身份复用，本轮未重新执行Host107。

| 实测项目 | 短阶段 | 默认演示 |
|---|---:|---:|
| 真实CSI接收/消费/输出 | 3/3/3 | 60/60/60 |
| 不同姿态输出 | 3 | 60 |
| 编码/原码流离线解码图像 | 352 | 637 |
| 主机实际RTSP GUI解码 | 292 | 577 |
| 主机完整覆盖真实来源 | 3 | 60 |
| 投影关节可见性核验 | 42 | 840 |
| 含初始化的运行时长 | 36.50511秒 | 65.16524秒 |
| 成功阶段规整次数 | 0 | 0 |

两阶段共63次真实推理、989编码图像、869主机实时解码图像。主机加入码流前的启动图像不计丢失姿态；NoInput与重复不计新姿态吞吐。60窗口按2Hz完整回放，零待处理窗口覆盖。原H264逐帧ID有序，全部真实来源与本机同一冻结渲染器重建图像对应；有损解码的身体区域RGB平均绝对差分别1.64523/1.64924，不能理解为模型坐标误差。

308/309/310在两阶段均逐位匹配旧原始输入、预处理张量、全部100分数和4200姿态值；默认演示其他57份仅通过结构、有限性、最高分选择与视频来源/几何映射，没有完整精度验收。所有返回原字节已保存，不声称951300个保存FP32都具有独立数值参考。

最初VPU普通连续页失败保留；用户批准一次重启后仅执行一次，启动后BOOT/SDK/模型身份保持、FPGA operating、CMA仍256MiB。后续修复演示入口的证据目录和Producer Recorder配置遗漏，通过独立demo_engine集中初始化，未改既有CPU数学/NPU图或SDK。每个修订使用新包和新目录，无失败Session续跑。成功两阶段正常drain/LAST、两STREAMOFF、workers join后销毁Engine、全部端口/进程释放及内核不变通过，最终只读身份复核完成。

本轮仅验收有界演示；永久首次启动、原并发坏读根因、严格5Hz、30分钟、零拷贝和HDMI仍待。当前故障排查按用户要求保持暂停；未继续首次Host目的租约方案。详情：[ADR_45](ADR_45.md)、[演示结果](../tools/pose-v1/DEMO-RESULTS-20261011.md)、[Done.md](../Done.md)。

## 17. FPGA、启动介质与工具链基础

物理目标为悟净Lite/JFMQL30TAI676H。基础流水灯先按原理图核对100MHz AC14、LED J1/M6/H7/J8及1.5V，再以FDC约束、Vivado2019.1 XSim自检、Procise2025.1.1 temp/SVN32494综合/布局布线/时序/位流和原生JTAG下载完成实板观察。MCP负责入口与证据组织，未替代时序/身份复核；xlconcat使用真实厂商生成HDL经Procise交接实板，未以stub代替。简单明文组合IP成功不能推广为加密IP、AXI/DMA/HDMI系统均兼容。

SD镜像带imageUSB专用512字节头，先核镜像载荷和FAT启动文件。旧卡8/9文件不匹配、BOOT头异常及局部容量测试失败保留；更换SD后用户确认串口登录，实际 `/dev/mmcblk0p2` 分区和ext4在线扩容经现场验收，再建立SSH与FPAI交叉编译。扩容只增加存储，不增加约1GiB PS物理内存或NPU算力。

部署使用原已核BOOT，SDK通过 `axi://zg330aiu?npu=0x40000000&dma=0x80000000` 访问，设备版本25122301、icore FMSHZGV3TECH-AID - 24160628。每阶段模型/RAW/SDK库/BOOT哈希和设备身份核对，未知地址不猜测写入。SSH使用固定主机密钥核验，演示控制器只在内存提示中读取已授权凭据，报告不保存密码。基础资料及历史工具问题见[ADR_03](ADR_03.md)、[Done](../Done.md)。

## 18. 显示与训练旁支的边界

HDMI为1920×1080／60Hz扫描，720p绘图／编码画布与扫描时序是不同配置。该历史演示未启动HDMI；后续独立应用已完成PS绘图转RGB565、PL读帧／扫描及三窗新推理实屏，详见文首工程入口。扫描刷新率不等于AI新姿态率，长期和跨启动稳定性仍未验收。

训练采用远程GPU环境，不与Lite部署混用。26版迁移/全新训练的残差分化、细化分支及梯度门检有独立实验；迁移收益不稳定，全新500轮试验因分支衰退在第6轮末停止。首版仍固定2024 epoch442，不用未验新模型覆盖已部署图。训练损失、MPJPE、ONNX部署误差和演示视频映射属于不同指标，不能互相替代，详见[ADR_04](ADR_04.md)。
