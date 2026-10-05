# 项目执行规范

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
