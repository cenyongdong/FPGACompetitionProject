# 独立AI读路径观测适配与固定DMA探针

2026-10-18状态说明：本页保留早期读观测探针的接口与mock范围。后续r9已用于板测，r13四档DMA及三窗新推理→HDMI通过；启动异常仍未解决，任务当前整体暂停。实际分段／无SDK探针及结果见[工程入口](../INTEGRATION.md)和[暂停汇报](../STARTUP-PAUSE-REPORT-20261018.md)。下述“尚未板测”等表述仅指该早期编写阶段，不能替代当前状态或授予重跑许可。

本包仅用于D45隔离诊断，不接正常Engine、模型或数学路径。源码及纯本机mock验证已完成，mock不替代ARM真实SDK编译或板测；实际ARM探针构建另见build-read-probe证据目录。尚未执行新板测，不能把源码或mock通过写成DMA或全链通过。旧ai_dma_probe.cpp、ai_monitor_sdk.hpp保持原样。

## 执行位置与前置条件

- 源码位于D:/FPGACompetitionProject/FPGA/hdmi_candidate/software。主代理使用build_ai_read_probe.py在既有FPAI ARM64环境以-Werror构建，新目录保存源码、六SDK身份、实际命令、完整日志与ELF；本机mock执行没有启动Docker或SDK编译。
- 板测须有另行批准、已核验的新候选执行包；本源码不构成BOOT写入、重启或重试许可。原BOOT保护、旧DATA独立暂停、SDK异常停止边界保持。
- 已打开Device必须保持同一生命周期，版本为device=25122301、icore=FMSHZGV3TECH-AID - 24160628，初始SDK DMA状态寄存器0x40584为0，内存区类型为AXIZG330AIPLDDRMemRegionNode。
- 命令只接受一个新trace绝对路径。trace本身和从其派生的八份字节证据拒绝覆盖；父目录需预先存在且可写，stderr须由外层完整保存。

## 最小接口与所有权

ai_read_monitor_sdk.hpp使用公开Device::defaultRegRegion，通过原Device访问0x400b0400的512字节观测窗。Capture引用由调用方拥有的Device和ostream：Device必须覆盖所有arm/freeze调用；Device销毁后只允许纯缓存save_cached、本地状态查询及无SDK析构，调用方不能据can_freeze()的本地状态推断Device仍然存在。日志必须覆盖所有写日志调用。Capture禁止复制／移动，析构不访问硬件，不执行Open、reset、DMA、解除错误或重试。

| 偏移 | 契约 |
|---|---|
| +0x00 | 读status：bit0 busy、bit1 error；只写1 ARM、写2 FREEZE |
| +0x04 | ABI必须0x41495201 |
| +0x08／+0x0c | request／response代数 |
| +0x10 | word_count必须104 |
| +0x40起 | 104个保持快照字，最后一字位于+0x1dc；word0必须ABI |

构造参数Epoch只允许两个明确包阶段：默认FreshBoot要求status=0、代数0/0→ARM1/1→FREEZE2/2；AfterSuccessfulProbe要求status=0、代数2/2→ARM3/3→FREEZE4/4。后一模式只能由执行器在完整probe通过、取证成功及free后明确选择，不能仅因为现场恰为2/2就推断成功。软件不自适应任意现场代数，不重置状态消除stale，非法enum也拒绝。每个Capture仍仅允许一次ARM及FREEZE尝试，ARM完成后才允许该阶段第一次负载。

独立DMA探针始终使用默认FreshBoot；共享三窗包的Device opened回调明确选AfterSuccessfulProbe。ARM仅清诊断状态，不清DMA、桥接器、HP端口、DDR、SDK或AI功能状态。

FREEZE仅允许该对象已成功ARM且当前status=0、代数等于所选阶段的ARM目标时执行一次尝试，完成须status=0且代数等于该阶段FREEZE目标。随后读取104字，读取前后都核对代数和status；日志同时保存明确expected_initial_sequence和expected_freeze_sequence，完整原值先写日志，再检查word0及稳定性。错误或SDK读取中断时，缓存只包含确实读到的words_read个字，不用默认零值充当未读取的样本；save_cached不再访问硬件。word1为ARM后sourcecycles模32，word2为flags，word3为reset周期；其余字段按新RTL契约分析，软件不自行转换地址单位或流量守恒。

每条命令使用从CSR写入前开始的100ms steady_clock deadline、100µs轮询间隔。CSR访问使用同步公开SDK；deadline检查发生在访问前后，不能抢占某一次阻塞中的SDK调用。外层仍须设置独立有界进程预算并保留SDK原错误，不把软件deadline当硬件完成证明。

