# Vivado2018.3就地030ai补丁、扩展PS前端与Procise接入

2026-10-16，Windows，工作目录D:/FPGACompetitionProject。用户明确取消完整工具复制，批准180秒新批次，并授权当前2018.3备份后就地补丁；用户关闭GUI后核对无占用。旧r1的60秒超时保持，不回写为通过。

## 实际结果

| 阶段 | 实际耗时 | 结果与范围 |
|---|---:|---|
| 备份/原厂过程读取 | 过程3.580671秒 | 34文件63,130,403字节，备份SHA一致 |
| 原版replace_7z030ai_file 0 | 6.924940秒 | exit0；精确文件写入守卫，最终九目标全部等于030ai源 |
| 真实扩展PS RTL展开 | 29.826517秒 | 工具exit0；旧后处理总数断言exit1另保留 |
| 连接契约独立复核 | 仅读原输出 | 全4527命名连接/3868 AI存在，实际实例/运行库7212位引脚名称方向一致 |
| 真实扩展PS综合 | 22.396529秒 | exit0，实际EDIF/DCP及利用率报告生成；PS7硬原语1，不是人工黑盒 |
| 现有translate_file转换 | 0.977310秒 | exit0，3572处差异仅7组原语名称替换，所有端口/连接/参数保持 |
| Procise转换网表导入 | 3.833887秒 | exit1，PCPU7接口不匹配，保存停止未重跑 |
| 原厂hook定义读取 | 2.767676秒 | 只读exit0，未调用hook/后处理 |

所有实际EDA/转换阶段上限180秒，本批无超时。已批准的RTL仿真预算保持，未新增像素负载。当前2018.3为030ai专用补丁环境，原版关键文件在[备份清单](backup-manifest.json)，[实际九项变化](patch-review.json)、[回退对象](rollback-plan.json)可核验；未复制完整工具，未自动回退。原参考297文件、九扫描RTL与2019.1九项库文件SHA保持。

真实PS沿用原已保存七份包装/依赖的SHA，不升级自定义PS，不改变AI_Mate。原代码读入后识别一个真实PS7硬原语并综合出[EDIF](actual-ps-synth/actual_ps.edf)与[DCP](actual-ps-synth/actual_ps.dcp)。后处理最初把Liberty7213总数当运行库总数，断言失败保留；独立检查实际连接后闭合：39处DEBUGDATA命名形式差异及Liberty独有、未被调用的DEBUGDATA160，IN/OUT/INOUT与input/output/bidir按语义规范化。没有为此改RTL或厂商源，也没有重跑RTL。[实际连接复核](actual-ps-rtl/connected-contract-review.json)。

## Procise的真实停止点

通用转换工具只完成PS7→PCPU7等名称替换。转换前后100387行，3572处差异全部为cell/cellref名；[完整线性对照](translate-ps/linear-diff.json)、[语义审查](translate-ps/conversion-contract-review.json)保留。全文difflib后处理较慢但最终自然完成，没有重跑转换。

新网表送入Procise2025.1.1temp/SVN32494、JFMQL30TAI676H的post-elaborate，实际报3981条IO-0134、63个不同的PCPU7缺失端口及DM-0047/IO-0168，含DDRARB和AXI接口；[全部错误与命名](procise-ps-import/failure-analysis.json)、[原stdout](procise-ps-import/stdout.txt)。内部错误数不是缺失AI端口数，不能推断硬件没有AI。此失败没有重跑，也没有删端口或伪造普通PS/黑盒。无完整实现/时序/位流或板端下载。

## 本地流程已查到的新依据

原厂包确有Vivado综合/实现/位流hook及可选Procise increment_bit_cfg_v3后处理，并非只有通用EDIF迁移。只读[真实函数体](flow-reading/hook-definitions.txt)和原process_control脚本已核对：add_hook还会覆盖HARC.cfg，change_speed默认TRUE，030AI分支会禁用若干REQP检查；随包位流配置却默认JFM7K325T8/sw_ctrl_led，不能直接套30TAI。它改变实现工具职责及额外配置，尚未调用或采用。

后续需要讨论原生Procise PS宏接入与原厂混合流程的选择，详见[具体依据/影响](../../../../FPGA/hdmi_candidate/JFM-FLOW-REVIEW.md)。不把前端通过推广为完整系统验收，不自动替换实现后端或复制默认配置；BOOT/SDK/模型/RAW/PS/AI_Mate保持，旧DATA调查仍暂停。

Common17-741本地TclStore路径告警、补丁恢复过程的fmsh-2023提示和独立PS无完整约束的WARN均保留，未静默删除。前端综合只做接口/资源门检，不作STA签核。修复监控的清理异常落盘路径已静态检查，本批实际无清理超时；所有源码、命令、输入身份、原始结果、文档前后值及清单保留。最终进程盘点/封存见completion-review.json。
