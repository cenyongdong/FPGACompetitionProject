# HP2 启动异常 r37：原生协议检查实板数据

2026-10-24。PL 作为 AXI 主机经 HP2 读取 PS DDR，首次软件重启加载诊断位流后，在未加载 SDK、未启动读帧的状态复现异常。**累计 AR=0、R=6；原生规则 58／59／61 被捕获。** 保持 AI 四路及 HDMI／旧视频 S01 连接，功能复位未改。测试结束已回原 BOOT。

## 接口及复位

- AI：HC0→HP0、HC1→HP1、HC2→HP2 S00、HC3→HP3；HDMI／旧视频→HP2 S01。
- 监测点为实际 PS7 HP2 AXI 边界，200 MHz／5 ns，与 S_AXI_HP2_ACLK 同一根时钟；GP 100 MHz、PS FCLK0 50 MHz。
- PS_HP2_resetn：PS7 SAXIHP2ARESETN 输出，低有效；仅用于观测和检查器 ARESETN，没有驱动 PL 功能复位。
- PL_HP2_resetn：PL AXI 互联的低有效复位，HP 时钟同步，等待 PL MIG DDR 就绪。
- HP_reset：HP 域高有效功能复位，由系统复位、~FCLK_RESET0_N 和软件复位产生，取反后送 HDMI／旧视频等模块。
- 原生 axi_protocol_checker 2.0 Rev.4：AXI3、64 位数据、32 位地址、6 位 ID、读写容量各 8；输入束旁路寄存 1 个 HP 周期，全部 160 位状态保留。

## 关键时序

| HP 周期 | 观察 |
|---|---|
| 342409 | PS_HP2_resetn 与 PS_RVALID 同采样边沿升高；RID=0x20、RRESP=0、RLAST=0、RDATA=0，PL 互联仍复位、RREADY=0 |
| 342414 | 首次状态：58 AXI_ERRS_RDATA_NUM、59 AXI_ERRS_RID、61 AXI_ERRS_RVALID_RESET；另有建议项92／93／95 |
| 342447 | HP_reset 降为0；PL_HP2_resetn仍为0 |
| 11588729 | PL_HP2_resetn释放，PS_RVALID仍为1 |
| 11588731～734、736～737 | 6拍PS R握手，RID均0x20、RLAST均0、RRESP／RDATA均0 |
| 11588735起 | S01_RVALID为1、S01_RREADY为0；HC2没有AR／R握手 |

协议窗口内检查器 SystemResetn／ready／seen_reset_low 均为1，PL互联仍在复位，所有通道握手为0，未见检查容量超限。报错早于6拍接收。首次160位状态 `0x0000000000000000b00000002c00000000000000`；低字在前数组 `[0, 738197504, 2952790016, 0, 0]`。

## 如何查看本包

- `protocol/protocol.png`：完整协议检查窗口；同名CSV／VCD包含全部AR附加字段、完整五通道及160位状态。
- `cycletrace/bank0.png`：首见PS RVALID的128点；`cycletrace/bank1.png`：PL互联释放附近的128点。两窗各有CSV／VCD／SVG。
- `raw/protocol.json`：未经修改的576位BRAM原始字；`raw/cycletrace.json`：未经修改的双窗口512位BRAM原始字；`raw/release.jsonl`：计数及独立释放事件原值。`analysis.json`保存对应周期／握手汇总。
- `decoders/`：仅依赖Python标准库的解码源码。命令：`python decoders/decode_hp2_protocol.py raw/protocol.json protocol-redecoded.json`，双窗口同理使用decode_hp2_cycletrace.py。
- `diagnostics/`：本轮采样与监测输入寄存源码，供核对采样方式；并非完整Vivado／HDMI工程。

图是真实BRAM采样，非示意／仿真。每窗128个连续点，横轴名义5ns，窗口外无逐拍证据；AR累计0指硬件监测启动至冻结，不覆盖配置前及停钟。RVALID背压保持本身合法。原生报告有输入寄存及内部延迟，5周期是本次实测间隔，不要平移整段原始波形。字段为十六进制；数据／ID／响应／末拍仅在所属VALID有效时有协议含义。

## 希望官方协助确认

1. FMQL30TAI／030ai AArch64平台上，SAXIHP2ARESETN输出具体表示什么状态？其释放对PL适配FIFO／复位及时钟有什么要求？
2. 在所示PS复位输出释放、PL互联仍复位时，HP2出口为何可能出现RID=0x20的RVALID？应优先核对哪一级PL适配／复位连线？
3. 原生58／59／61与本次边沿是否指向已知的复位释放约束？能否提供匹配平台的复位顺序或最小参考工程？

未断电冷启动，配置前事务历史未知，尚不能唯一定位根因。官方已说明HP FIFO在PL，不以PS内部HP FIFO残留作为已确认原因。

## 实际构建身份及恢复

源码基线 `6494ff45c5923d2abc45a88de6a743e87902d6f8`。Vivado2018.3＋原厂适配库／Procise，目标xc7z030ffg676-2／JFMQL30TAI676H；完整布线setup +0.030ns、hold +0.010ns、TNS／THS0，布线错误0。保留原AI两处最小周期例外与既定有限GT处理，未新加例外。

板用bit SHA-256 `1f7f3a4162266330147eb1ba0f4dbf1e94318ee5ea7f29dbbaf64aba23d53fed`；候选BOOT SHA-256 `58ae22619bc8459b0a795989ca5c7025cf941d82c588a4895ea037c2dff3327c`。BOOT中PL之外字节与原BOOT相同。候选启动ID `b5231f10-7b90-4a71-8c90-20851c9d0e8c`。一次候选启动后保存数据并回原BOOT，最终运行ID `38d16aa9-2569-4bcd-8468-fece968ff7bb`；9个启动文件、6个SDK库身份通过，无设备占用，采集连接已关闭。没有SDK／DMA／推理／HDMI START；不能据本次抓波形认定HDMI功能或启动稳定性通过。
