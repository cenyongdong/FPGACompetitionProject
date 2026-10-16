# HDMI修复接入整机与实板验证

2026-10-16用户明确批准将修复HDMI接入整机工程并开始上板验证。执行位置Windows D:/FPGACompetitionProject，隔离工作目录.local/hdmi-integration-20261016-r1，证据tools/pose-v1/evidence/hdmi-integration-20261016-r1。没有复制工具目录；复制此前已核验的参考工程/IP/JFM配套4731文件、2630489459字节，128.522秒。原厂原始工程、先前封存证据、BOOT/模型/SDK保持。

## 接入接口及所有权

- 新增hdmi_ref_100m顶层输入：AC14、BANK12、LVCMOS33，100MHz；保留原MIG 200MHz差分输入。使用现有2018.3＋030ai适配下MMCME2_BASE（BUFG反馈）/BUFIO及BUFR除5，目标pixel148.5MHz、serial742.5MHz，完整布线后核对实际原语/频率/资源及原厂约束。
- 原frame_to_ps_largebuf相机AW/W/B路径和输入格式保留。仅本次实例设置CANDIDATE_SCANOUT=1，关闭旧显示读请求及其消费者，旧AR/R与外部总线断开。新scanout是HP2唯一AR/R owner，一次在途，ARLEN范围0..15，保留原ARCACHE0011、ARPROT000、ARQOS1111；固定ARID0，异常RID转换为读响应错误进入停止/排空。
- 新router在旧桥截低9位前做完整地址片选。新CSR定在原cam窗口高端的0x400b0000–0x400b00ff；原公开SDK相机0x40080000低地址及其余旧别名仍转发旧桥。只改变这256字节原有别名，独立ABI探测后才能访问；不向旧BOOT假设此窗口已存在。此地址选择落实用户本次整机接入授权，不涉及PS BD地址或原软件ABI改写。
- mna_gp_ww为合并的完整32位地址/数据写，无WSTRB；新端点明确采用4'hf，按照awwvalid&&awwready提交。读端点锁存响应并承受背压；router锁定一次读所属端点直到响应被接收，避免用变化中的AR地址选择响应。
- 原TMDS编码及差分输出保留7FAMILY配置。两处ASCII常量改为10'b1111100000；序列器复位改为异步置位、三像素周期同步释放，取消组合反馈。独立时钟启动后默认黑色自由扫描、不启动显示DMA。

## 新CSR

| 偏移 | 含义 |
|---|---|
| 0x00–0x2c | 既有候选寄存器，ABI0x48444d01，命令/地址/ID/原子快照/计数/错误；完整接口见hdmi_register_bank.v |
| 0x30 | bit0锁定、bit1同步后的safe_idle诊断、bit2静态模式、bit3适配器错误；写8清适配器错误 |
| 0x34 | 静态色条0/1；仅safe_idle时修改，首次DMA START后不能重新启用色条；色条模式拒绝START并记适配器错误 |
| 0x38 | 真实像素域计数，注册Gray编码后两级同步至CSR，再解码；须结合主机/CSR时间跨度测量，不把单次值当频率 |
| 0x3c | CSR时钟计数 |
| 0x40 | 整机适配器ABI0x48445301 |
| 0x44 / 0x48 | 目标频率148500000 / 742500000，仅声明配置目标，不是实测 |

释放帧内存仍必须使用新原子快照的safe_idle、stopped ID及响应代数。0x30同步诊断位不替代该证明。帧RGB565从每个64位字低16位起，固定1920×1080/4147200字节；仅公开SDK分配并持有的实际PS DDR块可提交地址，禁止把udmabuf总窗口当作整块所有权。

## 验证、预算和停止

先验证router边界/回压/响应持有，以及真实2018.3 UNISIM MMCM＋SERDES/复位/计数/CSR的256周期波形；每仿真阶段90秒。新代码/整机语法与IP状态后才启动综合；不升级IP、不新增库替换。EDA初始180秒，依据真实日志进展和内存最多1800秒；单run、maxThreads2。超时自主记录并判断；真实逻辑/数据/身份错误停止依赖步骤，修正原因后仅使用新仿真目录/新run保留旧失败。

综合后绑定实际CDC对象：FIFO Gray总线最大延迟与bus skew、多位保持总线约束、同步器首级及复位释放；不使用全域false_path掩盖CDC。布局布线核验新增HDMI时钟、SRAM、TMDS引脚和全部新路径。仅继承用户明确批准的原AI模型两个Min Period定点例外；新时序违例不能自动套用。原厂四项GT配置范围保持，原报告与当前报告分开。

构建后核对raw/Procise产物的源和SHA，证明新配置载荷确实不同于参考，并核对新模块实际存在且连接正确。尚未包含修复的旧参考不计候选。板端每阶段新包、有限预算、完整原值；先ABI/锁定/频率诊断，再静态实屏，后帧地址/翻帧/在途STOP/故障排空，最后按既有共享模型门禁进行整机实时性测量。

已有临时下载授权有效。下载前重新核链、回退身份及运行中PS/PL停止/隔离条件；旧配置没有已验证的排空接口，尚不能以Linux无FD owner替代。若必须改启动分区或再次重启，将先完成可复核候选BOOT、回退及具体切换方案后讨论对应范围；本次不自动扩展这些操作。旧DATA调查保持暂停。

