# HDMI候选恢复入口：用户已要求暂停

暂停日期：2026-10-15。**只有用户明确唤醒后才继续，不启动后台续跑。** 原DATA坏读调查仍单独暂停，唤醒HDMI不自动恢复DATA。

## 已有授权与停点

用户已批准在隔离工程副本中修正独立显示时钟、AXI读握手和可观测停止／换帧接口，保持1080p60目标，先做RTL与Procise兼容性／构建核验，暂不上板、不替换BOOT。随后用户明确要求在合适位置中断，等待唤醒。

停在候选模块第一轮行为验证和原生展开／综合之后。没有本批Procise、xsim、xelab、xvlog进程；全部已启动工具调用已返回。较早板端只读探针已退出并回收、SSH结束，FPAI已停止。CIM命令行盘点受权限限制，随后仅以Get-Process核对上述四种工具进程为空，没有申请额外权限或结束用户其他进程。

## 已实际完成

- `rtl/hdmi_clock_fmsh.v`：Procise原生PLL_MM_SIMPLE／GLCLK／IOCLK，使用100MHz独立参考，数学参数对应148.5MHz像素和742.5MHz串行支路，脱离SDI锁定选择。原生综合保留参数；未进行PLL器件模型仿真、物理频率或抖动验证。
- `hdmi_axi_read.v`：一次在途读事务，FIFO提交及结束绑定RVALID&&RREADY，停止保留已发布AR并排空已接受读，即使FIFO满／像素停钟也可丢弃数据完成总线事务；缺失RLAST时不伪造idle。
- 命令邮箱、帧控制、寄存器bank与组合边界：单命令跨域、原子快照、帧边界采用地址、stop ID和safe_idle，默认禁止DMA。候选偏移尚未映射到当前板端地址；现有BOOT不可按这些新接口访问。
- `hdmi-candidate-sim-20261015-r2`：AXI10类、控制7类、CSR字节掩码/命令稳定/快照/非法部分命令检查通过；完整1080p帧32,400 burst、518,400个64位字、4,147,200字节在确定性背压下按地址与数据核对通过。r1为此前较小用例通过，各自范围保留。
- `hdmi-candidate-procise-clock-20261015-r1` 与 `...core...r1`：Procise2025.1.1temp/SVN32494、JFMQL30TAI676H原生展开与综合exit0，EDIF已生成。分别约6.752秒／8.677秒。core使用带CSR的顶层和显式地址窗口，未因默认空窗口将DMA逻辑全部裁掉。综合警告及原日志保留，尚未完整签核。
- 之前原始参考RTL的200MHz→80.81Hz、消费停止卡读、VS门控发请求、AXI背压提前完成缺陷均已复现。当前现场显示器已接，仍提示不支持时序；误点“稳定画面”作废。12项显示寄存器实板读取及BOOT／六库／内核前后一致通过；实板实际像素频率未测。

## 唤醒后的顺序与待查事项

1. 先核验暂停目录的源码SHA与实际产物，不覆盖旧证据或复用失败目录。读取最新用户指令，确认仍处于仅离线候选范围。
2. 审查地址边界：控制器目前接受64字节对齐帧基址，读主机拒绝跨4KiB burst；需验证非128字节对齐基址，决定按页边界拆分burst或收紧接口契约。当前已过完整帧测试的基址按4KiB对齐，不能推广为任意64字节对齐地址。
3. 核对真实原工程集成：本轮是独立候选模块和CSR本地总线边界，尚未接入PS/AI顶层、原双时钟FIFO、像素读出、帧复位／underflow、TMDS PHY、AXI-Lite适配和实际地址解码。不能称整条HDMI候选系统已经集成。
4. 建立真实时钟／复位／CDC约束、邮箱多位数据保持窗口、频率／lock观测，核对原生PLL参数及目标器件物理限制。native synthesis仅证明前端和综合接受，不是时钟频率或时序签核。
5. 依核实的原工程/IP配套决定后续构建；原IP迁移、工具版本变更等遇到重大影响先讨论。尚未布局布线、setup/hold/未约束路径验收、位流生成或上板。1080p60的Lite IO兼容性风险保持，改720p须另行确认。

## 证据入口

- [此前核验与原始缺陷复现](../../tools/pose-v1/evidence/hdmi-contract-validation-20261015-r1/REPORT.md)
- [当前候选行为结果](../../tools/pose-v1/evidence/hdmi-candidate-sim-20261015-r2/result.json)
- [原生控制综合](../../tools/pose-v1/evidence/hdmi-candidate-procise-core-20261015-r1/execution.json)
- [原生时钟综合](../../tools/pose-v1/evidence/hdmi-candidate-procise-clock-20261015-r1/execution.json)
- [暂停快照与身份](../../tools/pose-v1/evidence/hdmi-candidate-pause-20261015-r1/CHECKPOINT.md)

所有板端模型、RAW、CPU注册、NPU分配、SDK、BOOT及正式软件保持；当前暂停期间不继续上述待办。
