# HDMI现有资源分析：指定BOOT、参考包与无SDI输出路径

日期：2026-10-15，Asia/Shanghai。范围：Windows本机只读文件分析、哈希及BOOT配置载荷核验；未连接板端、未访问寄存器、未构建、未下载或更换BOOT。正式模型/SDK/演示保持，旧DATA调查仍暂停。

## 结论

现有资源已提供明确的“ZG／25122301／单路PLIN+pHDMI”软件参考和与历史板端相同的指定BOOT，不应笼统视为没有HDMI配套。优先研究保留该BOOT的PS生成RGB565→udma→既有PL扫描输出路径，不能据此宣布HDMI可直接运行或必须重做位流。

进一步源码追踪表明：参考工程是SDI摄像头工作流；无SDI场景的像素时钟来源值得优先核实。输入VTC与HDMI输出扫描是两条不同链路，不能把输入VTC寄存器或YAML分辨率当作HDMI模式配置。以下RTL只证明所读参考源码，不证明当前BOOT按同份源码构建。

## 执行与证据

- 位置：`D:/FPGACompetitionProject`；已有`C:/Users/cenyongdong/miniconda3/python.exe`，只用标准库。
- 入口：`audit.py`，一次执行；检查失败、身份变化或目标证据已存在立即停止。源文件只读，产物只写本证据目录。
- 前置条件：用户指定BOOT和配对.bit存在；历史BOOT审计含日志中的PL分区位置；原文件不得覆盖。
- 参数意义：PL分区offset186816、length5980464沿用已保存FSBL日志解析结果，只用于本机读取；不是板端地址。按32位字节序转换后比对.bit完整配置载荷，额外4字节单列。
- 实际输出：`analysis.json`、`sources.json`、执行stdout/退出码、当前文档修订记录；完整旧文档保存在`before/`。
- 通过标准：指定BOOT身份与历史记录一致、配对.bit载荷对应、三份重复SDK辅助头逐字节一致。通过只表示离线身份检查，不是HDMI实屏或当前板端状态通过。

实际一次执行exit0，stderr空；指定BOOT及配对载荷相符，三份重复辅助头同SHA，保存38份来源文件身份。stdout和退出码分别见`audit.stdout.txt`、`audit-exit.json`。

## 1. 资源身份可以确认到哪里

指定`BOOT.bin`为7,023,552字节，SHA256：

`ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef`

与2026-10-04原BOOT审计和2026-10-07板端预检记录相同；2026-10-15已有长测最终记录SDK/BOOT未变。本轮没有新板端读取。

配对`ai7030_top_disable_icap.bit`为5,980,609字节，SHA256为`6818b7f8dea8e0f9dbda1b0d11127255ee1ba8876326bc7708a633641784f72e`。BOOT内PL分区字序转换后的前5,980,460字节与该.bit完整配置载荷相同，尾部另有`20000000`。文件头记录设计名`ai7030_edif_top`、Version2018.3、Patched=DISABLE_ICAP,VCCM、PatchID32494、2026/09/14；这是发布产物元数据，不是当前本机需要改版或已复现构建的证明。

软件包`26040701/README.md`明确标注ZG、AI Mate25122301、Icraft3.36.0、单路PLIN+pHDMI(外置detpost)。当前SDK3.39.0运行混合推理已有独立证据，但HDMI单独兼容性未验。子例README的30TAI对应位流仍写TODO，并有100TAI/25060601旧链接；因此不能把所有例子文字等同完整Lite版本说明。

下载区与项目`Docs/26嵌赛开发/fpai_demo_app`中的`hdmi_display.hpp`、`et_device.hpp`、`sdicamera.hpp`三文件本轮重新哈希相同，原分析并非漏掉一套不同的显示包装器。

包内Image与旧板端记录不同，不能把整套配套文件一并覆盖板端。BOOT的uEnv还含从`mmc 0:2`读取download.bit的旧命令；历史日志已记录FSBL装载成功、后续二次装载未确认，本轮没有修改启动配置。

## 2. 示例中隐藏在摄像头对象内的初始化

