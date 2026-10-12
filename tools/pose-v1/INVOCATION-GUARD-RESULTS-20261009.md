# 单帧拥有值与独立落盘接入：本批结果

隔离接入已经完成，Host及新三窗通过。有界103在第12次调用GatherElements192拒绝496个非整数索引后停止；本批没有103、性能或数值根因修复验收。

## 实际改动与身份

程序`a281cb1acf7783baa6469d0e9e6e41fec7e63ea70945432ded8ac572b50a1e79`，manifest`c8de2aa8dd162dba0bfce7c25055338ae12ac8acff9f74fca3dd95c2df08e2de`，403载荷／74构建来源／15 SDK头／189厂商头库。新entry、Host探针和快照实现保持隔离；冻结stage-guard-r1与旧失败不改。

SDK无关observer从原post-copy shadow传递拥有字节，不再次读取原Host指针。主线程Frame最多保留8输入／1MiB，正常一帧115360字节，下一inv清空。CPU仍使用原暂存Tensor；原等待、SDK复制、582公开计数638、reset(1)、745、数学和Gather／NPU分工不改。正常新增设备源读回为0。

结果、元数据、Engine证据、失败Host帧、warmup及ARM参考分别落盘，保留原异常并记录每任务结果。Engine证据在workers join后由主线程保存；Frame拥有生命周期跨过完整输出比较。异常CPU暂存＋两轮晚源读取保持。

## 门检结果

Native与ARM各12项拒绝、拥有字节释放后保持及比较再抛错后的独立保存通过；默认空observer的旧快照自检各11拒绝保持。Host107／12注册／59600FP32逐位旧参考。真实Host192前向完成后释放SDK输入、结果，模拟最终比较拒绝：47040字节仍正确保存，元数据及后续任务成功，原异常未替换。旧CPU拒绝的47040字节及两轮Host源94080字节保持。

新三窗＋首帧重复4次完整前向／60400FP32逐位一致；492编码／462网络、全4来源、实际PTS及像素通过，退出0、正常LAST及子进程回收。每帧8输入115360字节、32 shadow＋4计数记录，六项独立保存正常。

本批唯一一次103运行：前11次完整结果／166100FP32正确，第12次S21_31_349／inv11／frame100011在192内核拒绝。板端收到12／消费12／返回11／覆盖0；客户端13次send不是板端ACK。失败调用没有返回完整输出，不虚构第12份分数／姿态或完整CSI落盘；原程序已在前向前核对输入载荷。

## 关键字节证据

失败Frame保存188.slot0、192.slot0及192.slot1共3输入47760字节；102条元数据（91 shadow／11个638检查）、六项持久化全部成功。首次582额外检查尚未到达失败inv，因此638不能覆盖192读取。

188输入和192数据输入逐位同旧同CSI参考。192索引输入16800字节中496个FP32不同，全部有限、非整数，没有NaN／Inf；18段范围从3040开始、最后至4160，64／128字节段呈256字节周期。

**18段坏值全部等于紧邻前一次192数据输入复制的相同偏移字节**，既匹配本次拥有的slot0，也匹配历史同CSI slot0。坏索引Host指针模64／128／256均0，FP32对齐、容量和非重叠检查通过；不能以目标256字节未对齐解释本次故障。

本帧保存值、原post-copy快照和CPU异常后的暂存逐位相同。两轮稍后的PL DDR SDK源读回94080字节均逐位旧同CSI正确参考，包括索引；不是用晚读值修复或继续本帧。源读晚于原复制，不能据此证明源在复制开始时正确，也不能据残留模式断言UDMA或缓存根因。当前证据支持同时核查192生产完成与连续搬运的公共暂存／同步路径。

## 视频、资源与限制

失败前缀314编码图像／284网络／9来源／238关节核验正确；正确inv9、10没进捕获尾，3采样未捕获，非完整视频或正常LAST。Native重建11帧及全部11份独立落盘ARM参考逐位一致，本次没有再次丢失参考／元数据。

两个abort STREAMOFF返回0，显示子进程error_cleanup_reaped／status256、network source0、Engine在join后销毁。三阶段内核相同，端口释放，全部代理客户端／SSH／SCP结束，无后台。普通512KiB单位门前57→40、最终15，本批规整0；未清缓存、重启或修改CMA／BOOT／SDK。最终MemAvailable748128KiB／CmaFree2120KiB只是现场，不作为泄漏或永久首启动可靠性证明。

合15正确硬件前向／226500FP32；单帧取证与保存缺口已修补，旧有限姿态失配及整体数据根因仍未解决。有限最终输出异常仅Host模拟验证，本次硬件触发的是CPU索引拒绝，不能声称真实硬件有限输出分支已覆盖。

## 证据与恢复

本机审查脚本初版假定bridge_input存在matches_expected字段，以及猜测子进程回收事件名，分别被真实JSON结构拒绝。只修正审查适配器：改用已核验的同CSI caller_input及完整输出绑定中间参考，并精确要求error_cleanup_reaped／status256、两abort_streamoff返回0；板端程序、数据、阈值没有改动或重跑。模式报告r1保留，r2另增本次实际前一复制字节的同偏移对照。

[完成审查](evidence/invocation-guard-20261009-r1/completion-review.json)、[失败前缀](evidence/invocation-guard-20261009-r1/failed-load.numeric-review.json)、[本帧输入](evidence/invocation-guard-20261009-r1/failed-frame-golden.json)、[块模式](evidence/invocation-guard-20261009-r1/bad-block-pattern-r2.json)、[晚源对照](evidence/invocation-guard-20261009-r1/source-readback-analysis.json)、[独立保存账本](evidence/invocation-guard-20261009-r1/failed-return/run-load-103/results/persistence-ledger.json)、[恢复点](evidence/invocation-guard-20261009-r1/next-checkpoint.json)。下一见[最小定位方案](INVOCATION-GUARD-NEXT-20261009.md)，旧失败不重跑。
