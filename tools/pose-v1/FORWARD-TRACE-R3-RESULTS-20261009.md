# 纯计时与异常Host输入取证结果

已实现新隔离计时配置及失败输入保存；Host107／异常捕获通过，硬件三窗在首帧188发现新的周期性数据块异常并停止。没有5Hz取证或性能通过结论。

程序6ce50e142d6635c4554b6280d9727ba00bba3c55414d97fa89c09a66f39ea1fd，manifest529bc28224241e27e2e9f85eb2f221f6d991333467e65d4f7719c40c4187cd07，403项包／61来源。原SDK3.39.0／BOOT／模型／RAW／CPU数学／复制／等待／帧协议／VPU两缓冲及显示子程序保留。旧r1与r2包、源码、构建和失败未覆盖。

- r2构建通过；发现新增Host探针需清除旧局部日志上下文，代理在77例后主动停止exit143，无探针或硬件执行。r3只增加公共configure(nullptr,false)修正该上下文。
- r3 Host107／12注册／59,600FP32／6,912,000字节IPC／9IPC拒绝与回收、9失败持久化拒绝通过。真实Host192异常探针保存两输入共47,040字节，NumPy逐项确认人为0.5为唯一非法索引、原内核异常不变。
- 三窗首帧TopK188在有限性校验拒绝NaN；完整模型结果0次。额外readiness查询、计时采样和SDK profiling均关闭，三个日志均空；因此不能仅归因于前一轮诊断查询。
- 保存720字节180值，96个在三个128字节区间改变为95个正零与1个0xffffffff NaN；84个与同CSI已验收r6桥输入逐位一致。NaN索引11。设备源当时未读回，尚不能确定NPU、SDK复制、缓存或其他写入者责任。
- 120失败回传、真实四RAW参数、注册／融合覆盖／SDK及BOOT身份通过；内核同、两个STREAMOFF成功、子回收、网络source0、端口释放，Engine在所有worker join后销毁。未自动重跑；本批规整0次，普通页充足，不清缓存／重启／改CMA。

[独立失败复核](evidence/forward-trace-20261009-r3/failure-review.json)、[块比较](evidence/forward-trace-20261009-r3/TopK188-block-comparison.json)、[Host探针分类](evidence/forward-trace-20261009-r3/Host-probe-independent.json)、[源差异核验](evidence/forward-trace-20261009-r3/source-delta-review.json)。

[ADR_17](../../ADR/ADR_17.md)记录新数据块难点；ADR_16继续保留原尖峰。下一有限计划：[源Tensor元数据和两次SDK读回](FORWARD-DATA-RECOVERY-NEXT-20261009.md)，用于区分源与Host暂存异常；尚未实施／执行。不以NaN过滤、索引截断、规整或宽松门禁恢复。所有会话／服务已关闭，恢复读next-checkpoint；103负载／HDMI／30分钟继续保留。
