# 三窗推理→HDMI只读路径观测构建器

`build_ai_read_shared.py`当前准备r2修订，尚未执行本修订的Docker或板测。r1此前已由主执行器实际编译并完成15文件包核验，但包级审查发现：probe完成后观测代数已是2/2，r1共享入口仍限定首次0/0，会拒绝继续；r1编译通过不能称可用全链包。旧r1实际驱动、导出源码、日志和产物全部保留，未回写。

本脚本用于主执行器在已停止且无人占用的FPAI容器中完成一次有界ARM交叉构建，不启动Docker Desktop，不连接Lite、不写BOOT、不重启、不执行模型。

## 目录及前置身份

工作目录D:/FPGACompetitionProject。本修订创建全新的证据`tools/pose-v1/evidence/hdmi-live-20261017-r3/read-shared-build-r2`及导出源码`.local/hdmi-live-20261017-r3/read-shared-build-r2`，存在则停止；容器源码为全新`/tmp/hdmi-live-read-shared-20261017-r3-build-r2`。使用本机实际Docker CLI和既有FPAI容器，要求初始容器状态exited，构建所有退出路径均尝试停止自己启动的容器。不得重复运行覆盖失败目录。

冻结源来自`.local/shared-resident-source-20261015-r1`，manifest SHA d2853ef64e76aba71d7ee175c7d85655bd3bab2352fc7c0264ea460c45656f3c；先核138文件并规范化Windows反斜杠，导出后严格检查128份baseline文件不变，仅application_core.hpp/.cpp两个既有可选回调适配文件变化。正式core、HDMI main及旧构建脚本不修改。三窗12份固定fixture与两份模型同旧monitor-v2包完整逐份核验，JSON/RAW仍分别为a1395205eed11112ac0e23dacf8eec4c09d7dfec120e99b060a9361cb9c812cc及d235ec300f2872f1b78ce6101bc98fd2cc13c47a53fe99f76e045587148279dd。输入、数学、CPU/Gather注册、NPU分配、SDK和帧协议不变。

## 公开Device适配与停止顺序

导出Config保留已有opened、apply-exception、ready三个可选回调，不增加私有访问或新的Engine接口。Device是Engine::Impl的稳定成员，open_device只赋值一次。opened回调显式构造`Capture(device, log, Epoch::AfterSuccessfulProbe)`，校验ABI/104字/status0/固定seq2/2后仅一次ARM到3/3，取得100ms有界ACK后才继续Session创建和apply；FREEZE严格从3/3到4/4。该入口仅适用于已成功完成限定probe的后续阶段，不可单独从初始BOOT运行，不从现场代数自适应、不接受任意初值、不重复ARM/FREEZE。probe保留默认`Epoch::FreshBoot`的0→1→2。额外旧MIG观察器只校验身份，on_device_ready保留原HDMI分配/完整帧写读验证。

原Session.apply异常先完整写stderr并flush，再将原what()写拥有日志，随后同一仍存活Device FREEZE并保存104原值；旧v2 MIG快照在独立try中随后保存。每个诊断错误独立报告，不能覆盖原异常，最后继续throw原异常；FREEZE失败只允许保存已读缓存，不再请求一次。不能将诊断失败记为capture成功。

正常三窗全部完整保存并通过原门检、HDMI close()已证明STOP及释放、所有常规诊断保存成功后，才在Engine销毁前FREEZE/保存104字与旧MIG快照。三窗之间没有新增snapshot、同步、读回或更改数学。冻结失败不产生成功summary。Capture引用Device及更长寿命ofstream，主入口只在成功Engine仍存活时使用非拥有Device指针。构造失败只在内部apply回调访问Device；main catch仅销毁无SDK析构的Capture，绝不解引用已失效Device或再次FREEZE。其他初始化或处理异常不自动扩大为新SDK取证。

## 构建及通过标准

编译器必须实际报告aarch64 GCC9.4.0，SDK六库SHA同既有expected.json，CMake固定3.39.0.0 EXACT。所有TU保留-Wall -Wextra -Wpedantic -Werror -ffp-contract=off；构建2线程，每阶段90秒，容器start/stop30秒。原先成功日志已确认两个既有unused-function：resident_support.hpp的匿名elapsed（main TU）和冻结host_cpu_adapter.cpp的匿名need。主执行器明确接受仅这两个TU增加-Wno-unused-function，保持冻结源码及其它告警错误；不是全告警零豁免。脚本复核compile_commands.json中精确两处范围，不能对新TU或全局放宽。

任何身份、编译器、编译、退出码、超时、ELF依赖或包哈希不符立即保存停止，不自动重试。CLI超时先停止该CLI并保存完整所得stdout/stderr；finally停止本批FPAI，停止失败另存cleanup-failure.json且不覆盖原错。构建产物必须为AArch64 ELF，依赖原Icraft Host/ZG330库。导出源码/适配diff/编译命令/日志/退出码及版本保存，构建后再次验证导出源码未变；15文件归档完整读回SHA复核。result.json只能说明编译和包验证，board_executed与full_chain_board_passed始终false。

正式模型板测、后续BOOT候选与重启均不由此构建器授权。旧DATA保持暂停。新helper由独立模块维护，脚本仅复制并记录实际SHA，不修改其实现。
