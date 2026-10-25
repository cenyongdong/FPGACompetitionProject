# r45 同位流、同启动有限消费诊断

基于 r38 合格连接，AI HC0→HP0、HC1→HP1、HC2→HP2 S00、HC3→HP3、HDMI→HP2 S01 保持。
新增 0x400b0800 控制别名；消费默认 WAIT，只允许一次 CONS，最多256拍/4096 HP周期，64周期空闲结束。
先完整保存启动异常与原生协议检查历史，再同启动单次消费；CHKR 只重新武装被动协议检查器，不能复位功能接口。
BRAM bank0保留首次PS RVALID窗口；bank1改为软件启用消费后的首次RUN窗口，格式0x02028010。
source目录为该次实际构建覆盖层；原r38及工厂PS/适配IP不变。新控制CDC用5/10/5ns显式约束，初次构造旧例外时排除新增诊断对象，不新增false path。

硬件仿真21例通过（包括实际互联/HDMI读核边界注入）；这些结果不等同于实板通过。
软件子目录仅保留相对r39/r40改变的源：诊断计数世代加2，复用r40时间记录，200ms采纳条件、数学、SDK、模型与NPU分配不变。
实际构建目录：D:/FPGACompetitionProject/.local/hp2-deferred-consume-20261024-r45。
本轮完整原生记录、物理检查、位流身份及板测结论：tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45/。
