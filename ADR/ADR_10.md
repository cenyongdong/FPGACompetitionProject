# ADR_10：慢客户端发送错误与有界TCP候选

- 日期：2026-10-08；状态：独立候选正负验证通过，正式r2尚未接入。
- 后续：新guarded目标Host107及真实32回归通过，977编码/767网络、实际128KiB缓冲、全来源/PTS/像素正确。旧r2仍未含策略；TCP三窗通过，27另有失配待取证，不扩大为完整慢客户端清理通过。[当前结果](../tools/pose-v1/TCP-INTEGRATION-RESULTS-20261008.md)。
- 背景：r2正常网络完整来源通过，AU容量8限制了应用队列，但不能单凭highwater1/2证明实际发送侧正常处理慢客户端。

## 实际接口/二进制证据

本机匹配厂商libliveMedia.a的RTPInterface.o在sendDataOverTCP中调用send，部分发送/EAGAIN路径调用makeSocketBlocking(500)、重发并恢复nonblocking，失败返回false/移除stream socket。当前原适配器没有注册发送错误回调，因此无法据正常结果宣布发送失败可传播。

匹配MultiFramedRTPSink.hh公开setOnSendErrorFunc。新增独立guarded_rtsp候选：仅在网络模块注册错误回调，发送失败记录rtp_send_error并停止整条参考链；在SETUP后设置每TCP连接SO_SNDBUF=65536并回读上限，实际Linux返回131072。无系统sysctl、内核、CMA或编码参数更改。旧online_rtsp/r2冻结；不任意丢P帧或从未知IDR恢复。

## 已执行负面测试

SDK无关程序以10fps重复一份已记录的真实21KiB IDR，实际SPS/PPS/NAL保持，不重新打开VPU/NPU。客户端PLAY后停止读取、SO_RCVBUF4096，3秒发送原始保活但不读回复；6秒左右第二次写入报告对端已关闭。

服务产生85个AU，highwater5，实际消费80个后收到RTP发送错误；错误后无继续AU/NAL事件，停止释放两source/端口，exit1是预期拒绝，stderr明确EXPECTED STOP，内核/BOOT/SDK不变。不是AU溢出触发，也不是客户端先主动关闭。完整证据`tools/pose-v1/evidence/rtsp-pressure-20261008-r1/completion-review.json`。

## 验收限制与后续

正常对照已通过：原16秒控制91帧未满100门禁，保留；新30秒控制300真实seed IDR、同guarded源码、223接收帧全部字节/生产实际PTS/解码像素一致，无发送错误、水位1、exit0/内核同/释放正常。程序ee7a10a0…c99c8481，完整证据`tools/pose-v1/evidence/guarded-normal-20261008-r1/completion-review.json`。独立控制内容固定NoInput，不作新模型/吞吐证明。

该结果证明隔离候选的有界TCP和公开发送错误传播；不把候选行为回填为已冻结r2的能力。下一以独立新集成目标执行身份/Host/真实来源回归后固化。当前不能宣布混合推理在慢客户端下的全部清理路径、长期服务或任意网络断连已通过。实际首版服务仍为有限本地CSI输入，TCP窗口前端整合另有门检。
