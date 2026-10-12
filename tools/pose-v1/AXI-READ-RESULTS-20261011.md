# 匹配 AXI／UDMA 读路径审查与双模式内存对照

2026-10-11。批准范围已完成，所有程序、SSH／SCP 会话已结束。四项内存对照通过，**原模型并发异常未复现，根因仍未解决**。当前入口：[ADR_36](../../ADR/ADR_36.md)、[数据核验](evidence/axi-pair-20261011-r4/data-review.json)、[下一步](AXI-READ-NEXT-20261011.md)。

## 实际路径与证据边界

匹配 AXI 插件 SHA256 `d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178`，XRT `a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96`。只读反汇编／符号／匹配公开头文件确认以下路径，程序未使用其中私有字段或寄存器偏移。

| 边界 | 可确认行为 | 仍不能证明 |
|---|---|---|
| PL 数据读取 | PL-init 从公开名称 `udma` 获取区域并分配 16 MiB 暂存块；PL-read 处理 64 字节边界并调用 dmaRead | 所有设备实例／内部线程都由同一资源锁覆盖 |
| DMA 到暂存 | dmaRead 持 pthread mutex，配置传输并轮询状态；错误掩码 0xA／等待掩码 0x5；随后暂存 MemChunk::read，最后解锁 | 状态位的硬件定义、DDR 写响应完成及全局可见性 |
| 暂存到 Host | UDMA-read 持另一 mutex，设置 sync_offset／sync_size，写 CPU 同步触发属性，然后 memcpy | CPU 缓存同步代替 NPU／DMA 生产者完成 |
| 应用两方法 | Tensor::read→MemChunk::read→源区域 read；copyFrom→MemChunk::copyFrom→跨区域 memcpy。Host 公开头未覆盖跨区域版本，XRT 默认版本分配零初始化中间字节区，再读源、写目标 | 更换应用包装器会绕过底层 PL／UDMA 读路径或必然消除异常 |

审查的初次部分函数窗口不完整，已保留并新增按符号大小的完整窗口；不能用原短窗口作“未见同步”的依据。[只读审计身份](evidence/axi-read-audit-20261011-r1/identity.json)、[完整窗口](evidence/axi-read-audit-20261011-r1/complete/identity.json)、实际板端模块同步反汇编均由 data-review 绑定。

实际板端模块 `u-dma-buf.ko` SHA256 **78cae7106e5273fc297178d5cfe226ea8737feaef34dbec8bce450478f35436c**，版本 3.2.5／内核 5.4.52。CPU 属性回调具有 mutex、范围检查、命令 1 使用当前同步字段、DMA ops 回调／dma_direct_sync_single_for_cpu 路径。UDMA0 为 **128 MiB@0x30100000**，sync_mode=1、direction=0、dma_coherent=0，最终身份相同。只读下载没有加载或修改模块。

