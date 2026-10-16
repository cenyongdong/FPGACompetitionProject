# 用户安装Vivado2018.3后的登记与首次实际预检

2026-10-16（Asia/Shanghai），Windows，工作目录D:/FPGACompetitionProject。用户自行完成安装并要求登记后继续任务；没有由代理下载、安装或修改系统工具配置。

## 实际已验证事实与限制

- 安装入口D:/vivado18.3/Vivado/2018.3/bin/vivado.bat存在；实际启动输出Vivado v2018.3 64-bit、SW Build2405991/IP Build2404404，入口身份见installed-launcher-identity.json。
- 新目录installed-preflight进行小锚点RTL展开/普通PS7库读取，预算60秒。内核随后实际完成，synth_design报告elapsed61秒；PS7输出3305个位引脚、无AI_命名引脚，并打印INSTALLED_PREFLIGHT_COMPLETE。这不是实际扩展PS综合或HDMI验收。
- 外层60秒触发TimeoutExpired，taskkill返回Access denied，驱动又等待15秒超时后exit1，未取得工具进程返回码，整轮明确不通过。工具最后自行退出，不将完成标志回写为通过。驱动v1未能在第二次异常前写execution.json，现记录从外层工具结果恢复的状态并明确来源；原始Tcl、stdout/stderr、Vivado完整log、cleanup.txt及实际引脚文件全部保留。
- 启动Common17-741报告本地TclStore路径'C'无写权限并回退安装目录。原因尚未核实；没有据此断言许可证、逻辑或磁盘故障。并行全树盘点可能增加I/O耗时，未经受控验证不作归因。CIM进程查询曾被系统权限拒绝，之后限制外核对时目标已结束，没有停止其他Python进程；最终EDA进程另盘点。

[本次执行与失败状态](installed-preflight/execution.json)、[完整stdout](installed-preflight/stdout.txt)、[Vivado日志](installed-preflight/vivado.log)、[引脚原值](installed-preflight/builtin-PS7-pins.txt)。没有自动重跑或延长原预算。

## 安装说明、保护及恢复准备

只读目录盘点实际99661文件、28,560,628,023字节，任务自然结束；这是容量盘点，不是全安装字节身份验收。本轮对2018.3九项潜在数据库目标、旧2019.1对应目标、原参考297文件及九份已通过扫描RTL另行SHA核对一致。没有执行replace/reset/hook、完整复制工具、补丁或真实PS综合；不声称整个安装树逐字不变。

已更新PROJECT-PROGRESS、REFERENCES、Done、DIFFICULTIES、讨论记录和候选恢复文档。用户安装的路径取代此前备用下载/代理安装设想；15日原证据及失败不改。文档原值、修订后快照及SHA清单保留。

下一阶段具体对象已准备：[版本及新批次方案](../../../../FPGA/hdmi_candidate/VIVADO-VERSION-PLAN.md)、[私有目标与36个静态恢复路径](proposed-private-target-map.json)。拟完整复制工具至新的r2私有目录，不用硬链接；只在该副本运行原版speed=0，保护用户安装和2019.1。拟复制900秒/总45GiB、元数据90秒、PS综合180秒、RTL90秒；尚未启动，需按超时停止/新预算规则确认后执行。即使2018.3前端通过，Procise的扩展PS绑定仍需独立证明。

监控驱动已修复超时清理异常路径，确保未来先记录状态再停止；当前仅AST静态检查，未运行修复后的EDA阶段。没有板端连接、候选下载、BOOT/SDK/模型/RAW/PS/AI_Mate修改或重启；旧DATA调查仍独立暂停。无完整候选位流或实屏通过结论。
