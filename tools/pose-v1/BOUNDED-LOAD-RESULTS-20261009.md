# 103次入口实施、门检及真实设备源异常取证

103低日志入口已实现并完成构建、Host与三窗门检；**实际负载第61次前向拒绝NaN，103门检未通过**。首次取得真实异常后的设备源两轮数据：它们与旧同CSI正确中间参考逐位一致，而原Host输入0暂存有周期性块差异。根因尚未证实，按约定停止，没有重跑或规整。

## 实施与通过项

隔离103预算/新worker、30秒就绪编码期、100秒网络/105秒客户端和180秒硬件边界；原模型/RAW/SDK/BOOT、CPU数学、等待/copyFrom/reset(1)/745、VPU两缓冲及异常Host/源读回保持，内部计时采样/额外查询/profiling均关闭。结果完整保存；ARM结束后稀疏重建参考与主机冻结renderer完整参考明确区分实际采样缓冲，不共用不同帧号的画面。

r1 ARM编译完成后Native命令路径被PowerShell拆分，失败保留；r2仅修正构建表达式。r2父8510f6e120ae5a21a3a6c155da210d67e2ab31f7c94d1fd67bc948820f1f3a19，子6d88d03af190a893445838ef3695d0774ad006d1863f9b063827e0d6e4137d39，manifest437dcf38262ea907d1dc7f10fe2201cf71328b2962dc7e606dd26f4fdbc8495e；403载荷/68来源，SDK3.39.0/15头/厂商189保持。

- Native与ARM各206真实渲染，103映射/104拒绝、首末IPC字节与正常/异常回收通过，29参考预算正确。
- Host107/12注册/59,600FP32与持久化/IPC/AU/协议拒绝通过；Host错误探针两轮94,080字节与暂存逐位一致。
- Native工具先与旧33份正确ARM参考逐位核验。新三窗4次/60,400FP32逐位旧参考，4份Native/ARM参考一致，491编码/461网络/2744关节、全部来源/实际PTS/解码像素与正常LAST/回收通过。

## 103实际失败

单会话发送端成功send62条，随后因板端关闭连接报10053；没有ACK，不能当作收到62条。板端完成inv0–59的60次前向，906,000FP32（预处理输入、分数及姿态）全部逐位旧参考，无此前消费序号缺口；失败inv60/frame100060/S13_07_304在ScatterND582有限性验证前拒绝NaN，未完成第61次。与三窗合64正确前向/966,400FP32，**不能算103或100计量通过**。

### 真实源读取

两个非参数输入均[100,14,3]/16,800字节、PL DDR ADDR，单轮33,600字节，两轮新增67,200字节。参数位于模型输入槽1（真实RAW50,400字节），不与non-param暂存slot1混淆；四项真实RAW参数及融合绑定与旧部署核对一致。

| 内容 | 输入0（基底） | 输入1（更新） |
| --- | --- | --- |
| 原Host暂存NaN/Inf | 4 / 0 | 0 / 0 |
| 原暂存与源读回差异FP32 | 2,096 | 0 |
| 两轮源之间差异 | 0 | 0 |
| 两轮源与旧同CSI正确中间值 | 逐位一致 | 逐位一致 |

输入0 NaN位于8–11，均0xffffffff，12–15为正零；差异区间从[0,64)字节开始，后续主要是每256字节中的128字节段。两轮源全部有限，源码/身份与原异常未改，未直接解引用ADDR。旧N1整目录604项哈希核验后才使用call6/同S13_07_304中间参考。局部旧缓冲模式比较未找到完整对应，不能写为“上一帧覆盖”定因。

**晚读正确不证明原复制瞬间源也正确，更不能证实某次CPU/SDK/缓存操作就是根因。** 它将排查范围收窄到原复制及其时间、内部临时/Host目标存储可见性或后来源更新；不是微小定点误差或候选切换。

## SDK本机审计

当前板端/FPAI libaxizg330aiu.so均d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178。XRT跨区域默认memcpy（0x358e8/0xf4）创建清零临时字节，源区虚调read，再目标write/释放；Host头文件没有另行覆盖该跨区签名。PL DDR read（0x53e20/0x17c）经64字节处理/dmaRead；dmaRead（0x53860/0x5c0）含内部chunk/锁/SDK控制与读回。两条高层路径共享PL DDR读取，但目标和时间不同。PL DDR同区域memcpy（0x286c0/0x5c）到dmaMemcpy，不据此认定当前Host跨区用了该路径。只归因明确函数范围，不把邻接反汇编算入入口；缓存或完成同步错误仍未证。插件是本轮失败后新增单独身份核对，不回填为旧失败已锁定的身份。

## 部分媒体及清理

错误后编码中止，422次sample中已有419个完整码图像/389真实网络帧核对，均覆盖已完成结果的inv0–57，1,624关节正确；inv58/59尚未成为已捕获画面，3个采样尾部未捕获。Native60个实际正确结果参考与29份ARM稀疏参考逐位一致。它们是**失败前缀诊断**，不是完整来源视频/正常drain/103通过。局部审查器首次依赖成功summary失败，以新r2审查器从inference行计数修正，不修改数据或重跑板测。

原异常保留，两端abort STREAMOFF返回0、子回收/network source0，workers join后销毁Engine；内核/BOOT/SDK相同，8554/39001释放，测试/SSH/SCP/客户端结束。失败路径没有正常LAST，不伪报全部队列正常归还。资源三阶段22项哈希核验，最终MemAvailable681088KiB/CmaFree26012KiB；本轮规整0、未清缓存/重启/改CMA。该坏值不是一次连续页申请失败，不能用规整作数据修复或推断泄漏。

下一最小设计：[复制返回时Host shadow/目标元数据与失败接收统计](HOST-STAGING-FAULT-NEXT-20261009.md)。尚未实现或执行新诊断/API替换。103/严格5Hz及HDMI/长期保持待验，管理进度不因增加测试上调。

证据：[完成复核](evidence/bounded-load-20261009-r2/completion-review.json)、[失败60次完整数值](evidence/bounded-load-20261009-r2/failed-load.numeric-review.json)、[设备源与暂存](evidence/bounded-load-20261009-r2/device-source-readback-analysis.json)、[同CSI旧参考](evidence/bounded-load-20261009-r2/same-case-source-golden-comparison.json)、[具体SDK路径](evidence/bounded-load-20261009-r2/sdk-copy-read-mechanism-review.json)、[失败视频前缀](evidence/bounded-load-20261009-r2/video-failed-prefix/review.json)、[失败网络前缀](evidence/bounded-load-20261009-r2/network-failed-prefix-r2/review.json)、[恢复检查点](evidence/bounded-load-20261009-r2/next-checkpoint.json)。ADR_18与ADR_17分别记录预算工程和原数据故障的后续事实。
