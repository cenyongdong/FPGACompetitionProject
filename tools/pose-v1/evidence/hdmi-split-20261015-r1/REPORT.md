# HDMI分组验证与TMDS时钟常量修正

执行日期：2026-10-15，Asia/Shanghai。执行平台Windows，工作目录D:/FPGACompetitionProject。用户明确认可r5内核像素比对和4KiB/FIFO成果，批准新r6 core/r7 pixel独立目录、每阶段90秒，并要求修正uihdmitx.v时钟字符串。原r5驱动TimeoutExpired/exit1完整保留，用户认可与实际进程退出结果分开记录。

## 本批结果

| 工作 | 实际结果 | 证据 |
|---|---|---|
| 恢复前核验 | 前轮24项候选文件SHA相同、r6/r7目录未存在、现有XSim入口存在；保存文档/候选before快照 | preflight.json、before/ |
| r6 core | 编译/展开/仿真全部exit0，无超时；仿真外层11.540083秒 | [r6执行](../hdmi-candidate-sim-20261015-r6/execution.json)、[日志](../hdmi-candidate-sim-20261015-r6/simulate.stdout.txt) |
| r7 pixel | 编译/展开/仿真全部exit0，无超时；仿真外层30.102087秒 | [r7执行](../hdmi-candidate-sim-20261015-r7/execution.json)、[日志](../hdmi-candidate-sim-20261015-r7/simulate.stdout.txt) |
| 常量修正 | 隔离副本uihdmitx.v的UFAMILY/7FAMILY两处时钟txdata均改10'b1111100000；原参考字节不改 | clock-literal-origin.json、clock-literal.patch、uihdmitx.original.v/uihdmitx.fixed.v |
| Lite目标波形 | 真实参考OSERDESE2包装/OBUFDS与UNISIM/secureip模型，旧/新各128周期严格边沿检查通过；r4五阶段exit0，无超时 | [TMDS r4执行](../hdmi-tmds-literal-20261015-r4/execution.json)、[实际日志](../hdmi-tmds-literal-20261015-r4/simulate.stdout.txt)、simulation-copy/tmds_clock.vcd |
| 双分支VCD独立审查 | 读取r3已捕获波形、不重跑内核；两分支常量输入正确，四输出各128字符/1280位中心样本与差分互补通过 | tmds-vcd-review.json；非目标UFAMILY精确边沿差另列，不记双分支严格波形通过 |

## core与pixel的范围

r6保留原AXI10类、控制7类和CSR门检，三种帧基址偏移0/64/4032各完整518400个64位字、4147200字节，全部地址/数据及背压检查通过；32400/32401/32401个burst，页尾不越4KiB。r7完整比较2073600个RGB像素，检查2200×1125/HS44/VS5扫描、FIFO异步环绕和部分字flush、欠载报错后排空以及像素停钟后的STOP。没有为了过门修改生产RTL、缩小完整帧/像素数量或放宽这些门禁。

本批r6/r7使用分离的展开根，FIFO小用例完成后停止自己的测试时钟。每阶段仍90秒，任何超时/非零/Fatal/缺PASS保存并停止，不延长预算、不复用失败目录。实际两个新批次均正常结束。r5当时断言PASS而外层超时，结合相同生产RTL的新分组通过，支持该轮失败来自外层执行预算；不能由此推导未测输入/物理层绝对无故障。

## 时钟常量修正与波形

问题不是Verilog解析器不允许字符串，而是语义/位宽："1111100000"为80位ASCII串，连接10位txdata时截断为0x030，即0000110000；预期10'b1111100000为0x3e0。低位先发送时旧图案每10位只有2位高，新图案有5位高。

候选路径：[rtl/display/uihdmitx.v](../../../../FPGA/hdmi_candidate/rtl/display/uihdmitx.v)，第92/136行。只修改两处功能常量与对应说明注释，保留原始字节编码、厂商版权和其余逻辑。原Docs参考文件保留，未覆盖失败快照。此副本用于本轮实际TMDS仿真；尚未加入原生Procise物理顶层，不能误称当前BOOT已经修正。

