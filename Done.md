# 已完成工作记录

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
