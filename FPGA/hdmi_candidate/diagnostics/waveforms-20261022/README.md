# HDMI / PS HP2 实测波形与原始记录

整理日期：2026-10-22。用于厂商技术答疑；本包完全来自已保存实板记录，没有新增启动或板端访问。

## 先看什么

- `01_r29_isolated_fault.png`：最新隔离故障，最早观察状态与PL释放附近放大，附HP原始首事件及短窗计数。
- `02_same_image_healthy_vs_fault.png`：完全相同隔离bit／BOOT的健康与故障启动对照。
- `03_connected_vs_isolated_fault.png`：视频保持连接与源端隔离时的两个故障样本。
- 同名SVG可缩放；PNG已检查中文和版面，适合直接发群。

## 数据是什么，不能解释成什么

这些图是FPGA内被动事件记录器的实测数据重绘，**不是ILA逐周期连续抓波，也不是RTL仿真波形**。

GP记录器以名义100MHz采集经同步后的电平变化，保存每条变化的64位GP周期。三例事件表均未溢出。
图中阶梯线表示日志中同步电平的保持关系；不能据此排除比同步采样更短的原始脉冲。实心点表示首条记录或该信号的记录变化。
记录前未知区域在图中标灰；初态resetn=1不证明捕获到了释放边沿。

HP记录器以名义200MHz直接记录原始握手累计和首RVALID事件。HP与GP计数起点、停钟和FREEZE切面不同，**不能把两个域的周期数直接对齐**。
图中的纳秒／微秒只按既有时钟约束折算，不是示波器测得的周期。未捕获配置前及无观测时钟阶段。

没有保存逐拍RDATA、六次R握手的各自时间戳或原生ILA的WDB／LTX文件。HP累计R=6是六次原始管脚握手，不证明六笔合法事务。
RVALID=1且RREADY=0本身符合背压保持规则；疑点是请求来源和初始化／复位经历。
本包不能直接证明PS内部FIFO占用、FIFO残留或DDR颗粒硬件故障。

## 三个样本

| 标识 | 视频连接 | 结果 | SDK／推理／HDMI START |
|---|---|---|---|
| r26 | 原双输入HP2共享结构，功能视频分支仍连接 | 故障，PS AR=0、原始R=1 | 全部0 |
| r28 | S01全部27个主机输入置0，双输入互联内部保留 | 单次健康，PS AR=0、原始R=0 | 全部0 |
| r29 | 与r28完全相同隔离bit／BOOT | 再次启动故障，PS AR=0、原始R=6 | 全部0 |

AI四路均保持HC0→HP0、HC1→HP1、HC2→HP2互联S00、HC3→HP3。
r28／r29的BOOT SHA256均为`f4bed59ec07751bcd7eaac332d9524675e071a4eff1226a4f9b5bdd1642bde04`。
隔离版只断开视频源端，保留S01互联内部；图中S01返回并不是已断开的功能HDMI reader输入。
r29计划30分钟无SDK驻留，但启动记录已锁存故障，首次检查即提前冻结取证；**30分钟未完成，不能报告长期通过**。
每例均已完成原BOOT回退，本次导出没有写BOOT、重启或SDK操作。

## 文件及复核

- `raw/r*/startup_snapshot.jsonl`：原始128字PS／PL记录及19字启动见证，从既有板端归档逐字节提取。
- `raw/r*/axi_snapshot.jsonl`：原始104字六边界快照；r29另含驻留提前停止的原始时长／标志记录。
- `raw/r*/probe.stdout.log`与`probe.stderr.log`：对应原采集程序输出；不是人为改写的诊断结论。
- `raw/r*/case.json`及`capture_manifest.json`：样本身份、BOOT身份、时钟域和冻结位置。
- `decoded/r*_startup.json`：由包内同一解码器从原始字解码的事件、首事件和计数。
- `tables/`：GP事件、HP首事件和104字逐字含义，CSV保留十进制／十六进制原值。
- `decoder/decode_ps_release.py`：实际解码逻辑，使用Python标准库；不访问板端。
- `decoder/ps_release_witness.sv`、`ai_read_monitor.sv`：实际记录器RTL，供核对采样／冻结／字布局；不是完整FPGA工程。

104字通道次序：0=HC0、1=HC1、2=HC2、3=HC3、4=S01视频入口、5=HP2互联对PS出口。
通道15号字表示按ARLEN累计的预期返回拍数，不能当作错误计数或完成证明。
首R管脚编码为`{RLAST,RRESP[1:0],RID[5:0]}`：r26为0x120，r29为0x20，二者RID均为32。

## VCD查看说明

`vcd/r*_GP_full.vcd`保留完整GP事件时间轴；`r*_GP_release_zoom.vcd`仅保留PL释放前40至后15个GP周期，适合直接查看。
缩放文件将左边界重设为时间0，`original_GP_cycle`保留原GP周期；`$timescale 10ns`来自名义GP100MHz。
VCD只包含已记录的同步电平变化，没有添加时钟、R握手脉冲或RDATA。缩放左端电平由此前最后一条记录保持而来。
完整记录首条事件之前及所有文件结束之后置X／`observation_valid=0`，表示不在覆盖范围。
可用支持VCD的波形查看器打开，但查看器中的曲线仍是事件记录重建，不能称为原生ILA采样。

## 主要信号对应关系

| 图中信号 | 实际观测边界／内部名称 |
|---|---|
| PS HP2 resetn | PS输出，经`diagnostic_ps_resetn`导出；不是PL给PS的复位输入 |
| PL HP2 resetn | `proc_sys_reset_1_peripheral_aresetn`，经`diagnostic_hp2_resetn`导出 |
| DDR calibrated | `ddr3_init_done`，PL侧MIG校准就绪 |
| PS ARVALID / RVALID | `axi_interconnect_4_M00_AXI_ARVALID/RVALID`，`diagnostic_hp2_read[60]/[62]` |
| S01 ARVALID / RVALID | 外围`S_AXI_HP2_ARVALID/RVALID`，原视频分支与互联之间 |

图中放大窗的GP先后关系不等于源域精确传播延迟。若进一步需要逐拍RREADY／ARREADY／RDATA及配置前事务，需要另行准备厂商适配支持的连续采样方案；本包没有伪造这些缺失信号。
