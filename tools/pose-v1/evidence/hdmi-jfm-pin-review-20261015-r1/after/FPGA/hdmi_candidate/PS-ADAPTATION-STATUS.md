# 30TAI自定义PS原生适配阻塞与恢复入口

2026-10-15。板测、隔离重建、16根IP修订白名单与有限衍生字段例外均已获批准。本页记录实际新阻塞，不撤销已有授权，也不将工具不兼容推断为PS配置或AI_Mate设计错误。

## 用户补充资料后的最新核对

进一步按用户提示核对真实replace_7z030ai_file：严格限2018.3，先恢复多器件库再替换9项Vivado原语/器件文件；当前2019.1工程内只读入单文件仍报AI_IN端口不匹配，未改全局库或绕过版本检查。原理图确认AC14/100MHz、TMDS差分对，以及F8=1.5V/高有效PL_KEY2；IO直驱1080p60不可保证的限制保持。PS构建仍阻塞，未下载候选。 详见[JFM兼容核对](JFM-COMPATIBILITY-REVIEW.md)及[引脚契约](PIN-CONTRACT.md)。真实Tcl过程已通过正常加载器在只读拦截下读取；以下“未加载”是上一批结束时的状态。当前仍未执行replace/reset/hook，未更换工具或全局库；新探针失败与原生失败分别保留。

## 已实际闭合

新r3副本有限契约门检通过；generate_target实际97.599574秒exit0。13项独立IP和PS_AI BD输出已生成，28项原有HDL参数、生成前后配置一致。4项register_slice实际生成包装无新增活动REGION/USER/CLK2X端口，aclk2x接0，既有寄存器级数和PIPELINES参数一致。

原始5位thread ID、crossbar6位ID及BASE_ID=0/32在新模型中保持。实际生成互联的XSim r2四阶段exit0：两入口各32个ID，64读/64写burst，每burst16拍，读/写各1024拍；地址、ID、返回来源、完整数据、LAST、WSTRB和响应检查通过，加入周期性背压，一次全局在途，不扩大负载。仿真5.941891秒/90秒预算。它验证了该有界路由场景，不代表并发仲裁、完整PS/DDR或候选STOP集成已通过。

相同生成互联进入Procise2025.1.1temp/SVN32494、JFMQL30TAI676H，原生展开/综合16.416899秒exit0，产生真实EDIF；未布局布线或签核时序。空的未使用USER端口等WARN保留。

## 实际阻塞

独立PS包装原生门检，输入使用生成的ps_ai_processing_system7_0_0.v、processing_system7_v5_5_processing_system7.v和原自定义包的ATC依赖，不改其源码、参数或版本。180秒预算，实际8.417573秒exit1，失败位于综合前的展开：

`Module call "PS7_inst" has more terminals than its module declaration "PCPU7"`，ELAB-E-6 / RTL-0902。

生成包装和原自定义模板含PS7_AI_IN/OUT扩展端口；原生工具将PS7绑定为PCPU7时接口不匹配。当前证据只证明此直接RTL路径不兼容，不能断言器件没有AI资源，也不能擅自删除端口、换普通PS、用黑盒伪造完成或改全局原语库。

本机30TAI教程第5–6页提供的是JFM hook加30TAI时序库的Vivado流程，含replace_7z030ai_file；现有授权明确不改全局数据库，所以未执行。随包Vivado→Procise迁移PDF针对FMP100T4，不能直接作为30TAI扩展PS兼容依据。两份原始PDF完整提取文本、SHA与PS失败源码已保存。JFM脚本只做静态阅读：按run.tcl已提供的字节转换查看顶层派发逻辑，未执行该Tcl或加载受保护all_src_files；没有修改工具安装或厂商源码。

## 后续恢复须先闭合的事实

1. 核对本机/厂商给出的30TAI扩展PS到当前Procise的正式映射或网表迁移入口，明确它如何处理全部AI扩展端口；FMP100示例和普通PS7库不足以证明支持。
2. 若使用JFM网表前端，先说明所需hook、库和版本、实际读写路径及私有副本隔离方法。已有“不改全局数据库、不安装/升级工具、不升级自定义PS或AI_Mate”边界保持，不能为了继续构建直接执行替换库命令。
3. 如官方流程必须越过该边界，再提交实际对象、差异、回退与工具兼容证据供用户讨论；不先执行再补授权。已有板测许可不需要重复申请。
4. 接口映射闭合后再在新副本做PS独立门检，审查全部扩展端口绑定和未知/黑盒；随后才组合PS/DDR、HP2读所有权、新CSR解码、PHY、CDC及完整实现。当前无完整候选位流，未下载或改BOOT。

原失败不自动重跑，无后台构建。旧DATA排查独立暂停。证据：[生成及后检](../../tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)、[互联仿真](../../tools/pose-v1/evidence/hdmi-generated-axi-20261015-r2/result.json)、[原生互联](../../tools/pose-v1/evidence/hdmi-native-axi-20261015-r1/execution.json)、[PS完整失败日志](../../tools/pose-v1/evidence/hdmi-native-ps-20261015-r1/stdout.txt)。
