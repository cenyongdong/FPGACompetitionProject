# 项目执行规范

- 参考触发器：遇到比赛要求、悟净 Lite 硬件、Procise/Icraft 工具链、AI 部署、FPGA 开发或系统联调问题时，先查阅根目录 `REFERENCES.md`，再按其中索引核对原始资料。
- 歧义处理：在理解或执行过程中遇到任何模糊、不清晰、资料矛盾或缺失的地方，及时向用户提出并讨论，不自行决断；暂停依赖该结论的操作，可继续不受影响的阅读和整理，并记录用户确认结果。
- 决策与执行审批：根据分析结论形成的决策，必须在执行前与用户讨论并取得明确同意；任何认为重大的项目、技术决策及其执行也必须先讨论并取得同意。讨论时说明结论依据、拟采取的操作、影响与尚存的不确定性；未获同意不得执行依赖该决策的操作，不能把排查授权、用户沉默或笼统意向当作对后续修复、配置变更或实施方案的同意。
- 关键决策分析：面对用户提到的关键决策，必须以中立、客观的视角进行分析，不偏颇、不谄媚，一切以客观事实和可行性为准；区分已验证事实、推断与未知项，说明方案的适用条件、收益、成本及限制，不因迎合用户偏好而预设结论。
- 完成工作记录：每次完成项目开发或验证后，将对应工作写入根目录 `Done.md`，统一使用“工程内容总结＋对后续开发的参考”模板。工程内容总结应记录目标、平台/工具版本、实现内容、验证结果与证据路径；后续开发参考应说明可复用方法、适用条件和限制。已有同一工作的记录时优先补全、更新，避免重复；严格区分已完成、待验证和用户现场确认，不将分析或计划写成已完成成果。
- 当前基线：悟净开发板 Lite；Icraft 3.39.0；Procise 来自 `FMSH_Procise_2025.1.1_temp_202603201420_32494.exe`；板载镜像为 `icraft_v3_ubuntu20.04_aarch64_sd_image.bin`。参考位流尚未确定，不能自行选定；用户已确认 `Docs/开发板手册/JFMQL30TAI_LITE.pdf` 是 30TAI 配套原理图，查阅 `REFERENCES.md` B4 获取页码和引脚依据。MIPI BANK12 电平及 GPIO 网络名/BANK 对应仍存在资料冲突，相关接线或约束须先讨论核对，不自行决断。
- FPGA 平台规范：本项目以复旦微 Procise 为开发与实现目标；参考 Vivado/Xilinx 工程时可以借鉴 RTL、接口和设计方法，但必须核对复旦微器件、封装/BANK、原语、IP、时序库、约束转换、位流及调试工具的适配。Vivado 的器件识别、仿真或报告不能替代 Procise 的实现/位流/时序和实板验收；不得直接采用未经适配的 Xilinx IP、位流或底层假设。
- 已验证硬件状态（用户报告，2026-09-30）：Lite 已在无 SD 卡情况下完成开机和连线上板测试，使用 Alinx 黑金下载器，Procise 与 Vivado 均可识别芯片；不再将下载器连接/器件识别列为尚未验证。此结果不自动证明 Linux 启动、特定位流功能、DDR/AI 或模型已验证。
- 原生 FPGA 测试（2026-10-01）：用户已批准 `FPGA\lite_led_chaser` 独立流水灯方案、XSim 2019.1 纯 RTL 行为仿真、Procise 全流程及生成位流后直接 JTAG 易失配置下载，并批准 StartupClk=JtagClk 修正；本次仿真、原生综合/布局布线/内部时序、位流复核和下载已完成，用户现场确认“四颗 LED 按预期循环”，全流程功能验收通过。总结见 `Done.md`，入口和证据见 `FPGA\lite_led_chaser\README.md`、`REFERENCES.md` 第 13 节；不能将其扩展为 Flash/BOOT 更新、AI 系统或 MCP 全流程已验收。本次流水灯未使用 MCP；后续接入状态见下一条。
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
