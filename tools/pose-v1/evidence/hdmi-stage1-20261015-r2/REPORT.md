# HDMI 第一阶段：板端只读核验与独立显示前置条件

日期：2026-10-15（Asia/Shanghai）。用户已批准先创建根目录讨论记录，再按“配套／时钟核验 → 静态色条 → 翻帧与安全停止 → 骨架”的有条件顺序实施。

## 实际结果

根目录 [讨论记录](../../../../ARCHITECTURE-DISCUSSION-20261015.md) 已先创建。本次随后完成了一次板端只读盘点：SSH 退出码 0，控制器实耗 3.124318 秒，当前 BOOT 与原记录一致、三份 SDK 核心库一致，FPGA 为 operating。**独立显示所需的像素时钟／PLL 和安全停止契约仍未核实，未进入色条测试。** 没有把 Linux 时钟树或源码分析当作 HDMI 实测。

## 执行位置、条件、范围与失败记录

- 主机：Windows；工作目录 `D:/FPGACompetitionProject`；使用已有 `C:/Users/cenyongdong/miniconda3/python.exe` 和 Git OpenSSH 9.7p1，没有安装或升级。
- 板端：`root@192.168.126.49`；使用默认登录目录，远端通过 `python3 -c` 执行保存的 remote_probe.py 内容，未上传包或创建远程文件。
- 前置条件：已存在的 ED25519 主机密钥必须与固定值一致；认证由专用 askpass 子进程从用户已提供的凭证读取至内存，密码不出现在命令、环境变量或运行日志。
- 参数：一次连接最长 60 秒，主机外层上限 70 秒；读取 BOOT 分区时仅以 `rb` 打开 `/dev/mmcblk0p1`，沿用已有 FAT16 只读解析器，不挂载或写分区。
- 操作：读取 SDK 文件 SHA、包版本、设备树、DRM/fb、UDMA 属性、Linux 时钟摘要、进程名称、内核日志与挂载信息。未打开 NPU/VPU/UDMA/mem 设备，未调用 SDK、MMIO、ioctl、I²C 探测或硬件初始化。
- 停止条件：连接／命令超时、非零退出、非法 FAT 链、BOOT 或 SDK 身份变化均停止，证据不覆盖。不运行推理或编码，不恢复暂停的 DATA 任务。
- 实际 r1 失败：Git SSH 在本机受限环境下无法建立 signal pipe（Win32 error 5），退出 3221225794；尚未连接板端，完整 stderr/调用输出保留于相邻 r1 目录。随后仅以 `ssh -V` 核对限制外启动成功，再建立全新的 r2 目录，解除本机隔离限制后执行一次只读盘点。这不是失败硬件负载重跑，没有重用失败 Session。
- 产物：`remote_probe.py`、`probe.stdout.json` 完整原始返回、transport stdout/stderr、`execution.json`、`review.json`、源码身份与文档前后快照。连接同步返回且控制器退出，没有远程后台任务、显示 DMA 或本批设备句柄需要遗留回收。

## 1. 当前身份与可见接口

| 核验项 | 本次实际结果 | 可得出的结论 |
| --- | --- | --- |
| BOOT.BIN | 7,023,552 字节，SHA `ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef` | 与用户指定 BOOT、历史记录相同；读的是启动介质文件，不能独立证明运行配置的内部网络 |
| SDK | icraft/customop arm64 3.39.0；hostbackend、zg330backend、xrt 三库 SHA 与原预检相同 | 当前运行库文件身份保持 |
| FPGA manager | operating | 处于已配置状态；不能证明 HDMI 正确 |
| DRM / framebuffer | DRM 记录 0，`/proc/fb` 空，未见 `/dev/fb*` 或 `/dev/dri/*` | 未发现可直接调用的 Linux 显示接口 |
| I²C adapter | `/sys/class/i2c-adapter` 无条目 | 未发现现成 I²C 适配器；不代表物理 DDC 线路不存在 |
| UDMA | udmabuf0 134,217,728 字节，phys 0x30100000，sync_mode 1，dma_coherent 0 | 只读取属性，未分配／提交扫描帧；不以这些属性推断完成或缓存协议 |
| Linux clk_summary | 可读取；列 PS／CPU／DDR／VPU 等时钟，无 HDMI/cmos PLL/cam_clk 的已识别节点 | 无法从该接口确认 HDMI PCLKX1、PCLKX5 或 PLL lock；PS ddrx1=400 MHz 不等于 PL 外部 DDR 用户时钟 |

