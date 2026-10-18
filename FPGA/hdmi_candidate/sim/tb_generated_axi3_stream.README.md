# 有限AXI3连续读测试台

`tb_generated_axi3_stream.sv`是独立模板，旧测试台及生成DUT不改。此文件新增时仅进行了源码审查；编译、仿真及结果由主执行器另行记录，不能将代码存在称为验证通过。

## 实际对象与展开契约

核对对象为`.local/hdmi-live-20261017-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v`内`ps_ai_axi_interconnect_3_0`，以及其实际可达生成包装和原厂仿真模型。当前对应`ps_ai_xbar_4.xci`的AXI协议值为1（AXI3），ID宽6，两个来源的线程ID宽5、BASE_ID=0/32、READ_ACCEPTANCE各8，M00_READ_ISSUING=8、C_S_AXI_SINGLE_THREAD全0；M00地址窗口是从0开始的30位范围。执行驱动必须在使用前重新核对此配置及源码身份，不凭自动编号猜测角色。

四个`GENERATED_*`标记与旧模板相同：展开实际模块端口声明、DUT命名连接、所有时钟/复位连接及剩余输入初始化。顶层名为`tb_generated_axi3_stream`。

- 所有DUT output声明为wire。
- 时钟及复位input声明wire，分别连续连接共同`clk`与`rstn`。
- 以下七个input声明wire，由TB连续赋值，必须从输入初始化排除：`S00_AXI_rready`、`S01_AXI_rready`、`S00_AXI_bready`、`S01_AXI_bready`、`M00_AXI_arready`、`M00_AXI_awready`、`M00_AXI_wready`。
- 其他input声明reg，初始化为0；AR源与M00响应在下降沿驱动。`M00_AXI_rvalid/rid/rdata/rresp/rlast`、`M00_AXI_bvalid/bid/bresp`均为reg。
- 依赖应由当前生成BD递归识别，不能复用旧2019.1自动编号清单。沿用实际vendor模型及其.vh文件；不替换为简化自制互联。

## 流量与检查

单个200MHz公共时钟，复位在边沿之外释放。两个源同时提交各256个读请求，合计512事务/3456个64位数据拍；源端最大各8在途，下游最多8在途。burst长度固定轮换1/2/8/16拍、SIZE=3、INCR。每个事务地址使用独立4KiB页，半数正好在页边界结束，所有地址8字节对齐且不跨4KiB；地址均在已核窗口内。未发送非法跨页流量，也不声称非法输入拒绝行为已测。

两源均覆盖全部32个ID，后64个请求重复四个ID，使同ID有机会同时在途。下游模型只对已握手接受的请求响应，使用最多8个请求的台账；每次选最新的可响应事务，保留同一完整RID严格FIFO。不同已接受RID可改变burst返回顺序；同一burst不交错。正常、SLVERR、DECERR响应均逐拍传播并核对，不产生EXOKAY。该行为以实际crossbar多ID支持为前提，不推导真实PS会采用相同返回策略。

源AR及模型R均独立于READY产生VALID，并在背压期间保持VALID及全部相关payload。TB同时检查DUT的M00 AR与两侧R在背压期间不变。M00 ARREADY的容量判据在下降沿锁存，避免posedge台账更新与DUT采样竞争。源端和主端分别按真实VALID&&READY计数，scoreboard检查地址、来源标签/ID、长度、正常响应数据、RESP、LAST、无重复/无额外响应、同ID顺序，以及下游接受数据与上游返回的守恒。错误响应的数据值在AXI契约中未指定，不据此拒绝合法实现；错误时的ID、RESP、LAST及背压稳定性仍检查。来源的请求接收记录与下游的响应记录独立维护。

所有真实握手写入`generated_axi3_stream.csv`，包括周期、边界、来源、序号、ID、地址、beat、长度、LAST、RESP及数据。最终摘要包含submitted（两入口AR握手）、accepted（M00 AR握手）、downstream/upstream beats、completed（入口末拍握手）、各峰值、ID/长度/RESP位图、不同ID改序次数及M_AR/M_R/两个S_R的实际背压周期。PASS要求全部512事务完成、上下游3456拍、ID全覆盖、四种长度全覆盖、RESP位图1101、M00在途峰值至少2、改序次数大于0，且M_AR和两个S_R实际出现背压。任何断言、覆盖不足或60000逻辑周期watchdog失败均立即fatal并保留CSV；不可将watchdog结束当PASS。

## 边界

本测试仅验证实际生成的AXI3读互联功能，写路径保持空闲；未包含AI_Mate、PS硬核、HP issue-cap控制、PL专有512位接口、DDR控制器、SDK、系统复位恢复或物理实现。此处的200MHz仅定义逻辑时序，不是板上200MHz时序签核。无板端连接、BOOT安装、重启或失败DMA重试授权；旧DATA调查不涉及。
