# 单次常驻生命周期结果（2026-10-10）

本批首次VPU启动、同一上下文三窗→103、完整数值及合成视频核验通过。旧192／ScatterND坏块未复现，根因未修；一次启动成功不等于永久首启动可靠性。

## 身份与实现

程序SHA256 `c4c5caaf83f82c07e663eedae2b94ae0723884e8f134e88bd8b9b1863c601822`，manifest `45dfbd83e7fcc422b11ef96866c3e6613b25a77b4bde96f303d7763701f0fc8a`，403载荷108来源。旧主fbf330d7…cb8702d、旧model-vpu4bab1a1d…49aab2a及原Engine／数学／桥／编码／模型／RAW／SDK／BOOT保持。Host107／12注册／59600冻结身份复用，非新入口Host107。

SDK-free Sequence仅负责阶段转换；新入口组合冻结Run与公开Engine接口，单VPU实际非空capture后创建主线程Engine。三窗4次→同上下文103次，调用0–106／帧100000–100106连续，阶段切换不join、不重开、不重建Session。错误停止下一窗口，原暂存与两晚源保持；末尾七项独立保存，join后销毁Engine。实际清理与null reset分开记录。

旧诊断计数限824只支持103次；新隔离实现仅行限改为856，旧源码和旧主程序保持。Native／ARM阶段13拒绝、107计数边界16拒绝、原生命周期6及Run9拒绝全部过；第108次被拒绝。对象2048行／4MiB、元数据2048行保持。源码生成GBK误读与旧审查器824行拒绝保留为工具修正历史，均非板测失败／重试。

## 实际内容与生命周期

| 阶段 | 调用编号 | 正确前向 | 完整FP32逐位旧参考 |
|---|---|---:|---:|
| 三窗＋重复308 | 0–3 | 4 | 60,400 |
| 27来源循环103次 | 4–106 | 103 | 1,555,300 |
| 合计 | 0–106 | 107 | 1,615,700 |

CSI原始载荷、10800输入、100分数、100×14×3姿态全部先保存后比较。六计算Host／七ZG组、1173融合与0→745协议通过，SDK profiling关闭。192实际源109232128／109285376保持；1712对象／856shadow稳定、856查询全234、963元数据（与查询合1819），107次582首次638/poll1，未增加等待。Host目标mod64为0／16／32均FP32对齐正确，不是64对齐修复。

驱动身份事件一次、两端各2缓冲，映射6,959,104字节，NV121280×720／原cookie保持。两个stage_started记录同一Engine／VPU对象。Engine初始化29321.69921ms；103阶段首末开始跨度20407.15648ms只作预算诊断，不据此验收5Hz。

VPU518合成NoInput图像、520packet（1参数集＋518图像＋1空LAST）、93,978字节，全部解码ID／像素／实际PTS正确；submitted=returned=518，drain／LAST／两STREAMOFF正常，worker join后Engine销毁。首次ready可以是参数集，实际首图像另有时间，不能混称。没有真实骨架图像、显示子进程、TCP／RTSP或HDMI；重复合成图像不算姿态吞吐。

## 资源与清理

新目录一次运行、没有重试。准备时普通512KiB折算9，按授权规整一次144.80296ms后28；进入编码器31→raw REQBUFS后29→capture REQBUFS后21→首次capture20。与上批9→7→0后固件失败的资源条件不同；这支持普通高阶页可用性的重要性，不能归因常驻策略独自修复第一次启动，也不推定16单位是保证阈值。

全部buddyinfo／pagetypeinfo／meminfo／vmstat、原内核日志、耗时和14＋完成阶段快照保存。契约与本次前后原内核字节相同，旧分配失败仍在历史内核日志中，未隐藏或白名单忽略新错误。未清缓存、重启、改CMA／内核／BOOT／驱动／SDK。

结束MemAvailable745488KiB／CmaFree28892KiB／普通单位30是释放后的现场，非泄漏或永久可靠性证明。七项落盘成功、exit0／stderr空，所有项目程序、端口及代理连接已结束；979文件回传哈希核验完整。

## 范围与后续

单次常驻合成VPU＋真实NPU生产107完整正确，旧异常设备源读触发0，异常机制继续保留。不能将未复现写成缓存／DMA／数学或VPU根因修复；整机持续5Hz／30分钟／HDMI／采集终版／安全连续申请／零拷贝仍待。管理粗估83/100保持。

[完成审查](evidence/resident-sequence-20261010-r1/completion-review.json)、[资源](evidence/resident-sequence-20261010-r1/resource-review.json)、[数值](evidence/resident-sequence-20261010-r1/resident.acceptance.json)、[视频](evidence/resident-sequence-20261010-r1/resident.video.json)、[ADR_28](../../ADR/ADR_28.md)、[恢复点](evidence/resident-sequence-20261010-r1/next-checkpoint.json)。下一[真实拥有画面单因素方案](RESIDENT-SEQUENCE-NEXT-20261010.md)仅准备，未新板测。
