# 2018.3前端通过后的Procise接入与原厂流程复核

2026-10-16。本页记录本机原始JFM资料的实际内容及尚待讨论的实现路径，不是完整流程执行通过或替换项目实现目标的授权。

## 当前实际边界

用户安装的D:/vivado18.3/Vivado/2018.3已按明确授权就地执行原版replace_7z030ai_file 0。34份文件共63,130,403字节事先备份，九项最终目标与030ai配套SHA一致，其余备份文件未变化；没有复制完整工具。2019.1和Procise安装库保持。

同SHA七份真实PS包装/依赖的RTL展开29.826517秒、独立综合22.396529秒，均在180秒内工具exit0。真实PS7硬原语存在，实际实例和运行库的7212个位引脚逐项名称/方向一致，全部4527个命名连接和3868个AI_连接均可绑定；EDIF/DCP实际生成。此前按Liberty文本7213总数做的后处理断言exit1保留，之后仅对已保存结果做独立分析，没有重跑RTL。

Liberty与运行库的差异已定位：39个调试端口是DEBUGDATA[161]～[199]与DEBUGDATA161～199的表示形式差异；文本额外的DEBUGDATA160不在实际PS调用中。IN/OUT/INOUT与input/output/bidir规范化后，实际连接和运行库无差异。没有为通过门检改PS、厂商库或原始失败记录。这只闭合前端实例契约，不是目标物理签核。

## 通用网表路径的真实失败

现有Procise translate_file.exe提供的功能是原语名称转换。实际转换新PS EDIF，0.977310秒exit0；100387行保持，3572处差异全部为cell/cellref的七组名称替换（PS7→PCPU7及IO/时钟/反相原语），AI端口/连接/参数均未删除或改写。

转换后网表首次导入Procise2025.1.1temp/SVN32494、JFMQL30TAI676H，post-elaborate阶段3.833887秒exit1。日志含3981条IO-0134内部读取错误、63个不同的PCPU7缺失端口（64条IO-0140另含实例引脚错误）、DM-0047/IO-0168，列举DDRARB、MAXIGP/SAXIHP等接口。此结果证明通用重命名不足以建立本机原生宏契约；不能据此断言器件不支持AI，也不能将内部错误计数解释成缺失AI端口数。

已停止此实现路径，未重跑、删端口、改普通PS或黑盒伪造通过。无完整系统布局布线、位流或下载。

## 本地确有另一套原厂流程

只读读取原厂受保护脚本的真实过程定义，2.767676秒exit0；没有执行hook。原始process_control脚本和正常加载器下的info body表明，这套包包含Vivado综合、优化、布线、位流前后hook，以及可选的Procise位流增量处理。

- add_hook_tcl_to_prj会写Vivado运行配置及工程hook文件；在2018.3还会覆盖安装目录data/parts/xilinx/common/HARC.cfg。它超出本次已执行的九项030ai补丁，尚未备份/修改该文件。
- 其change_speed缺省为TRUE，不能将既有speed=0库替换当作已同意新的速度参数。
- 030AI相关生成脚本有禁用REQP-44/46/52/56检查的分支；另有045AI专用CRC/区域逻辑，不能将不同器件分支混用，也不能将工具的检查关闭当验收通过。
- post_write_bitstream_patch按procise_incr_cfg.txt生成脚本并调用Procise；实际生成命令为increment_bit_cfg_v3，输入是已生成的.bit，而不是将扩展PS导入PCPU7。
- 随包配置默认device_type=JFM7K325T8，输入sw_ctrl_led.bit，输出sw_ctrl_led_incr_cfg.bit；这是其它目标示例，不能复制成30TAI配置使用。
- 原生EDIF迁移脚本与这种位流后处理是不同路径。它们出现在同一工具包中，不证明可互相替代，亦不证明当前版本已适配本板全部资源。

这些发现修正“只要将新EDIF改名送入Procise即可”的假设。本地资料并非缺整套JFM流程；缺的是针对当前30TAI和候选工程、符合项目实现约束且逐项验证的路径选择。

## 下一阶段需要讨论的取舍

| 路径 | 已有依据 | 尚缺/影响 |
|---|---|---|
| 继续原生Procise实现整机 | 本机已支持目标器件，候选扫描/时钟及生成互联有原生综合成果 | 当前PS的RTL和通用EDIF两路都失败；需要正确的30TAI原生PS宏契约/处理入口，不能猜端口映射 |
| 审查原厂Vivado＋JFM、Procise后处理流程 | 已找到实际hook、位流后处理及匹配2018.3库，原参考工程本为2018.3 | 涉及实现工具职责、额外HARC写入、速度/DRC等配置；必须逐项审查并讨论是否采用，不能替代Procise/实板验收 |

建议先就这两条路径讨论；不在本次自行切换实现后端。若进一步准备原厂混合路径，应先生成30TAI限定的参数/读写清单和隔离工程差异，再决定执行范围；未知库写入、时序/DRC豁免和启动变化均不自动采用。保持1080p60目标、当前BOOT/SDK/模型/PS/AI_Mate和旧DATA暂停。

[完整本批证据](../../tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/REPORT.md)、[原厂hook实际定义](../../tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/flow-reading/hook-definitions.txt)、[Procise失败原值](../../tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/procise-ps-import/failure-analysis.json)。
