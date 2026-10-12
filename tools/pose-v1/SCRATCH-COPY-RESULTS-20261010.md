# 受控 SDK 双源搬运与编码并发结果

批准的 [方案](PRODUCER-COUNT-NEXT-20261009.md)已完成。本批独立搬运全通过，但没有复现模型192坏索引，不能宣布故障修复。全部测试和代理连接结束，规整0，旧模型失败保留。

## 实际执行与证据

| 阶段 | 结果 | 执行性质 |
| --- | --- | --- |
| 原 Host107／12注册／59600 FP32 | 身份绑定保持 | 原ELF、402载荷、主来源和SDK一致，复用上一批结果，未新运行 |
| Native／ARM模式契约 | 各10拒绝、47760字节拥有值、残留块及部分异常保存通过 | 本批实际运行 |
| r3无VPU连续搬运 | 100对全字节正确，69.24394ms跨度 | 不创建模型Session／不前向NPU |
| r3编码并发搬运 | 100对全字节正确，19800.31428ms跨度 | VPU实际capture后打开SDK，对内无新增等待 |
| 合成编码核验 | 200图像序号／实际PTS、36443字节H264正确 | 202 capture＝1参数集＋200图像＋1空LAST，不计模型推理 |

r3 ELF `613f2dc1b28bc3864e61a490e961cbb0d640570e0d8fd2f6df3249eb3f17f946`，manifest `df830da9f8d221424363ec1d09fddde8a34f409e40140fa095695385efd870a2`；403载荷、85来源、15规范化SDK头、189厂商文件。原主ELF `3f0ad06c…419f1e37`不变。

程序每对立即拥有两份字节，再执行全字节memcmp；独立NumPy参考核验全部实际指纹与preload／首末原始数据，r3合2388000 FP32比较。首末字节保存，不以低日志方式存下每一对原始数据。SDK分配两源4096／34368、32字节padding34336，64对齐、范围不重叠、共同设备区域确认。ADDR未直接解引用，零拷贝未实现。

并发第一非空capture是SPS/PPS，早于SDK打开；200张合成NoInput图像全部可解码，实际PTS逐一同原输入，编码上下文跨整个搬运窗口。首张图像capture稍晚于SDK打开，该点不写成首图像已先就绪。原两缓冲、prime2、格式、cookie、拥有packet保持；200提交／200归还、正常LAST、两STREAMOFF、worker join后SDK销毁。三阶段exit0／内核同，无残留pose进程或本项目端口。

## 历史修订与失败保持

r1无VPU100对通过（69.18623ms），但B源地址模64为32；未执行r1编码。r2增加SDK拥有padding，只构建，未板测。r3在板测前补调用者持有原字节，复制抛错时独立保存部分槽位和两轮晚源；此异常机制经Native／ARM测试，硬件运行未触发。

本机准备GBK／UTF8、PowerShell工具错误，以及初版视频把参数集计为图像的审查错误已纠正并记录；没有重新运行任何失败板测，也没有更改数据或阈值。[修正记录](evidence/scratch-copy-20261010-r3/local-corrections.json)。r1／r2构建和证据保留，不并入r3身份。

普通高阶页存在，未规整／清缓存／重启／改CMA／BOOT。最终MemAvailable748928KiB、CmaFree29916KiB、普通512KiB折算单位35；资源快照不作为永久可靠性或泄漏证明。[资源审查](evidence/scratch-copy-20261010-r3/resource-review.json)。

## 对原因的影响

本批说明该受控公开SDK路径在100对无VPU与100对编码并发条件下正确，尚不能区分真实模型中的NPU生产可见性、实际TensorType／分布、源位置／chunk或目标生命周期。固定1D模式和低位scratch源与真实模型不同；没有证明SDK DMA/cache fence、驱动无责、零拷贝可用或稳定5Hz。

匹配AXI／XRT二进制已有锁和UDMA同步属性路径；本地资料仍不足以确认DMA mask0x5／0xA完整硬件意义和厂商UDMA驱动同步契约。保持未知，不使用私有偏移写入、固定延时或改SDK猜修复。

后续读 [ADR_22](../../ADR/ADR_22.md)／[下一方案](SCRATCH-COPY-NEXT-20261010.md)。完整103、长期、HDMI和安全零拷贝继续待，不以本批通过替代模型全候选验收。

恢复：[完成审查](evidence/scratch-copy-20261010-r3/completion-review.json)／[检查点](evidence/scratch-copy-20261010-r3/next-checkpoint.json)。板目录 `/tmp/pose-scratch-copy-20261010-r3`，本机包 `.local/pose-v1-scratch-copy/package-20261010-r3`，构建 `.local/pose-v1-build/mixed-20261010-scratch-copy-r3`。原始回传归档哈希保存在完成审查；本机保留字节与程序，Git提交保留源码和文本证据。
