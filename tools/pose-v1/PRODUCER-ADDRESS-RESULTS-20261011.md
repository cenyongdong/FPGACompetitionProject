# 独立高地址生产者：有限前帧数据复用失配

2026-10-11。PRODUCER-PHASE-NEXT批准范围已结束；有VPU第50次保存输出后数值失败，停止且未重试。原正式坏索引责任仍未解决，但本轮在单独19成员组中得到更小的数据失配场景。

## 实际结果

| 阶段 | 完整正确结果 | 返回／边界 |
|---|---|---|
| Native／ARM合同 | 区间／容量／所有权12拒绝，载荷9拒绝、Trace／时隙／ioctl过 | 无新Host107／Device初始化 |
| 高地址四调用 | 47040 FP32逐位参考／有限 | exit0，4次0→11 |
| 无VPU100 | 1176000 FP32逐位参考／有限 | exit0，100次绝对时隙过 |
| 有VPU100计划 | 前49次576240 FP32正确 | inv49保存两个输出后失配exit1，50次forward，非100通过 |

合153完整正确调用、1799280 FP32；另1失败调用保存11760 FP32，均完整文件。call50不存在。失败是有限数据逐位不一致，不是超时、候选排序或整数门禁放宽。未完整Engine／新CPU数学／网络／HDMI或长期测试，管理83/100保持。

## 身份、地址与前置门检

r2 ELF `745a6aaee544ccfec72aae4a0366091f4a40af4bcb15704818fb7eac0b0e9e3f`。当前ARM device／tensor／ZG三头匹配已有规范哈希，XRT／AXI库匹配分配器审计汇编；公开DefaultMemManager声明起点4096／容量4294963200，声明不是全4GiB物理验收。借助SDK自动管理104MiB前缀，不申请同大小Linux连续页，不指定地址、不读写复制前缀；CMA保持。

实际prefix `[4096,109056000)`，auto_free=true、alignment4096；部署所有9chunk非重叠，其他块在105MiB以下，四边界均有可核对owner：

| Value | 字节 | 实际物理地址 | 别名 |
|---|---:|---:|---|
| 486 | 400 | 109088768 | 实际输入 |
| 478 | 17280 | 109068288 | 实际输入 |
| 4386 | 30240 | 109113344 | 8467 |
| 4390 | 16800 | 109092864 | 8479 |

保持原19成员、RAW权重及9185／0→11、非OCM／dtype／布局。每次Session部署／两图案真实SDK往返都回传核对后才放行。与正式两输出109232128／109285376相对顺序不同，仅地址带控制；不能称精确重建旧布局。

r1编译后审查加强异常释放顺序，r2将前缀句柄销毁移到释放核验catch之外、Device销毁之前；r1未上传或运行，源码与构建保留。r2实际三个Session都是销毁后仅剩前缀1块、自动释放后0，最终SDK块0。

## inv49保存错误的字节证据

当前B输入486／478与固定参考逐位同；4386输出7560个FP32中**800个变化**，无NaN／Inf，全部逐位同紧前inv48／A图案同位置。A／B正确参考的7560值全部不同。4390的4200个索引FP32全部正确，无变化；不能称本次复现了旧192索引错误的完全相同机制。

800值分为31段：12×64字节、19×128字节，起点都64对齐，元素跨度5584至7535，字节范围22336至30144内有间隙，首／末物理范围0x6814740至0x68165c0。完整区间与输出／前帧／参考SHA见[失败核验](evidence/producer-address-20261011-r2/on.failure-review.json)。对齐或前帧吻合是观察，不能直接认定CPU cache或某个DMA层根因。

实际forward计数0→11，两个source_ready=true、地址／offset／capacity／chunk身份稳定。失败forward431.12μs、4386 copy156.82μs／4390 copy88.21μs；没有1.764秒尖峰或时隙异常。4896个阶段事件只在compare结束标记exceptional，所有阶段容量／owner正常。allocstall／pgscan／pgsteal／OOM／compact增量0，pgmajfault6是阶段总量，不定位原因。

本批只保存首次输出；源Tensor局部句柄在SDK函数返回后结束，没有失败后两轮晚源read，不重开设备追读。**能确认首次拥有值已错，不能区分NPU输入写入／生产、输出读取／DMA／缓存和Host暂存责任。** 原完整模型异常读取仍冻结保留，此隔离目标没有冒称晚源机制已执行。

## 视频、资源与收尾

实际VPU先capture后Session，原type10 NV12／type9 H264两端2缓冲、cookie／Host复制保持。1282公开ioctl单线程／fd6，100个SDK copy跨度全部与提交capture区间交叠，包含失败帧；不是纯硬件忙或fence证明。216raw提交／215归还、215ownedpacket／40561字节，包括参数头，214 NoInput图像ID0–213解码连续正确；尾214／215未解码，不计姿态吞吐或正常drain通过。

错误后两abort STREAMOFF成功、worker join后SDK销毁，prefix1→0／所有块0，正常drain-LAST未过。冻结VPU summary submitted／returned=0是abort异常未返回EncodeResult的占位字段，实际提交与归还用原日志，不改原summary。

VPU前资源只读普通512KiB单位254→254，规整0；无清缓存／重启／CMA／BOOT／SDK／模型变化。阶段和最终dmesg逐位同、BOOT9／库／模型身份同、FPGA operating，全部本批程序／管理器／测试端口及代理SSH／SCP结束。最终MemAvailable694740／CmaFree2024KiB仅快照，不证明泄漏或永久启动可靠性。原152软件／CPU分工／745／异常Host和晚源读取机制不改。

严格通用审查在失配处拒绝预期输出是正确行为；专用失败审查核对了全部49正确前缀及失败两文件。其初版事件数期望多写2条，只修本机审查计数至4896，原程序／包／数据不改，不重跑板测。

[API依据](evidence/producer-address-20261011-r2/api-audit.json)、[实际副本diff](evidence/producer-address-20261011-r2/address-sdk-r2.diff)、[四调用](evidence/producer-address-20261011-r2/four.phase-review.json)、[无VPU](evidence/producer-address-20261011-r2/off.phase-review.json)、[失败](evidence/producer-address-20261011-r2/on.failure-review.json)、[视频前缀](evidence/producer-address-20261011-r2/on.video-review.json)、[完成绑定](evidence/producer-address-20261011-r2/completion-review.json)、[恢复](evidence/producer-address-20261011-r2/next-checkpoint.json)、[ADR_42](../../ADR/ADR_42.md)、[下一](PRODUCER-ADDRESS-NEXT-20261011.md)。
