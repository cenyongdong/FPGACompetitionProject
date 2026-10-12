# 真实模型复制对象与类型取证结果

本批批准路线已完成，新Host与三窗全内容通过；唯一103在第73次192坏索引停止。复制前后对象身份／类型／范围合法且一致，残留仍存在，根因未解决。没有重新运行失败负载，全部代理测试和连接关闭。

## 实际完成

新r3 ELF `fbf330d73ec34c43c7c2757253115e720ba7dccfd6fc6f54a28c6cbaacb8702d`，manifest `c83773ef0e51aed2b85cdc2128a4549b9188a50c239c5fd2ee2a422ca98387e4`，403载荷80来源。原桥／入口删除新metadata适配后逐位还原，原wait／copy／数学／192查询／582638／reset(1)／745／模型／SDK／BOOT保持，正常设备读取新增0。

| 门检 | 本批结果 |
| --- | --- |
| Native／ARM新模块 | 各17拒绝，部分错误身份行保存／线程／范围／预算／不可覆盖保存通过 |
| 新主程序Host | 实际重做107例、12注册、59600 FP32，原47040拥有字节及两轮94080 Host源读回通过 |
| 三窗＋重复 | 4正确前向60400 FP32，489编码459网络／全4来源／实际PTS／像素通过 |
| 一次103诊断 | 前72正确1087200 FP32，第73次192拒绝，未完整103／性能验收 |

四份ARM画面及warmup逐位Native。合76正确1147600 FP32，不包含独立Host用例值。源dtype／分布和对象观察增加CPU字符串分配及时间扰动，不按失败延后或诊断节拍记性能优化。

## 失败事实及排查范围

S51_01_301／inv72／frame100072，GatherElements192索引128值有限非整数、7坏段全同紧邻前次192数据复制的同偏移。188、192数据输入正确；原拥有shadow／CPU异常暂存／跨调用Frame相同。两轮晚设备源94080字节逐位同正确同CSI参考。失败192八查询全部234，两阶段合616查询均234；额外wait-to234仍无已观测等待依据。

新对象合1222行，失败阶段1158行对应579份shadow，651原元数据及584计数完整。8个源chunk使用同一PL DDR区域／同一Device，实际及声明dtype一致：FP32、各shape／layout和merged轴完整有效mask均通过；同copy前后Tensor／Region／chunk／Device／指针／offset／capacity未变化。

失败192两源地址109232128／109285376、offset0、容量30240／16800，源范围不重叠；两个Host目标chunk不同、范围不重叠，合法Host区域。目标模64分别16／32，仍FP32对齐；不能把256字节目标对齐当作故障必要条件。对象数值身份不是物理地址或内部UDMA缓冲身份，未验证应用PL DDR映射或内部DMA/cache fence。

八项独立保存全完成：原完整输出、复制元数据、192计数、新对象、Engine、失败Frame、warmup及ARM参考。3个失败输入47760字节保持；29份稀疏ARM画面＋warmup逐位72份Native重建对应项。

失败434图像／404网络／70结果来源／1946关节是正确前缀；完成inv70／71没被捕获，3采样尾未出，不能记完整视频或正常LAST。接收／消费73、返回72、覆盖0；PC74次发送没有ACK证明，10053为停止后的客户端异常现场。

## 资源、历史失败和结论

两abort STREAMOFF均0、显示子回收256、network source0、Engine在join后销毁、内核同及端口释放。规整0；普通512KiB单位34→33→23，最终MemAvailable749348KiB／CmaFree4228KiB，仅资源现场。不清缓存、重启或修改CMA／BOOT／SDK。

r1／r2严格编译格式失败保留，r3仅改括号与格式，没有放宽-Werror。审查工具PowerShell转义失败以独立Python工具修正；最初在SCP尚未结束时解包遇文件锁，待传输exit0及归档哈希一致后新目录提取，不是板测重跑。

本次未观察到可见对象变化、错误dtype、范围越界或同域两个输入地址重叠；仍不能区分复制时源尚未可见与SDK内部中转／缓存责任。常量1D scratch与动态模型之间差别仍存在。下一 [真实类型／动态模式独立对照](TENSOR-IDENTITY-NEXT-20261010.md)仅准备，未新搬运／模型测试，不以重复制、索引修复或固定sleep掩盖坏值。

[ADR_23](../../ADR/ADR_23.md)／[完整审查](evidence/tensor-identity-20261010-r3/completion-review.json)／[恢复点](evidence/tensor-identity-20261010-r3/next-checkpoint.json)。包 `.local/pose-v1-tensor-identity/package-20261010-r3`，构建 `.local/pose-v1-build/mixed-20261010-tensor-identity-r3`，板目录 `/tmp/pose-tensor-identity-20261010-r3`；旧包和异常全部保持。稳定103／持续5Hz／长期／HDMI／采集终版与零拷贝未通过。
