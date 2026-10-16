# 原厂路径二实际实施、整机参考位流与门检结果

2026-10-16，Windows。用户同意审查后的方案并授权查看本地资料、自主决策推进。工作目录D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1；Vivado2018.3 Build2405991/IP2404404，Procise2025.1.1temp/SVN32494。没有复制Vivado工具目录，只复制原参考工程297文件与JFM配套3401文件/2,171,091,576字节。原源码/PS/AI_Mate/模型和BOOT不写回。

## 结果先看边界

原厂参考工程已实际完成综合、布局布线、位流生成及Procise的30TAI ICAP后处理，impl_r2整阶段1173.647281秒、exit0。**完整时序门检未通过，产品HELD，未上板。** 新HDMI候选尚未接入；原始参考中的扫描问题和ASCII常量保持原样，不能把这些新参考位流称为HDMI修复候选。

| 门检 | 实际结果 |
|---|---|
| 原配置生成后/原厂hook后契约 | 28项XCI非运行时参数相同，5份DDR PRJ及父BD同SHA |
| 实际2018.3 AXI3模型 | 两个入口各32 ID，64读/64写完整16拍burst、数据/路由/背压通过；全局一次在途，四阶段均小于90秒 |
| 完整链实际产物 | 原始.bit 5,980,025字节，Procise ICAP.bit 5,980,609字节，真实路由DCP |
| Setup/Hold | WNS0.030ns/TNS0，WHS0.021ns/THS0，失败端点均0 |
| 最小周期 | WPWS−0.409ns/TPWS−0.479ns，失败端点2，报告明确Timing constraints are not met |
| 内部约束覆盖 | no_clock0，内部max-delay未约束0 |
| 外部时序/CDC | HIGH未设input delay11/output delay6；CDC Critical报告条目12,822，未完成签核；不是独立物理故障数 |

[完整结构化复核](result-review.json)、[AI时钟连接](AI-clock-trace/actual-clock-connectivity.txt)、[总时序原值](implementation-only-r2/timing-summary.rpt)、[CDC原值](implementation-only-r2/CDC.rpt)。两处最小周期失败来自原AI_Mate的1GHz模型，非HDMI常量修复引入：BUFG/I要求1.409ns，PLL CLKOUT0要求1.071ns，实际1.000ns。原网表已有该PLL配置；路由DCP中可见BUFG只连锁定状态寄存器。是否为硬核时钟占位/保活结构，缺少已核验的正式适配语义，不能推定硅上能力或擅自豁免。保持AI_Mate及频率，下载步骤停止；旧DATA未恢复，更不能把此报告当其根因证据。

## 原厂配置决策和安装状态

32项IP库原文件先独立备份、回读SHA，再按原厂精确清单应用，全部目标SHA匹配。与先前030ai九项补丁合计41项预期变化；2019.1九项目标、其它已备份2018文件状态和HARC均核验保持。完整[备份](IP-library-backup-manifest.json)、[实际应用](IP-library-apply.json)、[回退对象及身份条件](IP-library-rollback-plan.json)保留，未自动回退。

正式配置xfft_modify=FALSE表示32项配套已独立应用，避免重复覆盖；不是省略这些库。早前“工程存在counter实例”的推断已[更正](counter-usage-correction.json)：索引缓冲是FIFO，活跃counter实例未证；完整应用32项的依据是原厂配套一致性，不能声称每个库均实际实例化。change_speed=FALSE保持；只读核对实际xc7z030默认分支仅复制zynq.lib/padr，二者均与现安装逐位相同，见[速度默认值核验](030ai-speed-default-readonly-review.json)。

只接受原厂030ai四项GT检查处理。实际一个GTXE2_CHANNEL、一个GTXE2_COMMON在SDI层次；执行守卫日志逐项记录REQP-44/46/52/56关闭，没有扩大到其它规则。实际实现会话DRC列99项Warning/Advisory、无Error，含两个单规则显示上限；复开DCP的诊断会话恢复默认规则，REQP-52/56重现为Error。两套报告均保留，不互相覆盖，见压缩包中的impl_r2/ai7030_edif_top_drc_routed.rpt及[默认复开报告](implementation-only-r2/DRC.rpt)。规则会话设置不会自动由DCP恢复。