`examples/0_datapath/PLin+HDMI/src/sdicamera+hdmi.cpp`先创建`SDICamera`，再创建显示类。摄像头构造会配置PS/PL resize、格式、写入长度及输入VTC选择。默认ZG YAML的`camera.vtc=false`依赖真实SDI输入；相机与显示均填1920×1080/60。

只创建`RGB565HDMIDisplay`不会复现摄像头对象的这些初始化。但CSI骨架系统没有SDI来源，不应为显示而直接运行整个相机例子或调用其复位路径。`SDICamera::reset()`还有无上限等待及“初始化reset影响imagemake/icore”的源码注释，原例的恢复方式不能直接作为当前停止策略。

该无AI例子只读取display宽高，不读取`display.fps`；显示类的宽高只影响`width*height*2`分配。YAML中的60不是实际HDMI60Hz配置或测量。

## 3. 新发现：输入VTC与HDMI扫描并非同一时序发生器

参考连线为：

`frame_ctrl H/V寄存器 → ps_ai_peripheral中的vtc → frame_trans输入选择 → 相机/测试图输入链`

其中`frame_trans.sv:184–186`用`vtc_enable`切换cam与vtc输入。HDMI侧则为：

`color_bar固定时序 → video_rect_read_data → uihdmitx → TMDS`

`video_define.v`启用VIDEO_1920_1080，`frame_to_ps_largebuf.v`固定显示区1920×1080及read_len=518400个64bit传输单位，对应4,147,200字节。因此，仅改0x094–0x0B4输入VTC项不能据此证明HDMI输出模式随之改变；仅把软件缓存改720p还会与这份参考RTL的固定读帧长度不一致。

## 4. 新发现：无SDI时的时钟候选问题

参考`rx_sdi.v:365`：

`assign cam_clk = rx0_locked ? rx_usrclk : sys_clk_200m;`

该fallback端口在顶层接`hp_clk`；`demo_clkrst_wrapper.v`又把hp_clk接ddr_clk。HDMI的color_bar、像素消费与`uihdmitx.PCLKX1`直接使用cam_clk；cmos_clkgen参考配置输入148.5MHz、输出148.5/742.5MHz，但其148.5MHz输出没有作为此处HDMI的PCLKX1。

因此，在无SDI且rx未锁定时，必须核实fallback的实际频率与PLL锁定、像素/串行频率比例。端口名sys_clk_200m本身不是频率测量，不把它当作实板确为200MHz；也不把该参考连线认定为当前BOOT的已证根因。启用输入VTC只改变输入数据/同步选择，不自行修正cam_clk选择。

## 5. RGB565扫描、换帧与停止

显示类使用公开MemChunk写入udma，再提交参考0x40080054的物理地址/8。参考RTL的camera_rd_addr、64bit读地址单位能解释这一约定；这增加接口交叉证据，但未形成当前位流的可操作白名单。

参考frame_fifo_read在读请求应答状态锁存基址，表明存在按请求采样地址的逻辑；但没有据此建立软件可见的flip完成/旧帧释放契约。frame_to_ps的read_finish未接出；四个read_addr输入均接同一camera_rd_addr，不能因底层有四个端口就宣称应用已具备四缓冲。

frame_ctrl的disable_hdmi位位于参考offset0x78，门控输出HS/VS/DE，同时影响输入写入的RGB565/YUV422选择；这不是已经证明的“所有在途DDR读取结束”应答。不能仅停线程、延时一帧或写该位后立刻释放扫描缓存。

## 建议讨论的后续范围

1. 保持所选BOOT，先取得/核对其无SDI独立显示的时钟、PLL锁定及扫描控制依据；优先排除像素时钟异常，不先盲改分辨率。
2. 形成当前版本的显示寄存器语义与安全读取范围；参考输入VTC、HDMI时钟和扫描控制分别列清。
3. 配套明确后，以独立1080p RGB565静态色条验证；随后核对换帧/停止，再接现有骨架渲染及RTSP分支。
4. 若证实该BOOT依赖SDI恢复时钟且无独立修正接口，再讨论可回退的匹配工程/位流变更。当前证据不足以承诺纯软件解决，也不足以要求立即重做硬件。

这些是分析建议，未启动新设备验证。原显示器“不支持时序”、旧失败和历史身份清单保留，未宣布HDMI通过。
