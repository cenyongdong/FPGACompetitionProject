# r4错误后源读回：实施与有限回归结果

已实施异常后两轮SDK源Tensor读回，Host验证和最终三窗全链回归通过；两次成功的四帧场景均未复现旧坏值，因此**未取得模型异常时的设备源读回，不能判断旧异常在源侧还是搬运侧，也不能宣布修复**。

程序a7903f6a98c37585c4b9764a899fa6a9c3183024d49b45a7c1b8e9c7fba21cf6，manifest4f85e8148bdc1b47bacb0848dc7282bc5167b726329cd335568269996705aa8d，403载荷／63来源；旧r1/r2/r3、模型、RAW、SDK、BOOT、数学、正常等待／复制、reset(1)／745、VPU双缓冲及子程序保持。

## 已实施与验证

- 错误后先保存拥有的Host暂存，再保存源区域／指针类型／chunk身份／offset／容量／声明；调用两轮Tensor::read，单轮总字节等于原暂存，两轮总量最多其两倍，上限1MiB／轮。两轮间无文件写入；无ADDR/BOTH直接解引用、显式wait/reset/cache或新forward。原CPU异常继续抛出，读回异常不掩盖它。
- Host107／12注册／59,600FP32、IPC与持久化拒绝通过。真实Host192探针47,040字节的两轮SDK读回共94,080字节，与原暂存逐位一致，原0.5非法索引拒绝保持。这只验证Host源，并非设备源实测。
- 初始控制延误未发送输入，板端在5秒窗口超时退出1，0前向；现场完整保留。先启动等待就绪的客户端后，板端4次／60,400FP32逐位旧参考、本地495帧／2744关节正确，但RTSP过早DESCRIBE返回404，网络未验收。
- 新控制只等待首次URI就绪，不重试输入或模型；相同程序／包／门禁／180秒上限在新目录4次／60,400FP32逐位旧参考、499本地编码／469网络帧／2730关节、四来源／实际PTS／像素、正常子回收与LAST归还均通过。本次首DESCRIBE直接200，404等待分支未在该成功场景触发，不伪造其分支验收。
- 合计8正确前向120,800FP32，错误捕获目录均未创建，模型异常设备源读回0次。最终内核相同、source0、8554/39001释放、workers join后销毁Engine。本轮规整0、未清缓存／重启／改CMA。

## 资料与结论边界

FPAI导出的ARM libicraft_xrt.so哈希a29e4eee…749dc96与板端一致。实际入口确认copyFrom委托MemChunk::copyFrom／区域memcpy，read委托MemChunk::read／区域read；具体区域虚函数、DMA和缓存路径尚未穷尽，不把不同入口当作故障定位证明。Linux cache helper no-op继续不作同步证明。

独立证据：[完成复核](evidence/source-readback-20261009-r4/completion-review.json)、[Host源读回](evidence/source-readback-20261009-r4/Host-source-probe-review.json)、[无网络场景局部核验](evidence/source-readback-20261009-r4/local-result-review.json)、[最终数值与生命周期](evidence/source-readback-20261009-r4/process-three-stream-ready.numeric-review.json)、[真实网络](evidence/source-readback-20261009-r4/network-stream-ready/review.json)、[SDK入口](evidence/source-readback-20261009-r4/sdk-mechanism-review.json)。

下一保留异常捕获进入经讨论的有限覆盖或自然首启动，并继续实际区域实现审计；不得循环尝试制造故障、清缓存／重启或放宽finite/索引。当前没有证据把旧三块异常归因于额外查询、RTSP或VPU单一因素。旧221.61ms尖峰／严格5Hz／103／HDMI／30分钟仍待。服务和连接全部结束，恢复读next-checkpoint。