启动分区、SDK 库、设备树和日志完整字段保留于 `probe.stdout.json`；不能把历史显示器名称字段当成本次重新探测到显示器。该字段沿用历史盘点脚本的用户现场信息，本次未取得 EDID、HPD 或屏幕 OSD。

## 2. 补充源码核对：为什么不能直接等待一帧后释放

参考源码 `frame_to_ps_largebuf.v` 的 display_en 门控 color_bar 的 HS/VS/DE，再送入 `video_rect_read_data`。后者在 VS 下降沿发起读帧，在 DE 对应区域消费 FIFO。`frame_fifo_read.v` 的读状态机在 FIFO 空间不足时可停留 S_CHECK_FIFO。

据此可作出的源码级推断：关闭 display_en 会停止有效像素消费，若发生在读帧中间，FIFO 可能填满，剩余帧读取不一定能够走到 S_END。关闭时的 VS 下降沿还可能触发一次读请求。**因此，既不能证明“关闭显示后等待一帧即完成”，也不能用无限等待读完成作为退出方案。** 这不是板端故障复现，仍受“参考 RTL 尚未与当前 BOOT 建立构建身份对应”的限制。

该层的 read_finish 未接出；PLL locked 只直接控制 TMDS 发送器复位，所审查连接未提供软件可读取的 PLL 状态。参考输入侧完成、帧号或写入 ACK 均不能替代显示 DDR 在途读取结束。现有代码不支持据此生成已验证的软件安全停止实现。

参考 XCI 的用户参数为输入 148.5 MHz，MMCM×5、输出分频 5 和 1，意图产生 148.5/742.5 MHz；其中若干 MODELPARAM 的 ACTUAL_FREQ 文本又与请求值不一致，不能仅按单个“实际频率”字段下结论。需要与真实生成网表／实现报告核对。本文没有启动 Vivado 或把其配置等同 Procise 实板测量。

## 3. 下一阶段的明确门槛

| 必须确认的契约 | 现有证据 | 仍缺少的内容 |
| --- | --- | --- |
| 25122301 在无 SDI 时的时钟 | 参考 RTL 存在 SDI 锁定选择与 fallback；HDMI PCLKX1 直接使用 cam_clk | 当前发布位流的配套构建来源／时钟报告，或已映射的频率和 lock 观测接口；不能猜测寄存器 |
| 独立 PS 图像扫描 | 软件 RGB565 地址提交与固定 1080p 读长可交叉解释 | 当前发布版本对该用法的地址、范围、格式、启动条件与必要输入设置说明 |
| 换帧与释放 | 参考读请求会锁存地址，读完成未接出 | 软件可见的帧地址接受／旧帧不再引用契约，或者经过证明的等效机制 |
| 安全停止 | display_en 只门控同步／消费且影响其他路径 | 阻止新请求、处理 FIFO／在途 AXI、观察 idle 的公开流程；不能以软件 ready 或固定延时替代 |

先补齐当前 25122301 发布版本的上述配套信息，才能继续保留 BOOT 的独立 1080p RGB565 测试。若证实没有独立时钟和停止接口，再讨论匹配的 Procise 工程变更；当前没有批准或执行 BOOT 替换、重启、时钟修改或 SDK 改版。

本阶段完成的是讨论归档和只读身份／接口盘点；时钟核验未闭环、色条／翻帧／停止／骨架均待验。正式 demo 和共享模型未改。