MIG CLK_REF非专用时钟路由例外在JFM hook前原配置生成的XDC即存在，限其200MHz参考到MMCM CLKIN1，不是新HDMI例外。[前后原值与决定](MIG-clock-review/decision.json)。原厂正常pre_synthesis会改隔离生成的MIG实现RTL/XDC并重综合；本批保存适配后DCP，不称生成RTL逐位未变。自定义PS修订、DDR配置和BD仍保持；未用原生PCPU7失败作为本路径前置条件。

## 超时处置和真实执行记录

原始完整链初始180秒，在有新日志、无ERROR、资源允许时按180秒有界延长。到1800秒绝对上限时已完成24项IP OOC、顶层综合、布局和物理优化，布线刚启动；最近日志4.63秒，仍无ERROR。监控按上限终止原进程树，exit1，旧结果保持为中断。[原决定与退出](factory-system/execution.json)、[清理](factory-system/cleanup.txt)、[清理后0进程](after-limit-process-inventory.json)及[原impl_1完整快照](factory-system/frozen-impl1/manifest.json)保留，ZIP逐条SHA已验证。

代理依据用户超时自主判断授权创建新impl_r2目录/Session，复用完成且NEEDS_REFRESH为false的综合，未重跑IP或顶层综合。原Performance_NetDelay_high策略、所有输入/约束/hook及实际命令保持；[完整驱动diff](implementation-only-r2/generated-driver-diff.txt)仅为create_report对象名称改变，[独立归一核验](implementation-only-r2/normalized-profile-review.json)通过。新实现初始180秒，依据真实进展续等原进程至1260秒预算，在1173.647281秒完成。没有向用户重复请求超时批准。源码helper v1用于首批，后续版仅将监控日志范围限定新运行，避免把旧失败日志当本批新错误。

实际根IP/父BD生成73.044333秒；独立MIG前置OOC261.135601秒（180→360秒）；AI时钟DCP只读追踪50.859220秒。各阶段工作Tcl、stdout/stderr、execution、超时依据分别在目录内。首次非ASCII路径解码/控制台GBK错误、嵌套IP生成入口错误、生成注释严格字节断言及IP名称误判均保留或按[失败复核说明](driver-failures-review.json)标注证据形式，不把后续修正当首次通过。原始AXI模型生成参数及测试源前后SHA均保持。

## 位流身份、日志限制和交付

[HELD参考产物](HELD-reference-products/README.md)中两份实际bit和路由DCP已复制并SHA回读。[身份及头部](HELD-reference-products/identities.json)：原bit SHA5a435937c5a0be8a3bce0db77555bd85e67c4b4ebf450c5afbd662e779e2fb50；ICAP输出SHAab9af4b8679a8f4bbe958d4dadbc78b81156da4a3b5a67c6510c9d1269befb78。原厂调用目标JFMQL30TAI676H，输入输出路径明确；头部UserID53180205，与实际引擎5.3.1.8对应，输出标记DISABLE_ICAP,VCCM/PatchID32494。不把包标签5.3.2.1_100AI_LV混同成实际运行引擎。

原厂Tcl exec会返回但不打印Procise子进程详细stdout，本次新bit调用没有独立原生stdout文件；记录命令、错误传播和产物身份，不虚构完整子进程文本。另一次对复制的原厂旧bit的独立[实际Procise探针](factory-bit-icap/execution.json)有完整stdout、4.011027秒exit0，输入不变、输出生成；其中Missing Bit Patch Info/VCCM inactive提示仅属于该旧bit探针，不移植到新生成bit。下一候选应在执行前完善这一层日志。首个未适配MIG检查点在原厂reset前未单独冻结，原执行/完整stdout保留；适配后MIG、真实综合和路由DCP已另行保存，不回填旧产物身份。

本地PDF检索和教程第5页整页渲染保留；原理图不能全文检索，因此不能据一次文本检索断言全部本地资料都没有1GHz依据。当前未取得相应正式例外，原最小周期/CDC门检失败保持。[门检分析与恢复边界](../../../../FPGA/hdmi_candidate/AI-CLOCK-GATE.md)、[实施配置](../../../../FPGA/hdmi_candidate/ROUTE2-BUILD-PLAN.md)。

所有实际运行日志、报告和DCP按[235项清单](actual-run-products-manifest.json)归档到actual-run-products.zip并逐条SHA核验；直接可读报告及关键产物另保留。source-snapshots、生成hook/守卫和输入身份可复核。原参考297文件、9扫描RTL及旧三批封存清单SHA通过；文档工作原值和脱敏快照身份分别记录，历史完成清单不回写。最终EDA进程为0，无板端连接、下载、BOOT改写或重启。