原frame_to_ps_largebuf.v:472明确选择7FAMILY，故Lite目标回归保留严格边沿条件。模型使用100MHz像素、500MHz DDR串行时钟，验证字符图案和分频比例；没有模拟PLL，也不将100MHz模型波形称为实板148.5MHz测量。

| Lite 7FAMILY实测模型波形 | 修正前 | 修正后 |
|---|---:|---:|
| 每周期时间 | 10000ps | 10000ps |
| 高电平宽度 | 2000ps | 5000ps |
| 低电平宽度 | 8000ps | 5000ps |
| 占空比 | 20% | 50% |
| 严格检查 | 128周期 | 128周期 |

测试在RGB/HS/VS/DE持续变化时检查时钟周期/高低宽度以及P/N互补，并核对实际序列器txdata端口。旧设计在模型中确实出现20%占空比，修正后恢复50%；这是参考数字发送链路的因果对照，未证明当前BOOT必然含此缺陷，也未完成Procise原生序列器、IO/封装/BANK/电气、742.5MHz/1485Mb/s、布局布线、PLL抖动或实屏验收。

## 排查失败记录与非目标分支

- TMDS r1：把参考.v与测试.sv合用SystemVerilog模式，E3参考代码以bit作generate块名，与SV关键字冲突，Verilog编译exit1。保存并停止，未启动内核。修正为分别按Verilog/SystemVerilog编译，源码逻辑不改。
- TMDS r2：展开缺B_OSERDESE2，exit1，未启动内核；本机xsim.ini和模型源码表明需要已有secureip库。新增-L secureip，未安装/修改工具或IP。
- TMDS r3：双方展开/运行工具均exit0，联合严格波形断言因UFAMILY一次低宽4901ps而非5000ps失败，门检exit1，保存VCD后停止此联合负载，未重复运行同一联合测试。UFAMILY并非本工程选用分支，不能把它的现象记作Lite失效或强行放宽Lite边沿门检。
- 只读VCD审查在2.5–3.78µs窗口检查128字符：7FAMILY旧高2ns/低8ns，新高低各5ns，严格成立。UFAMILY新输出高宽5000/5099ps、低宽4901/5000ps，位中心仍每10位5高，旧输出仍2高；两分支实际txdata均符合修正。出现99ps级边沿差的原因没有闭合，原语模型的100ps路径项是线索，不能断言是已查明根因或映射到本板。
- TMDS r4是独立Lite目标负载，仅实例化实际选用7FAMILY旧/新链路，严格5ns/5ns与2ns/8ns门检保持，连续128周期通过，所有阶段exit0；不是将r3改写为整体通过。UFAMILY额外严格边沿诊断仍保持未通过。

以上前端修正与新目标验证均用独立目录保留源与日志，未修改生产序列器实现、未迁移IP/数据库、未连接板端。原有序列器组合反馈复位及原生物理适配仍是后续待闭合项，不把修正常量当作物理层所有隐患已经清零。

## 执行入口、产物与停止条件

实际执行：`python FPGA/hdmi_candidate/scripts/simulate.py r6 core`，第一组通过后`... r7 pixel`；TMDS脚本r1/r2/r3用于联合探索和前端排查，r4用于Lite目标。所有XSim编译/展开/仿真各90秒，原始退出码和工具日志在各execution.json/文本中；Fatal即便xsim退出0也拒绝。`review_tmds_vcd.py`只读已保存VCD，无内核重跑。

本批未新增Procise综合：9份生产逻辑RTL未改，前轮scanout原生综合1个RAMH36E1结果保持；本次改动是参考发送层两处常量，验证为XSim参考模型，不能把它写成Procise物理层综合/时序通过。新候选源码/前后文档SHA/参考38项身份/进程盘点与完整产物清单存于本目录，原r5及前轮哈希清单保持。

已完成本次授权的分组验证和目标常量修正/行为验证。PS/DDR/GP/HP2接入、TMDS原生物理适配、CDC/布局布线/时序及实屏仍未完成。旧DATA保持暂停，当前BOOT/SDK/模型/RAW/CPU注册/NPU分配不改，暂不上板、不生成或替换BOOT，无本批后台作业。
