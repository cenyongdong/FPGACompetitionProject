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
