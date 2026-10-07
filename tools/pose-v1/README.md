# 首版实施工具与证据

> 当前RTSP首批已验证：200帧传输/重连与标准播放器100帧逐位原视频，有限上下文清理通过，无新依赖。[结果/录制视频](RTSP-RESULTS-20261007.md)、[F0接入准备](F0-INTEGRATION-PREP-20261007.md)。当前是预生成码流回放，在线VPU/实际推理合并、显式色彩、HDMI/整机长期仍待；旧未RTSP/暂停条目为历史。

> 当前最新：视频任务已恢复，真实27骨架/54帧有限编码及两独立上下文重复通过，主机完整核验，MMAP描述兼容修正已采用。[结果/视频](VIDEO-DESCRIPTOR-R5-RESULTS-20261007.md)、[恢复入口](RESUME-VIDEO-20261007.md)。原推理/SDK/BOOT保持，HDMI1080p60未改时序，RTSP/实时合并/整机长期未通过。旧暂停和失败条目按历史保留。

> 当前暂停：真实骨架编码发生VPU固件MMU ABORT；[首批报告](VIDEO-SEQUENCE-RESULTS-20261007.md)、[失败核验](evidence/video-sequence-20261007-r1/failure-review.json)、[恢复说明](RESUME-VIDEO-20261007.md)。HDMI只读/离线色条已准备、无实屏写入，用户要求等待唤醒。Build-VpuSequence等新工具不是已验收生产编码器，不重跑失败包。

> 最新安排：[下一视频计划](NEXT-VIDEO-PLAN-20261007.md)、[恢复授权与来源检查点](evidence/video-next-plan-20261007.json)。用户已审查编码样片并允许HDMI测试，暂停解除。首批真实骨架动态文件＋当前BOOT HDMI配套，随后1080p60实屏/RTSP/真实推理合并；未新板测。

> 最新独立VPU：[720p10fps/30帧结果与MP4](VPU-RESULTS-20261007.md)、[执行位置/停止条件](VPU-COMMANDS-20261007.md)、[核验](evidence/vpu-20261007-r1/completion-review.json)。Build-Vpu/prepare_vpu_frames/run-vpu-stage/audit_vpu_stage/review_vpu_video为隔离工具，主机已有OpenCV，无新安装。HDMI目标1080p60、接屏不支持时序、测试暂停未改硬件；编码文件通过不等于RTSP/整机/长期。恢复读vpu新检查点，旧未编码记录为历史。

> 最新渲染与V0：[结果/预览](RENDER-RESULTS-20261007.md)、[命令](RENDER-COMMANDS-20261007.md)、[配套差异](V0-VIDEO-PAIRING-20261007.md)、[核验](evidence/render-20261007-r1/completion-review.json)。CPU画面与三格式通过，VPU实际只枚举MPLANE，编码/HDMI/RTSP仍待；恢复按render-r1检查点。

> 最新E1首批：[生产接口/TCP结果](APPLICATION-RESULTS-20261007.md)、[命令](APPLICATION-COMMANDS-20261007.md)、[完成核验](evidence/application-20261007-r2/completion-review.json)。当前入口为application_gate.py、Build-Application.ps1、send_application_cases.py；原P2/r6保持。下一阶段为渲染/视频配套，网络2Hz正确性不算整机5Hz。

> 最新：现有数值阶段已由用户验收；profiling关闭＋单时钟计量及消息构造优化已完成，处理基线5.24655Hz/P95 190.75409ms，整机/视频/长期未验收。[P2结果](P2-RESULTS-20261007.md)。较早“数值未验收/4.65Hz/P2候选”保留为历史。

当前状态见[STATUS.md](STATUS.md)、已批准[全流程计划](FULL-FLOW-PLAN-20261007.md)和[应用检查点](evidence/application-20261007-r2/next-checkpoint.json)。旧N1/P2“数值/核心5Hz未通过”按历史理解，当前固定样本数值由用户验收、核心短期5.25Hz；整机/视频/长期仍待，勿重复已完成门检。

<details>
<summary>历史工具交付和阶段说明（较早“当前/下一步”按当时日期理解）</summary>


当前快照r2已编译并独立核验，[构建结果](MIXED-BINDING-R2-BUILD-RESULTS.md)，构建验收文件已生成。
使用新r2目录传输后先Host107完整回传，不重跑r1/复用旧门禁，不直接apply或mixed。

当前已批准绑定快照r2并应用，新包准备完成，尚未编译/执行；入口[MIXED-BINDING-R2-COMMANDS.md](MIXED-BINDING-R2-COMMANDS.md)。
仅SDK公共元数据快照，保留原严格门检，先新构建/前置门检后apply取证无forward，旧r1不重跑。

当前SDK设备内存往返已通过，[结果](MIXED-MEMORY-RESULTS-20261006.md)；memory验收文件已生成。
用户仅300秒apply-check（创建/apply/绑定、无forward），回传核验后再单样本。前置步骤不重跑。

当前offline真实RAW/PS已独立验收，[结果](MIXED-OFFLINE-RESULTS-20261006.md)；离线验收文件已生成。
用户满足硬件前置条件后仅30秒memory-check并回传；Host/离线不重跑，不直接Session部署。

最新mixed-r1 Host桥独立验收已通过，[107例结果](MIXED-HOST-RESULTS-20261006.md)，host-check.acceptance.json已生成。
用户传板并回传提前offline的失败预检目录后再继续离线；不重跑Host或跳过门禁进入硬件。

最新mixed-r1构建已核验通过；[一条缩进警告审查](MIXED-BUILD-REVIEW-20261006.md)确认控制流符合预期，源码/包保持。
build.acceptance.json已生成；现在用户继续命令B传输，再C仅host-check。下述未编译为原交付状态，Lite新阶段仍未运行。

