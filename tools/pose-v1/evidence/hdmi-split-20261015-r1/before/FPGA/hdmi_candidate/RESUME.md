# HDMI候选的当前状态与继续入口

2026-10-15用户明确唤醒后，已恢复离线候选。当前本轮仿真在90秒外层预算触发超时后停止，未自动重跑；新分组入口已准备，等待用户确认新批次。没有后台续跑。旧DATA坏读调查继续单独暂停。

## 授权范围

保持1080p60，在隔离目录修正独立显示时钟、AXI读握手、可观测停止/换帧接口，做RTL与Procise兼容/构建核验；暂不上板、不替换BOOT，不迁移/升级既有IP或工具。暂停时17项源码身份在本次恢复前全部核对一致；历史见[暂停检查点](../../tools/pose-v1/evidence/hdmi-candidate-pause-20261015-r1/CHECKPOINT.md)。

## 本次实际结果

- r3复现64字节对齐、页尾偏移4032时的4KiB burst越界拒绝；修正按页拆分后r4实际exit0。偏移0/64/4032三个完整1080p帧均518400个64位字/4147200字节，逐地址/数据通过；相应32400/32401/32401个burst。
- 新增双时钟FIFO、连续1080p扫描及scanout组合。停止保持HS/VS/DE，活动区输出黑色；欠载报faults位3并停止新请求、排空在途AXI。
- Procise scanout r1原生展开/综合exit0，10.620秒，真实EDIF中1个RAMH36E1；未布局布线、完整CDC/时序或电气签核。
- r5编译/展开exit0，原始xsim.log记录所有断言完成：完整2073600像素比对、2200×1125时序、欠载排空、像素时钟停止时STOP，以及原AXI/CSR/控制/三基址/FIFO用例。但外层simulate调用90秒TimeoutExpired、驱动exit1，**整体不验收**。原日志完整保留，不能只摘PASS掩盖超时。
- 原工程101项引用中93存在、8项JFM hook文件缺失，JFM_Kits中有6项同名；与旧索引一致。没有安装hook、修改数据库或自动迁移IP。PS/DDR/TMDS仍未完成集成。

## 已准备、未执行的新批次

`scripts/simulate.py`增加独立core/pixel展开根，避免长扫描期间继续驱动无关单元测试；FIFO测试完成后关闭自己的测试时钟。每阶段仍90秒，失败保存原始输出/源码；超时仅清理本次进程树，绝不自动重试。新入口仅做Python AST静态语法检查，未动态验证，原r5失败不回写。

如用户明确同意新批次，依次执行：

1. Windows，工作目录D:/FPGACompetitionProject；先确认r6/r7新目录不存在、工具版本和候选源码身份一致。`python FPGA/hdmi_candidate/scripts/simulate.py r6 core`：控制/AXI/CSR与三基址完整DMA帧组，每阶段90秒。
2. 第一组exit0且PASS/无Fatal后，再`python FPGA/hdmi_candidate/scripts/simulate.py r7 pixel`：FIFO与完整1080p扫描组，每阶段90秒。
3. 任一非零、超时、Fatal或缺少PASS，保存并停止，不启动下一组、不复用失败目录、不延长预算。结束盘点本批工具进程并归档最终SHA。

新批次不含板端运行、BOOT替换或IP迁移。两组通过也仅说明离线逻辑成立，不能跳过[集成与约束门槛](INTEGRATION.md)。

## 尚未完成

HP2读写所有权接入、GP总线适配及地址映射；真实PLL/像素/串行时钟与锁定观测；复位和Gray/邮箱CDC约束；原生TMDS序列器、电平/封装/BANK与1485Mb/s物理能力；PS/DDR/AI/IP配套构建、布局布线、setup/hold/未约束路径审查、位流和实屏。720p取舍须另议。

显示器现场仍是已接入但不支持时序，误点“稳定画面”无效。原始参考源码、当前BOOT/SDK/模型/RAW、CPU注册和NPU分配保持。完整执行、原值与前后身份见[本轮报告](../../tools/pose-v1/evidence/hdmi-resume-20261015-r1/REPORT.md)。
