# HDMI候选当前状态

2026-10-15。用户已允许实板、隔离同配置重建、16根IP修订白名单和有限衍生字段例外；旧DATA调查独立暂停。当前无后台构建，尚未下载候选或更换BOOT。

## 最新实际结果

实板只读身份和12寄存器核验通过，BOOT/六份SDK/内核保持。原r6 core/r7 pixel及Lite TMDS常量128周期结果保持，9份生产扫描RTL未改。纯输出OBUFDS→ODU_DS在实际引脚的兼容探针布线通过，但无有效STA端点，不是1080p60/1485Mb/s签核；双向IODU尝试因PLACE0854失败并已拒绝。

新r3有限契约门检通过，Vivado2019.1目标生成97.599574秒exit0；28项原有HDL参数、生成前后配置和四regslice生成端口核验通过。实际生成AXI3互联两入口各32 ID、64读/64写完整16拍burst，数据/地址/路由/背压通过，一次全局在途，仿真5.941891秒/90秒预算；Procise原生互联展开/综合16.416899秒exit0。

完整候选当前受阻：自定义PS生成包装直接原生展开时，PS7_inst端口超过PCPU7声明，ELAB-E-6/RTL-0902，8.417573秒exit1停止。没有改PS包/参数、AI_Mate或全局库，没有用黑盒替代。当前没有完整系统位流，显示器最近用户现场仍为“不支持当前时序”。

## 恢复入口与边界

先阅读[PS适配状态](PS-ADAPTATION-STATUS.md)，闭合30TAI扩展PS的正式映射/网表迁移依据；FMP100迁移流程不能直接套用。本机30TAI教程的全局库替换未执行，现有不改全局数据库/不安装升级/不升级自定义PS或AI_Mate边界保持。已有板测授权持续有效，不重复申请；候选下载仍需真实完整实现产物、扫链及硬件停止/安全切换条件。

PS/DDR/HP2/GP所有权、CSR解码、原生PHY/规范复位、CDC及完整实现/时序/实屏仍待验。无FD owner不证明在途DDR读停止。BOOT/SDK/模型/RAW/正式CPU注册/NPU分配保持，不增加重启许可。失败目录和原门检不回写，不自动复跑失败负载。

[本批总报告](../../tools/pose-v1/evidence/hdmi-bringup-20261015-r1/REPORT.md)、[生成后检报告](../../tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3/REPORT.md)、[已获批准的有限规则](IP-CONTRACT-REVIEW.md)、[集成契约](INTEGRATION.md)。历史分组结果见[前批报告](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)，原失败均保留。
