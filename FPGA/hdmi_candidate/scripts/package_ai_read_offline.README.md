# 读路径观测v3离线打包器

package_ai_read_offline.py只准备本机离线文件，具有icap、boot、bundle三个顺序模式。新增时仅完成源码准备与静态审查；本代理没有运行Procise、BOOT生成、板端命令、部署或重启。实际执行结果以各新目录内完整日志、controller-result.json和review.json为准。

工作目录D:/FPGACompetitionProject；证据根目录tools/pose-v1/evidence/hdmi-live-20261017-r3，工作根目录.local/hdmi-live-20261017-r3。任何目标目录存在即拒绝，失败不覆盖、不自动重试。旧打包器及旧候选证据保持。

## 前置门禁

三个模式均要求read-v3r5-reports/review.json中bit_generation_prerequisite_pass为true，并要求read-v3r5-bit/execution.json实际exit0、无超时或监控终止。唯一原始候选位流来源为W3/reference/fpai_demo_vivado.runs/route_read_v3r5/ai7030_edif_top.bit；不回退搜索其它候选文件。此标识是从已完成物理优化检查点继续的独立native目录，不是伪造或复用的managed run状态；candidate_run字段必须为route_read_v3r5、managed_run为false。

三个模式还共同调用冻结W3 `controlled_read_v3.py`公开纯函数`verify_checkpoint_lineage`（实际源码SHA固定`2e6b57a9351caffa648251e89799bcaf02d412d42d77a224a041789a12a0b65a`），不调用其manifest／批准／CLI入口，不产生manifest循环。要求bootstrap／route／reports／bit真实exit0、无超时／monitor stop、phase通过、DIRECTORY为`.`、937来源／41库及guard、同frozen physopt、新routed checkpoint完整bytes／SHA、正式r5报告review、bit phase／bit-identity及五份完整原厂pre／post hook和五项严格bool true上下文证明全部成立。helper源码、上述实际证据、937源／41库、checkpoint及bit均列入本阶段input-identities，结束前再次逐份核SHA；缺实际产物就关闭，源码存在不当阶段通过。

bit的两个原厂派生写目标另受精确隔离门：`call_procise_disable_icap.bat`（不在937保护源）与`procise_run_disable_icap.tcl`（仍在937保护源）仅可写本次E3/read-v3r5-bit/factory-derived/同名文件。门检绑定bit-input-proof中的isolation plan、bit-identity指向的factory-derived-isolation.json实际SHA、两个原文件before／after原字节档案及实际原位置；原SHA必须相同、每个固定redirected文件必须非空且完整bytes／SHA一致、write_count严格1。要求original_sources_unchanged=true、raw_batch_executed=false及禁止原始batch执行；不运行这些归档脚本，不改原源文件／源hash。该检查在任何Procise前完成，结果记入r5_bit_gate及controller-result；任何缺失、变更或类型错误停止。

综合来源仍为synth_read_v3r3，约束仍为read-v3r3-constraints-r3；旧r3 route在720.625秒被日志监控停止，r4又在1801.297秒因硬上限停止，完整原记录均保留，不能代替新r5实际门检。r4完成的44,506,212字节physopt DCP固定SHA f58a5f8e6f432be7e656de5ee32eae5ae63b491d5a5cb1055425ee32895525d9。r5先以实际bootstrap恢复并核对DIRECTORY为点、937来源、41库、2768位10ns及实际时钟，再仅执行原NoTimingRelaxation路由和完整原厂post hook；放行前仍须bootstrap、route、reports实际执行与正式报告门检，不把前驱的节点重叠0当作路由完成。

原始回退身份只来自hdmi-board-reference-20261016-r1：固定rollback-identity.json与boot-control-utf8-r2/inputs.json完整SHA，原BOOT固定ff350477…a68b31ef、7023552字节，原patched bit固定6818b7f8…1784f72e；原FSBL251210_ddr400_demo.out、bl31.elf、u-boot逐份核原SHA/长度。离线再次核原BOOT中186816起5980464字节PL分区与原bit负载的32位word-swap对应和4字节padding，不依赖历史报告的通过标签代替实际字节比较。

