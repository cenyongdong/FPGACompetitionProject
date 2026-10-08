# VPU连续内存取证与启动最小修正（2026-10-08）

**两缓冲隔离候选完成三次独立进程启动回归，期间未规整或重启。** 此结论限本轮程序、720p NV12/H264规格、MVX/内核和实际队列协商；不是任意碎片状态或长期启动保证。常驻运行结果单独核验，见[ADR_02](../../ADR/ADR_02.md)。

## 取证结果

r7仅新增14阶段内存快照与映射字节统计，六缓冲/prime2/cookie/数学/SDK/BOOT保持。Host107/12注册/59,600 FP32通过；一次combined退出1于DQBUF errno5，无capture/Engine/模型前向，两STREAMOFF清理返回0。完整内核新增记录仍是MVX固件order7/512KiB申请失败，不是原MMU ABORT。

实际模块`amvx.ko` SHA256 `300496e2c011168e29c9f7206dc5cabd82d9c7cb643d3b6a372b9825626074b5`，vermagic5.4.52。分配函数指令在0x96e8/0x96ec构造`0x10dc0`，0x96fc重定位直接调用`__alloc_pages_nodemask`，之后才DMA映射；与堆栈`+0x50`返回位置对应。此处没有直接调用CMA API，不改驱动标志或DMA属性。

实际配置`CONFIG_CMA_SIZE_MBYTES=256`、`CONFIG_COMPACTION=y`；启动日志预留256MiB于0x30000000，cmdline只有mem=1024M等原参数，无cma覆盖。本轮reserved-memory目录审计未取得属性，不据此声称不存在其他预留内存；iomem及原始配置保留。未找到本地匹配MVX驱动源码，模块指令不代替完整源码证明。

| 阶段 | 普通order7及以上块数（未加权） | 观察 |
| --- | ---: | --- |
| r7进入/格式完成 | 14 | Unmovable有11个order7、3个order8块 |
| r7原始REQBUFS后 | 8 | 高阶块减少，CmaFree不变 |
| r7 capture REQBUFS后 | 0 | 仅CMA有高阶块；固件随后失败 |
| r8两缓冲进入 | 15 | 初始普通高阶页总字节约同r7，但分布略不同 |
| r8原始REQBUFS后 | 13 | 保留11个order7、2个order8块 |
| r8 capture REQBUFS后 | 13 | 保留13个普通order7块 |
| r8实际首capture | 12 | 固件正常启动 |

[逐阶段独立复核](evidence/pipeline-20261008-r7/allocation-review.json)、[模块指令](evidence/pipeline-20261008-r7/alloc-instructions.txt)。快照观察会影响少量时序，不把快照当分配成功保证。

## 最小修正与回归

新`vpu_startup_encoder.cpp`与r7编码器逐字节比较，只改变一处申请数量`r.count=6`→`2`。仍由REQBUFS协商，独立门禁要求实际两端都返回2；格式/plane/stride/容量、prime2、opaque cookie、Host复制、帧完成协议与SDK/model/RAW/BOOT保持。

两端总映射字节20,877,312→6,959,104（约19.9→6.64MiB）；这是映射统计，不包含所有固件/驱动开销。少分配缓冲留出普通高阶页；不把扩大CMA作为当前直接修复，不修改全局VM配置。

程序SHA256 `33f865a281df277297c6ff277832cb000407369cfee30e8295df79db2c171273`，包manifest SHA256 `727f06ab569e9443a508dba265a861646215be38395dc319d69445726da6266c`。350载荷/21构建来源/15SDK头匹配，原编译warning保持、无新增warning。

r8首次Host300秒超时124，95例全部符合预期，所有22输出59,600 FP32已一致，但剩余拒绝例未完成，未生成Host验收/进入硬件。按实测进度完整估计约338秒，新外部有界包装Host420秒（程序/包未改、原失败保存）；107例完整通过。combined仍180秒，包装脚本副本纳入每次回传哈希。

预定三次新目录独立启动均exit0/stderr空/dmesg前后同；459份完整哈希回传。共24完整前向、30编码帧（每轮2NoInput＋8真实重复），完整数值逐位原参考、NV12逐位NumPy。三H264逐字节相同，且与此前r6成功码流相同。没有复位、缓存丢弃、内存规整或CMA/BOOT/内核/SDK修改。

[三次启动复核](evidence/pipeline-20261008-r8-host420/startup-review.json) · [第一次门禁](evidence/pipeline-20261008-r8-host420/combined.acceptance.json) · [第二次](evidence/pipeline-20261008-r8-host420/repeat1.acceptance.json) · [第三次](evidence/pipeline-20261008-r8-host420/repeat2.acceptance.json)

## 后续边界

保留原六缓冲源、所有失败包和旧程序。本轮候选为已验证规格的应用资源占用修正；若首次普通高阶页已完全不足，仍可能失败，常驻也不能解决这一前提。错误时停止，不自动重开或规整。

下一常驻入口采用已实测的两缓冲、一个Engine/一个VPU线程及容量2画面队列，验证真实PTS和20秒有界来源映射。常驻/27窗口/在线RTSP、整机5Hz/30分钟和HDMI1080p60结论分别保留，不以三次启动代替后续通过。
