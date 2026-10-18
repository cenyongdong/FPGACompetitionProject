# 六边界被动读路径观测器

`ai_read_monitor.sv`仅接收输入并提供独立CSR响应；不产生AI、AXI、DDR、HDMI或功能复位控制。它不是修复，也没有事务台账、历史环、数据内容或全链完成判断。新增扇出和资源仍可能影响物理实现，必须单独CDC、时序和实际身份核验。本模块及TB新增时尚未执行EDA或板测；具体结果由主执行器保存。

## 输入布局与时钟

`channels[767:0]`分为六个128位通道，次序HC0、HC1、HC2、HC3、HDMI入口、HP2互联对PS出口。每通道：ADDR31:0、ARID37:32（6位，5位接口补0）、LEN41:38、SIZE44:42、BURST46:45、LOCK48:47、CACHE52:49、PROT55:53、QOS59:56、ARVALID60、ARREADY61、RVALID62、RREADY63、RID69:64、RRESP71:70、RLAST72；127:73保留。所有输入均必须是同一200MHz source_clk同步信号；不直接采异步引脚。

`source_flags`各位为0 DDR校准、1 DDR UI reset、2 hp_clk_rst、3 HP2 ARESETN、4 pl_rst_n。全局复位观察累计条件是bit2为1或bit3为0，只记录同源观察值，不驱动或改变功能复位；接入者须核对真实时钟/极性。csr_clk为独立CSR域，两域各异步置位、三级同步释放自身复位。

## CSR和命令

自有512字节对齐窗口，模块使用地址低9位；本次隔离接入基址0x400b0400，范围至0x400b05ff。外部译码负责确保仅该窗口被选中。

| 偏移 | 内容 |
|---|---|
| 0x000 | 读bit0 busy、bit1 sticky command_error；写1 ARM，写2 FREEZE |
| 0x004 | ABI 0x41495201 |
| 0x008 / 0x00c | 已接受请求代数 / 已完成代数，32位回绕 |
| 0x010 | 冻结快照字数104 |
| 0x040—0x1dc | 104个冻结32位字 |

ARM仅在未忙且未处于已ARM状态时接受，清零诊断计数、样本和周期后开始观察。ARM ACK回到CSR后清零已公布快照，再置为可FREEZE；调用者只有取得该ACK并核对状态才可开始DMA。ARM不操作数据通路。FREEZE仅在ARM ACK完成且未忙时接受；其源域识别沿不再计数，锁存的恰好是前一有效source沿结束后的诊断状态。因此周期及事件时间戳使用ARM后的0起算标签；FREEZE识别沿本身排除。冻结后计数和快照都保持，直到下一次显式ARM。模块允许冻结后重ARM；SDK helper可以进一步限定首次代数为0。

ARM与FREEZE各使用独立的请求toggle、源域ACK toggle及各两级ASYNC_REG同步器，没有多位命令跨域。CSR每次只允许一个未完成命令；忙时、未ARM的FREEZE、尚未冻结的再次ARM、非法地址/值均拒绝并置sticky command_error，不增加请求代数。错误仅全局resetn清除，后续完成不能将已失败命令冒充成功。源时钟停止时没有伪造ACK或硬件自动超时；调用者的有界超时只表示未完成，busy保持，不能继续负载或重试旧命令。

FREEZE后的`source_snapshot`保持总线在ACK穿过两级同步器后由`csr_snapshot`锁存，保持至后续显式ARM。集成必须约束并实证这个3328位总线的最大延迟，不能用跨域false-path掩盖；同步复位及握手仍须单独审查。CSR读数据在RVALID背压期间保持。

## 104字布局

全局word0固定ABI镜像0x41495201；word1是ARM后累计有效源周期模32；word2低5位为最后观察的source_flags，其余0；word3为复位观察累计周期模32；word4—7为0。第c通道从word `8+16*c`开始：

| 通道内字 | 含义 |
|---|---|
| 0 / 1 / 2 | AR握手次数 / R握手次数 / 其中RLAST握手次数 |
| 3 | R握手且RRESP非OKAY次数，包括所有非0编码 |
| 4 / 5 | ARVALID&&!ARREADY周期 / RVALID&&!RREADY周期 |
| 6 / 7 | ARVALID周期 / RVALID周期 |
| 8 / 9 | 最后AR握手ADDR / 完整28位AR元数据channels59:32，高4位0 |
| 10 | 最后R握手9位元数据channels72:64，高23位0 |
| 11 | 当前引脚：低4位ARVALID/ARREADY/RVALID/RREADY，9:4 ARID、13:10 LEN、16:14 SIZE、18:17 BURST、24:19 RID、26:25 RESP、27 LAST、31:28零 |
| 12 / 13 | 首次非OKAY R握手：bit31有效、低9位R原始元数据，其余0 / 首次错误源周期标签 |
| 14 | 最后AR或R握手的源周期标签，同沿二者同时发生只记录一次时间 |
| 15 | 每次AR握手累加LEN+1，模32 |

word11中的“当前”只指最近一次有效观察沿的引脚，不代表已接受或尚待处理事务。无事件时最后AR/R样本保留，而word11每有效周期更新。计数32位回绕，200MHz周期计数约21.47秒回绕；不同边界、不同burst和在途状态不可直接互相等同，更不能拿ΣLEN+1或ready证明DMA已排空。现有v2的MIG观察器独立保留，不在本模块隐式读取或复位。

## 单元TB

顶层`tb_ai_read_monitor`，依赖原有`mna_gp_ww_itf`接口和本模块，不依赖PS/AI/DDR模型。预期成功标记`AI_READ_MONITOR_PASS`。所有命令、读回和等待有限，最终1ms逻辑时间watchdog；停源时钟的预期负例会打印`AI_READ_MONITOR_EXPECTED_TIMEOUT`，该标记不是命令成功。

TB通过公开CSR写握手和输入引脚建立独立期望模型，不读/force DUT私有状态；检查复位、未ARM拒绝FREEZE、已ARM拒绝再次ARM、ARM ACK及清零、六路同沿AR/R、1/2/8/16拍累计、6位完整ID/各元数据、首次错误不被后错覆盖、全部104字/9位偏移、FREEZE前一源周期切点（事件保持到ACK）、冻结后输入变化与读背压稳定、新ARM清除、停源时钟不伪造ACK、忙拒绝、sticky错误及带未完成命令复位恢复。人工固定计数及首次错误样本另行核对，避免仅靠参考模型复制实现。未测试物理CDC/STA或实板功能。