bit_payload解析器仅复用已核SHA的inspect_selected_boot.py公开函数，该文件CLI主体有__main__保护；没有导入另一脚本的执行主体。全部读取身份在阶段结束再次核对，禁止输入执行中改变。

## 三阶段、预算与产物

| 模式 | 新工作／证据目录及实际作用 |
|---|---|
| icap | W3/E3的read-v3-icap；原厂Procise set_device JFMQL30TAI676H，increment_bit_cfg_v3 -disable_icap；保存ai-read-v3.bit与ai-read-v3_disable_icap.bit，检查原始输入未变、Patched=DISABLE_ICAP、payload区别于原回退bit |
| boot | 新W3/read-v3-boot-inputs、W3/E3/read-v3-boot；原PS组件先复制到新ASCII路径，create_boot_image -fmql，仅替换PL；保存candidate.bif、输入身份、BOOT-ai-read-v3.bin、完整审查 |
| bundle | 新E3/controlled-startup-read-v3；不运行工具，完整核验后复制可审查候选和软件包，不部署 |

每个Procise进程预算180秒，完整stdout/stderr、PID、工作目录、Tcl、进程退出与耗时保存。真实工具错误或门禁失败立即停止；超时先保存现场并只终止自有进程树，清理失败另存而不掩盖原始失败。控制器总预算包含至多60秒有界收尾。BOOT输出即使门检失败也保留原文件和原值，不用失败产物进入bundle。

BOOT门禁要求新旧总长度相同、PL以外所有字节完全一致、PL word-swap后对应候选payload、原padding逐字节一致且PL确有差异；不修改原BOOT、uEnv、DTB、内核、SDK或模型。

## r2软件与包级契约

bundle仅采纳build-read-probe-r2及read-shared-build-r2。探针要求compiled/complete和容器停止检查实际通过；共享包要求compiled/package_verified、15文件、128份固定baseline不变、SDK一致、固定JSON/RAW模型SHA一致。两个实际构建源码中的新helper必须同为da850ba0…5b73b60f；共享main必须明确Epoch::AfterSuccessfulProbe，不能用旧r1软件组合。

独立probe使用FreshBoot 0/0→ARM1/1→FREEZE2/2；仅其完整四档通过、快照成功及free后，执行器才可进入共享三窗的明确AfterSuccessfulProbe 2/2→ARM3/3→FREEZE4/4。硬件恰为2/2不能自行推断probe成功，不能自动选取任意现场代数；任何SDK、字节、身份或代数失败均停止后续负载。

bundle核shared-package.tar原SHA/长度，拒绝超过50MiB，逐份读回15个安全常规文件、原manifest和固定模型SHA；不解压执行。原BOOT、新BOOT、原始／ICAP patched新bit、ai_read_dma_probe、shared-package.tar及包内文件清单、r2构建结果、SDK/model/helper身份形成新manifest.json。每份复制完整读回SHA；额外artifacts.json包含本阶段完整文件哈希。

此bundle是供后续审批、部署设计和审查的具体材料，不提供候选BOOT写入、再次重启、文件系统修复或板测许可。原两次候选／回退额度已经使用的历史记录保持；新的启动执行仍需相应明确授权。

## 本轮离线门检证据

`E3/packager-checkpoint-bit-gate-r1/mock-r1`对实际packager SHA `bf39a9e49a264d94b5033141560ac9c115c4b214faf104dac377a050e639ac3f`完成30项纯mock、9.453秒。覆盖冻结公开helper真实SHA导入与错SHA拒绝、三个phase的helper／937源／41库／checkpoint／bit输入固定、lineage失败在任何工具前停止，以及派生目标／一次写／类型／before-after／归档原字节／redirected bytes-SHA／原始batch禁止等负例。helper本身的r5 lineage门另见`checkpoint-lineage-gate-r1/mock-r2`43项；本组只mock其返回，明确验证packager调用和输入冻结，不把合成数据当实际bit验收。

同目录保留修改前后源码／README／SHA与独立只读root route reviewer审查记录。实际Vivado／原厂hook上下文、Procise、BOOT生成和板端均未由本组运行；后续仍须根执行器按实际新阶段结果逐门检查。