## 固定负载、保存与停止

探针通过ARM后只分配一次1MiB PLDDR块、64字节对齐，依次执行64、4096、65536、1048576字节完整往返，pattern逐字节沿用旧探针：(i*37)^(i>>9)^bytes，再取char。四档之间没有ARM、FREEZE、旧快照或额外同步。

每次read成功返回后，先以O_EXCL创建并完整write/fsync/close：

```text
<trace>.<bytes>.source.bin
<trace>.<bytes>.actual.bin
```

完整两份字节保存后才严格比较，不放宽数据门限。read未成功返回不创建actual文件；文件I/O失败的部分文件保留，trace不会记为完整保存或通过。字节产物的SHA由外层归档计算，不能用文件存在替代完整性核验。

| 结果 | 行为 |
|---|---|
| SDK异常 | 先stderr完整保存原what()；随后最多一次新FREEZE，再用同Device最多一次旧ai_monitor::save保存MIG；诊断异常只另记，不覆盖原错误；exit71，不显式free可能在途块 |
| 字节差异 | 已保存完整source/actual，记录首个差异偏移及原值；观测后exit72，不重试、不继续大档 |
| 诊断文件I/O异常 | 保存错误、尽可能完成单次观测与trace落盘，exit74；不得比较未完整保存的数据或打印PASS |
| 四档全过 | 仅此时FREEZE并读取104字、旧MIG快照、free；完整trace落盘后打印AI_READ_DMA_ROUNDTRIP_PASS并exit0 |
| 前置／身份／初始代数失败 | 不做DMA，不自行reset／re-arm，exit1 |

Open、版本、初始状态或ARM过程中SDK异常也先保存原错误并exit71；ARM尚未完成时不拥有合法FREEZE生命周期，因此明确跳过新FREEZE和旧MIG命令，不冒称已取到快照。ABI、初始代数、ARM超时等已识别的监控契约拒绝与SDK异常分开，前置拒绝exit1且不做DMA。

malloc、transfer、读SDK状态、最终CSR取证或free的SDK异常均进入保存后停止路径；若最终FREEZE或MIG已尝试失败，错误处理不会重复该命令。所有SDK异常分支使用_Exit，避免异常栈展开释放可能在途SDK块；Device和块不作软件恢复，不把无进程owner称为DMA排空。

## 后续验证建议与通过标准

可用不依赖真实SDK的mock记录CSR访问次序，覆盖：初始代数非0拒绝；ARM不完成／error／异常拒绝首DMA；FREEZE必须1/1→2/2；104字读取前后代数变化拒绝但保留原字；第k字SDK异常只保存前k字；重复ARM／FREEZE拒绝且不再次写CSR。另覆盖首次64字节读成功后两份文件完整保存先于比较、4KiB写失败后不生成4KiB actual、不启动65536档、诊断失败不改变exit71和原stderr，以及已有文件拒绝覆盖。

2026-10-17已用本机现有Winlibs GCC16.2、-std=c++17/-Wall/-Wextra/-Werror编译并运行隔离mock：15项helper和12项完整probe场景通过，9.937秒。完整probe源码和两个helper按原字节复制，只有假SDK头及Windows文件API测试shim替换真实外部接口。输入、编译命令、各退出码、完整stdout/stderr、逐次假SDK事件、实际字节文件和89文件清单见历史run-r1结果（原独立result.json已不在当前树）。helper时钟停止、代数变化、七字部分读取、重复命令拒绝，以及probe的SDK原错先记录、读取失败不造actual、差异前保存、晚文件碰撞和预存在路径拒绝均已覆盖。

后续包级审查发现成功probe会留下2/2，而原共享适配只收0/0；原r1编译和mock结果保留，不把编译通过当包级可连用。新增明确Epoch后，历史run-r2结果（原独立result.json已不在当前树）一次8.328秒通过48项helper和13项probe场景，含两个合法阶段、0～7全部错误初始值、req/resp不等、非法enum、同一生命周期不重试以及FreshBoot探针拒绝已有2/2。helper修改前后完整源码和SHA另存helper-epoch-revision-r2；r1实际产物不覆盖。新ARM探针与共享包必须用r2构建证据，最终离线包不采纳r1软件组合。

该mock没有使用真实SDK、网络或板端；Windows shim用_commit代替fsync，并将O_NOFOLLOW/O_CLOEXEC置0，因此不验证Linux这两个flag的语义。实际板测通过须四档完整来源与回读字节一致、104字同代数保持、同Device旧快照成功、资源正常释放且无SDK异常；只编译成功、mock通过或只读到ABI不算板测通过。新推理和HDMI须在该门禁通过后按实际执行包继续。
