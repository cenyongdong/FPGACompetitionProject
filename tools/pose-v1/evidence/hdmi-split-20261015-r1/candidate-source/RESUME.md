# HDMI候选当前状态

2026-10-15本批授权的离线分组验证与TMDS常量修正已完成。无后台续跑，暂不上板、不替换BOOT；旧DATA调查继续独立暂停。

## 最新授权与实际结果

用户明确认可r5内核全部像素比对、4KiB修复与FIFO综合成果，并将该轮超时归为外层监控门限；原进程exit1和失败日志不回写。用户批准新r6 core/r7 pixel独立目录、每阶段90秒，要求修正uihdmitx.v时钟ASCII常量。

- r6 core全阶段exit0，外层仿真11.540083秒，无超时。AXI10类、控制7类、CSR及偏移0/64/4032完整帧均通过，各4147200字节；不越4KiB。
- r7 pixel全阶段exit0，外层仿真30.102087秒，无超时。完整2073600像素/2200×1125扫描、异步FIFO复用/部分字flush、欠载排空和像素停钟STOP通过。
- 隔离`rtl/display/uihdmitx.v`的UFAMILY/7FAMILY两处均改10'b1111100000，原参考保留。实际选择的Lite 7FAMILY模型新/旧各128周期严格波形通过：旧高2ns/低8ns，新高低各5ns，周期10ns，P/N互补。
- TMDS r1/r2前端配置失败、r3非目标UFAMILY精确边沿失败保留；r4独立Lite目标全阶段exit0，外层仿真6.418892秒。UFAMILY附加99ps级边沿差原因未闭合，不能写作双分支严格波形或实板验收通过。只读原VCD复核两分支常量/位图通过，不重跑r3联合负载。
- 9份生产扫描RTL与前轮r5和Procise scanout综合逐位一致；原生1个RAMH36E1结果保持。本次为100MHz参考序列器模型验证，不是148.5MHz实板测量或Procise物理时序签核。

## 已执行入口与证据

Windows，工作目录D:/FPGACompetitionProject。实际执行`python FPGA/hdmi_candidate/scripts/simulate.py r6 core`，通过后`... r7 pixel`，以及独立TMDS目标验证。均各阶段90秒、安全监控，不延长或复用失败目录。[本批报告](../../tools/pose-v1/evidence/hdmi-split-20261015-r1/REPORT.md)包含源/原值/VCD/前后文档SHA/退出码和停止条件；[前轮报告](../../tools/pose-v1/evidence/hdmi-resume-20261015-r1/REPORT.md)与[原暂停检查点](../../tools/pose-v1/evidence/hdmi-candidate-pause-20261015-r1/CHECKPOINT.md)保留历史。

## 下一步的技术门槛

PS/DDR/GP/HP2所有权和地址映射、厂商IP配套/JFM引用、原生TMDS/规范复位、实际PLL/像素/串行时钟观测、Gray/邮箱CDC约束、封装/BANK/电平与1485Mb/s能力，以及布局布线、setup/hold/未约束路径和实屏。详见[集成契约](INTEGRATION.md)。不能将并行scanout综合或参考序列器行为仿真扩展为完整系统构建成功；工具/IP迁移等重大影响需按已有范围讨论。

本批无板端SSH/Docker/新Procise构建，无位流生成/下载/BOOT替换。原始参考源码、当前BOOT/SDK/模型/RAW/CPU注册/NPU分配保持。显示器最近实际用户现场仍为已接但时序不支持，未以本机仿真改写现场结果。