上游文档描述 CPU 同步用于缓存维护和 CPU 所有权切换；据此推断，该属性本身不能证明另一生产者已经写完。实际模块反汇编才是本板路径证据，网上 master 源码不冒充厂商 3.2.5 匹配源码。[上游说明](https://github.com/ikwzm/udmabuf/blob/master/Readme.md)／[上游源码](https://github.com/ikwzm/udmabuf/blob/master/u-dma-buf.c)。匹配标签源码未取得，厂商改动及硬件状态定义仍缺证。

## 独立工程与身份

新增独立公开接口 `pose::axi_probe::transfer`、SDK 所有者 Pimpl、有限编排和 Host 检查。两方法均验证 Host CPTR、相同 FP32 dtype／容量／非别名，Read 复用既有 input_read 公开适配。原图案、VPU worker 和异常保存模块复用；不包含其他功能的 cpp，不访问内部 DMA 暂存指针。

主程序 SHA256 **b2f7db68b72db95aa868b5b73454a8566736c1b2fdebc1f31095c20c3273fec7**；Host 程序 **a182324441521f9b657e425b0f926cc9b20fcb009c4c72d2f2ea8fcde386406c**；manifest **de0ace33c2a682c0a2d4875171a773e1f42d7ec969ebeffce15aa41d785bf975**；25 个来源。SDK3.39.0、公开头库与图哈希核验。原 CPU/Gather 源码哈希不变，Host107／12注册／59,600 FP32引用上批验收，本轮没有重跑该工程或创建混合 Session。

源采用实际 192 类型 `[1,180,42]`／`[1,100,42]`、FP32、`**C`、轴2全部有效声明。公共分配器拥有96 MiB前缀（不访问数据）、两个源及32字节 padding；四阶段地址均为 **100667392／100697664**，没有固定地址分配，非原模型109232128／109285376。声明4 GiB池不等于已验证实际全部物理容量。

## 逐阶段核验

| 阶段 | 新结果 | 适用范围 |
|---|---|---|
| Host | 两方法×两类型×四代图案，376,320字节逐位；8项非法方法／空／别名拒绝 | 无 Device::Open |
| copy | 100动态图案对，1,176,000 FP32逐位，首末跨度97.26898ms | SDK已知写入，非NPU生产 |
| read | 同规格100对，1,176,000 FP32逐位，97.25424ms | SDK已知写入，非NPU生产 |
| copy＋VPU | 100对，1,176,000 FP32；226合成图像／228 packets／41,492字节 | 19,800.36292ms固定采样跨度 |
| read＋VPU | 100对，1,176,000 FP32；229合成图像／231 packets／41,683字节 | 19,800.36011ms固定采样跨度 |

合计 **400动态对／4,704,000 FP32** 为 C++ 完整逐位门检；另有四次预载完整正确。NumPy 独立生成全部400对指纹，并核对12份实际保存图案对共 **141,120 FP32**逐位字节。指纹核验不称为保存了全部400对原始字节。初次结果拥有之后才比较；正常每阶段预载1次设备源 read，不添加每对晚读。没有异常，因此两轮晚源诊断未触发，不宣称本轮验证了真实异常捕获。

VPU 两阶段先实际非空 capture 再打开主线程 SDK，worker 无 Icraft；每对之间200ms、单对内部无睡眠。455图像全部编码ID、实际PTS、SPS/PPS、空LAST、拥有packet及解码内容通过；均为合成NoInput，不计新姿态吞吐。两端实际各2缓冲、原cookie，STREAMOFF10/9成功、正常drain-LAST，join后SDK销毁，四阶段全部分配块归还。阶段exit0／stderr空，跨全部阶段及最终内核日志相同，无项目进程或39001／8554服务。

普通512KiB准备余量分别17／83，策略记录的规整写入均0；不以余量或两次启动证明永久首次启动可靠。未清缓存／重启或改CMA／BOOT／内核／SDK／模型；最终MemAvailable **714320 KiB**、CmaFree **37544 KiB**仅现场，不证明泄漏或下一次分配必然成功。

## 难点、修正与结论

本机r1错误头名导致打包未完成；r2缺少新命名空间Bytes别名、SDK write需要可变char*及缩进Werror；r3仍有const签名失败。r4按实际签名和闭包头依赖修正，新目录构建，旧失败完整保留，未因此板测重试。回传Linux权限属性导致沙箱审查无法访问原解包树，另以原归档字节创建不导入权限的readable副本；档案及数据未修改。板端时钟落后导致tar未来时间提示保留，没有调整系统时钟；计量使用steady_clock。

结果支持：已知SDK写入、相同类型／规模／较高PL地址和合成VPU负载下，两应用读法均正确。**它不覆盖NPU实时生产，也不能从“未复现”证明VPU、SDK、cache或DMA无责。** 两应用方法共用底层读路径，当前不能把改read当根因修复。ADR_35首次Host坏片段与全部晚源仍保留；完整103、严格5Hz、长期、HDMI和零拷贝继续待验。管理估算83/100保持。