当前执行结果以本批execution.json/result.json为准，接线或计划准备不能称整机/实板验证通过。


## 首版审查后的修正及恢复

首版综合网表仍保留旧PHY。已在CANDIDATE_SCANOUT=1时generate掉其时钟和发送器；原默认参数0路径保留。新时钟调整为MMCM单一742.5MHz输出→BUFIO快时钟及BUFR/5像素时钟，避免混合BUFFIO/BUFG两输出的相位警告，实际模型256周期及1920活动像素复验通过；新版DRC/布线尚待实际核验。区域时钟的布局资源和FMSH IO能力仍须由当前适配流程及硅上结果确认。

首版set_max_delay使用Q端点导致路径截断，工具提示改用合法时钟起点；现已改为C起点，保留Gray最大延迟/bus skew及第二级正常时序，等待新版实际约束报告。未通过更改严重级别或新增DRC关闭来解决。

用户请求暂停后又明确恢复。本次暂停发生在第二版底层综合完成、外层元数据收集期间，原stage没有退出记录；恢复时DCP CRC/17份源SHA及工具Complete/NEEDS_REFRESH=0均已核验，使用新恢复目录读原DCP，不重跑综合。当前新约束、实现、位流和板测仍未完成。[本批实际报告](../../tools/pose-v1/evidence/hdmi-integration-20261016-r1/REPORT.md)。

架构方法另核对AMD原始UG471/UG472的BUFIO/BUFR配对说明，仅作为2018.3前端拓扑依据，不把Xilinx速率数字当FMSH器件保证：[UG471](https://docs.amd.com/api/khub/documents/IbGcnPFe6eF19RHma_Y~IA/content)、[UG472](https://www.amd.com/content/dam/xilinx/support/documents/user_guides/ug472_7Series_Clocking.pdf)。本地原厂适配及实现检查保持优先。


## 有效约束门检与实现启动

2026-10-16：HDMI整机任务已按用户指令恢复。第二版综合检查点的报告恢复完成，266.248秒exit0，未重跑综合；MMCM已由6降至5，旧PHY移除，148.5MHz像素时钟识别正确。r2约束绑定133.068秒exit0，已消除Q起点截断、资源超额及快慢时钟相位警告，但原工程整域false-path覆盖新邮箱上限，故未放行实现。r3因2018.3不支持独立reset_path命令停止，原日志保留；r4按本机手册用同对象set_max_delay -reset_path替换，再恢复所有旧逻辑起点的原cut，157.126秒exit0，真实邮箱路径5ns/10ns和Gray三组约束已核验。r2实际实现发现过程式XDC被读取器跳过，已停止并封存31文件；外层720秒停止后普通回收被拒，主机权限核对并回收该进程树，原结果保持。新impl_hdmi_r3通过追加前置Tcl包装，在原厂hook后加载同一约束；子进程已确认5ns/10ns实际路径和加载成功，现继续实现。其余原厂策略/hook和综合保持，尚无候选位流或实板验收。板端只读复核BOOT/六份SDK保持、FPGA operating、无设备FD owner；仍无公开排空/隔离证明。本轮未下载、修改BOOT、重启或推理，旧DATA继续暂停。

r4仅替换clk_out1_clk_wiz_0与clk_pll_i两向的原整域cut：新时钟对max-delay先用完全相同对象及-reset_path替换；随后全部旧起始时钟引脚（5879/53610）恢复对原目标时钟的false-path，新HDMI起点627/490排除。三组Gray仍是10/10/32位max-delay与skew约束，邮箱真实路径可计时且REQUIREMENT为5/10ns。预优化两个原NDRV不被豁免，需原厂opt后复核。新MMCM剩余REQP-1577指向BUFG反馈与区域输出的差异，两只SERDES时钟已同源并无REQP-1580；必须继续检查实际布线/保持与脉宽，不改严重级别放行。


## FIFO复位物理诊断与修正r4

2026-10-16：HDMI整机接入已恢复。时钟/色条及router仿真、第二版综合、邮箱5ns/10ns有效约束及实际Tcl hook加载已核验。r3实现因布局后优化异常耗时主动停止，未完成布线；79.069秒的优化DCP诊断定位FIFO跨域复位恢复−6.337ns、移除−3.367ns。已修正为每域状态由本域三级同步链释放复位；只对9个真正异步复位链CLR输入约束，不切功能状态复位。新r8像素仿真42.244秒/90秒通过：2073600像素、部分字刷新、欠载排空及像素时钟停转STOP。九份核心功能模块中仅FIFO本次修改，另八份及PS/DDR/AI_Mate/时钟配置保持。第四版顶层综合进行中，后续新约束/物理时序/位流和实板仍待验证。板端只读BOOT/六SDK身份保持；本轮没有下载、BOOT写入、重启或推理，旧DATA继续暂停。

优化DCP最差Recovery来源waiting_reg/C、目的lane/rd_bin等CLR；Removal来源pixel_release_reg[2]/C、目的内存域Gray同步器CLR。这是新HDMI结构问题，不属于原AI两个定点例外。三级wr/rd_release独立always仅接收原组合异步复位，状态分别以wr_release[2]/rd_release[2]作为本域释放后的复位。后续约束只切三组真实异步复位链的CLR，状态复位仍计时，并追溯综合后的唯一来源及源/目标时钟相同。原FIFO容量、AXI/帧协议与时钟目标不变。