2026-10-06当前入口：[MIXED-VALIDATION-COMMANDS.md](MIXED-VALIDATION-COMMANDS.md)，
独立目标pose_mixed_check及SDK Host桥已交付、新测试包已准备；尚未编译/板测，用户先完成构建返回证据。
[ONNX三样本参考](ONNX-REFERENCE-RESULTS-20261006.md)已实际完成，
[范围与阶段](MIXED-VALIDATION.md)、[交付身份](evidence/mixed-source-delivery-20261006.json)。
工程/数值分阶段、ONNX直接对照Lite；不等待Icraft CPU Matmul，不把源码或参考通过当成mixed/双路通过。

状态与边界见 [软件说明](../../software/pose_v1/README.md)。此目录不包含已通过的完整推理/双路显示系统。

CPU最小候选已于2026-10-06完成Lite独立验收，见[结果](CPU-ADAPTER-RESULTS-20261006.md)：
107例、12条注册记录、22输出/59,600个FP32值逐位一致；当前仍未接入正式推理器或验证NPU数据交接。
下述未编译/运行是最初源码交付状态，完整证据已补入结果文档。

2026-10-05用户批准后新增[CPU最小注册适配](CPU-ADAPTER.md)和[用户执行命令](CPU-ADAPTER-COMMANDS.md)：
`cpu_adapter_gate.py`生成固定NumPy参考并复核回传，`Build-CpuAdapter.ps1`交叉编译独立候选，
`run-cpu-adapter.sh`在Lite进行一次受限CPU测试。源码已交付，尚未生成测试包/编译/运行；
不接入现有推理器、不覆盖Gather、不补CPU Matmul、不访问NPU/DMA/HDMI。

2026-10-05新增独立混合推理检查器配套工具，尚未编译/运行：

- [INFERENCE-COMMANDS.md](INFERENCE-COMMANDS.md)：用户逐条执行入口，先做A环境查询。
- `Build-Inference.ps1` / `aarch64-icraft.cmake`：从当前worktree独立复制并交叉编译，不自动运行二进制。
- `Run-HostReference.ps1`：仅Host参考，逐项校验既有独立DLL，只改子进程PATH。
- `inference_gate.py`：原三份真实CSI打包、ONNX参考、数值统计和回传哈希校验，不安装或访问设备。
- [HDMI-STATIC-AUDIT.md](HDMI-STATIC-AUDIT.md)：参考源码、时钟/时序线索及用户资料确认；未配置HDMI硬件。

下面历史脚本保留；软件/AI操作也由用户执行，不沿用历史代理代执行授权。

- `Invoke-BoardAudit.ps1` / `board_probe.py`：严格主机密钥验证，读取FAT16启动分区、设备树。
  不挂载、不改启动文件、不访问未知寄存器；交互输入密码，不写入源码/证据。
- `validate_preprocess.py`：用实际训练AST、6个合成用例和固定9组300份真实MAT与FPAI的Linux主机C++比较。
  固定清单保留原3份回归；按批准幅度/相位周期策略门检，另报告标量差。生产C++未修改。
- `numeric_metrics.py` / `test_numeric_metrics.py`：主机与板端共用数值策略；人工±π只作非阻断诊断，
  真实相位标量差>1e-5 rad仍触发讨论，防止周期等价掩盖模型输入差异。
- `prepare_board_bundle.py` / `summarize_gate.py`：生成哈希核验的固定测试包，再联查窗口/参考/主机/板端身份。
- `inspect_selected_boot.py`：离线解析所选BOOT、.bit头部/载荷，对照新旧板端审计与启动日志。
- `read_fpga_version.candidate.py`：本次经单独批准仅只读回读0x4000001C=0x25122301；
  默认为只打印方案，再执行或扩大地址/SDK初始化范围仍须符合授权，不能当作通用寄存器访问入口。
- `Invoke-BoardPreprocessTest.ps1` / `board_preprocess_test.py`：核对测试包SHA256后在唯一`/tmp`目录
  运行arm64数值程序，报告误差及异常输入；不调用AI、视频或修改系统配置。
- `replay_raw_csi.py` / `csi_io.py`：原始数据客户端，板端接收服务尚未实现，不作为网络联调通过。
- `audit_assets.py`：只读记录所选模型、源码、生成物哈希及Host/NPU图分工。
- `test_replay.py`：Windows本机TCP回环，强制碎片读取验证3个原始窗口字节不变；不代表板端网络验收。
- `diagnose_phase_boundary.py`：只在离线参考中替换标量angle以排查边界；当前替换未解释C++偏差，
  不改变生产代码/训练文件，也不构成误差容限批准。

执行源码来自当前Codex worktree；FPAI挂载原`D:\FPGACompetitionProject`。本次源码明确复制到
容器`/tmp/pose-v1-source`构建，未修改原项目挂载、镜像、工具链或已安装SDK。
临时主机/arm64二进制、输入/参考张量在`.local/pose-v1-build`与`.local/pose-v1-validation`，不提交生成物。

`evidence/host-preprocess-initial-failure.json`保留零幅值移植错误；`host-preprocess.json`为修正后主机结果，
`board-preprocess.json`为实际板端结果。每个case的名称/原始文件由主机报告关联；不得抹去π边界失败。
本次实际数值参考是上述WindowsConda版本，不据此声称原训练服务器软件栈已重验。

最新300份门检、启动及运行版本结果见[RESULTS-300.md](RESULTS-300.md)；
`evidence/*-300*`与`board-runtime-audit-25122301.json`为本阶段新证据，旧9用例与原BOOT审计保留。
审计/板端复验须指定新的`-EvidencePath`，已存在的证据文件会被拒绝覆盖。

</details>
