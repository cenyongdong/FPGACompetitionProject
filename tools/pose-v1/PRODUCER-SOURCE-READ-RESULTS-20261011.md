# 单调用输出租约：归还通过，物理晚源读未触发

2026-10-11。本批已结束；有VPU计划inv49在准备后绝对截止处退出1，未重试、未增加负载以强行触发数值失配。

## 实际门检

| 项目 | 结果 | 边界 |
|---|---|---|
| Native／ARM租约合同 | 范围、溢出、重叠、代次、线程、失效、拥有值、正常零读、原错误保持通过 | SDK无关模拟合同 |
| ARM Host CPTR公开read | 八输出188160字节逐位参考 | XIR图规格、无物理Device／Session |
| 高地址四调用 | 4／47040 FP32逐位／有限 | 租约4开4关、源读0 |
| 无VPU100 | 100／1176000 FP32逐位／有限 | 租约100开100关、源读0、绝对时隙过 |
| 有VPU100计划 | 前49／576240 FP32正确 | 第50个时隙准备超截止，未reset／forward／开租约；非100通过 |

合153实际前向、1799280 FP32完整正确；0→11／保存后比较保持。原DATA800失配未复现，物理晚源四read／94080字节未触发，不能称源读责任已验证或修复。管理83/100保持，完整103／严格整机5Hz／长期／HDMI待。

## 身份与实现

程序 `9772a0e12bfe04807ccff33caa9136e0689f733caa024afa9d9da0ee30853b28`。原152冻结软件、producer_high基线、CPU／数学／等待／复制／原数据保存位置、模型RAWSDKBOOT不改。新增SDK无关Guard与异常保留助手、独立公开输出租约和薄适配；正常源Tensor强引用只延长到compare结束，主线程／代次／Session有效性检查，下一reset前拒绝活租约。显式关闭后清空Tensor／dtype／Device句柄，Session销毁前Scope失效，prefix释放后manager0。

失败只读模块已经构建：先确认首次两文件完整，再两轮公开Tensor::read至拥有字节，dtype文本、时间、地址／chunk范围、ready／计数与读取哈希保存；原比较错误重抛、诊断失败不覆盖，原文件不修补，无新增wait/sleep/reset/forward/write/cache helper。正常路径未调用该模块，真实物理读取尚未验收。句柄保留和元数据检查会影响时序，不能以未复现判修复。

实际源位置109113344／109092864，104MiB SDK自动前缀无数据访问，四边界非OCM／别名／owner正确，每阶段部署和真实两图案往返核对后才放行。不是原正式精确布局。当前ARM三头／分配链库哈希核验，SDK版本3.39.0、profiling-off和原reset(1)保持。

## 准备时隙失败

inv49 planned=200805093543847ns，actual=200805093627180ns。`filesystem::create_directory`墙钟**915.85662ms**，线程CPU0.29944ms、自愿切换2、缺页0。其后Host校验／分配／写入及journal约0.92314ms，截止检查发现已超过planned+198019801ns，在reset前抛出原错误：

`Prepared call missed absolute slot; no forward`

保存了本次正确B输入及身份和before_reset journal，没有output-4386／4390、trace或late-source，也没有下一call50。上一call48租约已关闭，49打开／49关闭，forced_expired0／failure_capture0／source_read_calls0。4842个阶段事件、49显式forward，异常只在deadline和sdk_call。绝对时隙门禁确实阻止了迟到前向，不移时钟／追帧／放宽时隙。

目录API内等待被定位，内部可含文件系统、存储或调度；不能断言某个驱动或存储根因，也不能回填为上批DATA800陈旧字节原因。阶段allocstall／reclaim／OOM／compact／pgmajfault增量全0，不证明长期无内存问题。

## 视频、资源与收尾

225raw提交／224归还，222ownedpacket共41056字节含参数头，主机221 NoInput图像ID0–220连续；尾221–224未解码，不记全输入编码完成。1340 Q/DQ单编码线程、type10/9各2缓冲／cookie／Host复制保持，98 SDK copy跨度全部与提交capture交叠（非硬件忙或fence证明）。两abort STREAMOFF成功、worker join后Scope／Session毁、prefix1→0／SDK块0，正常drain-LAST未过。冻结summary的0提交／归还是abort未返回结果，不当实际0工作。

资源只读普通512KiB单位196→196（off结束197为更早快照），本批规整0，无清缓存／重启／CMABOOTSDK模型变化。阶段及最终内核逐位同，FPGA operating，进程／管理器／端口39001和8554及所有代理连接结束。最终MemAvailable733520KiB／CmaFree27876KiB仅快照，不作泄漏或永久启动可靠性结论。

r1 Host检查器缺Network完整头编译失败；同一工具调用误继续依赖审计产生缺build-result衍生异常，两日志保留。r2补显式network.h，新目录重新构建，构建完成后单独审计，再ARM Host门检，没有r1板测或失败Session重跑。

[四调用](evidence/producer-source-read-20261011-r2/four.phase-review.json)、[无VPU](evidence/producer-source-read-20261011-r2/off.phase-review.json)、[准备截止失败](evidence/producer-source-read-20261011-r2/on.failure-review.json)、[视频前缀](evidence/producer-source-read-20261011-r2/on.video-review.json)、[完成绑定](evidence/producer-source-read-20261011-r2/completion-review.json)、[恢复](evidence/producer-source-read-20261011-r2/next-checkpoint.json)、[ADR_43](../../ADR/ADR_43.md)、[下一](PRODUCER-SOURCE-READ-NEXT-20261011.md)。
