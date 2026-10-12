"""Document observed234 failure and next controlled SDK copy gate."""
import json
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT;e=root/'tools/pose-v1/evidence/producer-count-20261009-r2';report=g.load(e/'completion-review.json')
def new(rel,text):p=root/rel;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
def prefix(rel,text):
    p=root/rel;old=p.read_text(encoding='utf-8');head,tail=old.split('\n',1);p.write_text(head+'\n\n'+text.strip()+'\n'+tail,encoding='utf-8',newline='\n')
new('tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md','''# 192公开生产计数诊断结果

本批已实施并结束。Host／新三窗通过；有界103第4调用192索引拒绝。失败两输入在原wait前／后和copy前／后的8次公开layerCount全部234，且坏段仍复制了前次数据输入的相同偏移。**此时再等到234不会产生等待，不能作为本次异常的有证据修正。** 234不是DMA/cache fence，未据此宣布全部内存写入已可见或根因已解。

## 身份与实施范围

新程序`3f0ad06c666d40921479cdb0a428783a3f01c0b145e85af02e6f430b419f1e37`，manifest`d362ee965059b8e0b0557d81252cb11b5a4d028b540c847323e53522986adc14`，403载荷／77来源／15SDK头／189厂商头库。冻结r1和全部旧失败保持。

SDK-free producer_count模块限制主线程、每inv8点顺序、源身份／边界、计数0–745和单inv不倒退；最多824条。只查询192，两源4386／4390→8629／8631→9186结束234。低于234只记录，不改变原等待、SDK复制或ready状态。原582638、CPU数学、Gather、Matmul NPU、reset(1)、745、SDK和BOOT保持；正常新增设备数据读回0。

新增第七项独立保存任务，原一帧拥有shadow、CPU异常暂存和两轮晚源SDK读取继续保留。三窗36原元数据＋32计数，失败30原元数据＋32计数，均在总2048预算内。

## Host与三窗

Native-Werror和ARM各16拒绝，8查询、824条边界、低于目标允许、查询异常保持／保存通过。原拥有帧模块12拒绝、Host107／12注册／59600FP32、真实Host最终输出比较拒绝47040字节和原CPU两轮源94080字节保持。

三窗＋首帧重复4完整前向／60400FP32逐位旧参考，493编码／463网络、4来源／2702关节、实际PTS／字节／像素／Native与ARM参考通过，exit0。32次公开192计数全部234，包括等待前及复制前；没有小于234、倒退或查询错误。这是有限诊断回归，不作性能验收。

## 本批唯一103异常

前3完整结果／45300FP32正确；第4 S12_01_331／inv3／frame100003在GatherElements192拒绝。收到4／消费4／返回3／覆盖0，客户端5次send不是ACK。本调用未返回完整输出，不伪造分数／姿态；整帧输入、计数和原CPU异常保存完整。

失败Frame有188.slot0和192两输入，47760字节。188和192数据输入逐位同旧同CSI正确中间参考；192索引16800字节有1728个有限非整数值，无NaN／Inf。55个坏段全部匹配**本次紧邻前次192数据输入复制的相同偏移**，同时匹配历史同CSI输入。原post-copy、跨门检Frame及CPU异常暂存相同，坏值在复制返回后已存在。

本帧8次公开计数全部234，绑定同一源地址／偏移／容量，时序与原wait、copy及shadow逐项核验。索引copy前查询结束仅约0.71µs即进入copy时间窗；不存在已观测的“计数小于234时开始本次复制”。前3正确调用也全234；与三窗合64次查询均234。

两轮晚设备源94080字节均逐位正确参考，索引与暂存有1728处差异；没有用晚值替换本帧。后读仍晚于原复制，故不能直接证明原复制瞬间DDR源已一致，或把残留位置直接归为某驱动／缓存bug。

本次索引Host目标mod64=0／mod128=64／mod256=192；前批同类异常mod256=0，因此未经验证的256字节对齐不作为默认修正。原对齐／容量／非重叠门禁不放宽。失败从前批inv11提前到inv3不能证明新查询导致异常；二者样本、资源和时序不同，未做因果对照。

## 搬运审计与资源

匹配AXI插件d55e4887…5fc7178已在板端再次核验。所审计UDMA read对象锁内写offset／size／sync_for_cpu，再memcpy；PLDDR dmaRead锁内包含MemChunk.read，不能从“存在锁和同步动作”直接推断驱动完成／可见性语义。

同一dmaRead函数体还看到SDK内部状态轮询：测试mask0x5为0后进入UDMA读取，另检查mask0xA错误；这些只是该匹配二进制的代码路径。硬件位定义、启动确认和写回完成语义尚未核验，应用没有按私有偏移新增寄存器访问、改SDK或插入延时／cache操作。

失败视频300捕获／270网络／1真实来源／28关节前缀核验，正确inv1／2未捕获、2采样尾未出；不是完整视频或正常LAST。3份ARM参考与Native重建逐位。合7正确硬件前向／105700FP32。

七项保存成功、原异常保留；两abort STREAMOFF0、显示子error_cleanup_reaped／256、network source0、Engine在join后销毁。三阶段内核同，输入／RTSP端口释放，全部代理测试／客户端／SSH／SCP结束，无后台。门前普通512KiB单位24／27、最终48，本批代理规整0；未清缓存、重启或改CMA／BOOT。MemAvailable753672KiB／CmaFree88464KiB仅现场，不证明永久启动或无泄漏。

## 工具修正与证据

传输脚本初版误指r1构建，部分目录及初版脚本保留，新complete目录修正后才传输。失败审查脚本初版用了数字开头的Python关键字，保留初版，仅修正审查字段名并通过py_compile；没有改程序、数据、门禁或重跑板测。

[完成审查](evidence/producer-count-20261009-r2/completion-review.json)、[计数／源／时序核验](evidence/producer-count-20261009-r2/failed.counter.json)、[本帧对照](evidence/producer-count-20261009-r2/failed-frame-golden.json)、[坏段匹配](evidence/producer-count-20261009-r2/bad-block-pattern.json)、[晚源](evidence/producer-count-20261009-r2/source-readback-analysis.json)、[恢复点](evidence/producer-count-20261009-r2/next-checkpoint.json)、[ADR_21](../../ADR/ADR_21.md)。下一见[受控搬运方案](PRODUCER-COUNT-NEXT-20261009.md)。103、严格5Hz、长期、HDMI和零拷贝没有新增通过。
''')
new('tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md','''# 下一方案：受控SDK双源搬运一致性，先隔离NPU

本批192原wait／copy前后计数均234，包括实际失败时；坏索引55段同前次数据复制同偏移。单纯添加wait-to234不能在该观测点产生等待，因此暂不实施这个修正，也不插入固定sleep、索引修复或cache猜改。

当前已停止、无后台。先读[结果](PRODUCER-COUNT-RESULTS-20261009.md)、[ADR_21](../../ADR/ADR_21.md)和新检查点；不重跑本次103或旧失败。

## 受控验证设计，尚未构建／执行

1. 新SDK无关模式／比较／拥有字节模块：数据源A30240字节使用唯一有限小数FP32模式，索引源B16800字节使用唯一可精确表示整数FP32模式。跨64／128／256字节及尾部有区分信息，全部输出要求逐位正确，不取整或丢弃坏段。记录来源、顺序、内存类型、区域对象身份、地址／偏移／容量及单steady_clock。
2. 复用此前已验证的公开Device.defaultMemRegion／Tensor.mallocOn／copyFrom契约，在新独立程序取得两份SDK拥有的PL DDR scratch张量，核验AXIZG330AIPLDDR区域、设备归属、范围不重叠及正确释放。它们不来自模型的绝对地址；不创建完整模型Session、不前向NPU、不改参数／图／BOOT，不直接解引用ADDR/BOTH，不包装私有指针。
3. 先进行有限SDK写入及读回门检，以确定scratch的实际数据。随后按A→B连续copyFrom到新Host CPTR张量；立即保留两个拥有shadow，再比较。最多100对／整体30秒。原失败顺序及两种长度保持，不以已通过的两个16KiB旧门检代替。异常保存原结果和两轮SDK晚源，停止，不恢复或继续失败帧。
4. 若无VPU条件通过，再在独立程序中使用原两缓冲、opaque cookie／NV12／H264和帧协议，先取得实际capture，再执行同一有界scratch序列；Device和编码上下文所有权明确，主线程独占SDK，编码线程不接入SDK。整体≤180秒、计量≤20秒／编码≤1000帧，错误全局停止／drain或abort STREAMOFF／join后释放。此项须完成具体资源与协议审查才执行，不把同进程编码当新的NPU模型门检。
5. 模块／模式／边界Native与ARM先过，Host107及旧取证／七项独立保存合同保持。VPU配置、线程关系及初始化顺序的变化都有新身份，不覆盖r2或旧证据；规整如需要按现有自主策略完整记录。

若scratch也出现同偏移残留，能在没有NPU生产者的条件下复现，从而优先定位SDK DMA中转／同步与驱动可见性。若仅VPU并发复现，则调查实际共享资源和DMA／缓存契约，不能直接断言VPU损坏内存。若均通过，回到模型路径，增加合法区域对象身份和已拥有的源／输出证据，控制变量继续定位；通过scratch不代表模型修复。

同时继续匹配资料核查SDK内部DMA状态mask0x5／0xA的硬件定义、启动确认／完成语义，以及UDMA同步方向、范围、mmap和驱动处理路径。二进制有同步调用不等于语义已证明；找不到匹配定义就明确保留未知，不直接使用私有寄存器偏移、强制映射、改SDK或BOOT。

真正零拷贝仍须独立验证公开映射、两端地址对应、生命周期、DMA／缓存同步和释放；不是本次残留的默认修复。完整100候选门禁、异常源读回、103／长期／HDMI范围保持。该方案仅准备，当前没有新scratch写入、VPU或NPU测试。
''')
prefix('Done.md','''## 2026-10-09：192完成计数已取证，失败时234，转向搬运一致性

### 工程内容总结

隔离producer-count-r2程序3f0ad06c…419f1e37／manifest d362ee96…86adc14，403包77来源。SDK-free192四点观察只增加公开计数查询，不改等待／copy／数学／ready；新增第七项独立保存。Native／ARM各16拒绝，Host107／12注册59600值及原拥有帧／CPU异常源读取通过。新三窗4前向60400值、493编码463网络全内容过。

唯一103前3完整正确45300值，第4 S12_01_331／inv3在192拒绝1728有限非整数索引，停止无重跑。3输入47760字节、30原元数据＋32计数及七项保存完整。失败8查询全部234，合两阶段64查询均234；55坏段全同前次数据复制同偏移，两个晚源94080字节正确。合7正确105700值；300捕获270网络／1来源28关节只前缀，正确inv1/2没捕获、2尾未出，3ARM参考正确。规整0／内核同／两abort STREAMOFF0／子回收／Engine join后销毁／端口及代理会话关闭。

### 对后续开发的参考

本次已观测复制开始前计数234，再等234不会产生等待，不作为有依据的修正；仍非DMA/cache fence证明。下一设计公开SDK拥有scratch的30240／16800双源连续搬运，先无NPU／无VPU，再有限VPU并发，区分生产者和搬运／可见性。二进制DMA状态mask5/A意义待匹配硬件定义，不猜寄存器／cache／延时。新[ADR_21](ADR/ADR_21.md)独立记录取舍；[结果](tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md)、[下一方案](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)、[恢复点](tools/pose-v1/evidence/producer-count-20261009-r2/next-checkpoint.json)。本批103／性能未过，数值根因未修；以下同日条目为历史。
''')
prefix('Agents.md','''- 192公开生产计数本批结束（2026-10-09）：3f0ad06c…419f1e37／d362ee96…86adc14，403包77来源。SDK-free192两输入原wait／copy前后8次公开layerCount观察，0–745／单inv不倒退／824条，低于234只记录；等待／copy／ready／数学／582638／reset(1)／745／Gather／SDK／BOOT保持，正常设备数据读回新增0。第七项独立保存；Native／ARM各16拒绝、Host107／12注册59600及原Frame／异常两轮源读取过。新三窗4正确60400值／493编码463网络全内容过；唯一103前3正确45300值，第4 S12_01_331/inv3/frame100003在192拒绝1728有限非整数索引，停止无重跑，合7正确105700值。失败8查询全234，合64全234，无低于234／倒退／查询错误；此观测点wait-to234不会等待，不按假设加等待或宣称DMA fence。55坏段全同前次192数据复制同偏移，188／192数据正确、两晚设备源94080字节正确；3输入47760／原元数据30＋计数32／七项保存／3ARM参考完整。失败300图像270网络1来源28关节只前缀，正确inv1/2未捕获、2尾缺；两abort STREAMOFF0／子回收256／source0／Engine join后销毁／内核同／端口与代理会话关闭。规整0，普通512KiB单位24→27→48，最终MemAvailable753672KiB/CmaFree88464仅现场。ADR_21及PRODUCER-COUNT-RESULTS/NEXT、producer-count-20261009-r2 completion/next-checkpoint为最新入口。下一公开SDK scratch30240/16800双源连续搬运（无NPU先验／VPU并发后验）方案准备未执行，匹配DMA内部mask5/A／UDMA同步语义继续调查；不直接用私有偏移、映射、cache、延时或CMA/BOOT猜改，不重跑本次103或旧失败。103／稳定5Hz／长期／HDMI／零拷贝待。
''')
p=root/'PROJECT-PROGRESS.md';t=p.read_text(encoding='utf-8').replace('## 当前检查点：2026-10-09 保存接入完成，192连续搬运残留待定位','## 历史检查点：2026-10-09 保存接入完成，192连续搬运残留待定位',1);p.write_text(t,encoding='utf-8',newline='\n')
prefix('PROJECT-PROGRESS.md','''## 当前检查点：2026-10-09 192故障时已234，受控搬运一致性设计

公开192四点观察实现，Host／新三窗全内容通过；103第4调用192失败，合7正确105700值。失败两输入8计数均234，1728坏索引55段同前次复制同偏移，晚源正确；等待到234不会在该点产生等待，根因未解。七项保存及原异常保留，全部代理会话已关闭、规整0。下一无NPU的SDK-owned30240/16800双源连续搬运和有限VPU并发设计，仅方案未执行；不猜cache、寄存器、SDK或BOOT修正。管理粗估83/100保持，不增加为103／5Hz／长期／HDMI／零拷贝通过。[结果](tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md)／[ADR_21](ADR/ADR_21.md)／[下一方案](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)／[检查点](tools/pose-v1/evidence/producer-count-20261009-r2/next-checkpoint.json)。
''')
prefix('DIFFICULTIES.md','''2026-10-09当前：[ADR_21](ADR/ADR_21.md)独立记录192四点计数和残留判别。新103第4次失败时计数234，1728坏索引55段逐位前次数据复制同偏移、晚源正确；不默认加wait-to234，搬运／可见性待证。[结果](tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md)／[受控搬运方案](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)。七项保存完好，103／性能未过。以下“当前／最新”为历史。
''')
prefix('REFERENCES.md','''2026-10-09当前：[192计数诊断结果](tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md)、[受控SDK双源搬运设计](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)、[ADR_21](ADR/ADR_21.md)、[完成审查](tools/pose-v1/evidence/producer-count-20261009-r2/completion-review.json)、[实际失败计数](tools/pose-v1/evidence/producer-count-20261009-r2/failed.counter.json)、[新恢复点](tools/pose-v1/evidence/producer-count-20261009-r2/next-checkpoint.json)。旧异常和SDK匹配审计保持。
''')
prefix('ToDoLists.md','''2026-10-09当前：192计数诊断已完成Host／三窗；103第4次索引拒绝时公开计数已234，不能将等待到234当修正。七项取证完整，测试／连接全结束。下一[受控双源搬运方案](tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)先无NPU验证30240／16800 SDK scratch，再设计有界VPU并发，尚未执行。完整103／稳定性能／长期／HDMI／采集终版待；当前完整输出门禁及旧源读取保持。
''')
prefix('ADR/README.md','''2026-10-09当前：新建[ADR_21](ADR_21.md)记录192生产完成观测与连续搬运残留判别，不挤入旧ADR。失败时8计数全234、55坏段同前次数据复制，wait-to234不作为默认修正。[本批结果](../tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md)／[下一受控搬运设计](../tools/pose-v1/PRODUCER-COUNT-NEXT-20261009.md)。
''')
p=root/'ADR/ADR_21.md';t=p.read_text(encoding='utf-8').replace('状态：用户已批准排查；隔离r2构建和Native契约通过，Host／硬件结果待补充。','状态：隔离r2已完成Host／三窗及一次103诊断；192失败时公开计数234，完整取证保存，数值根因待定位。',1)
t+='''
### 本批实际结果与下一决策依据

Host107／12注册／59600FP32、ARM16契约及原一帧取证／两轮源读取通过。新三窗4前向60400FP32／493编码463网络全内容过，32查询全234。唯一103前3完整正确45300FP32，第4 S12_01_331／inv3在192拒绝1728有限非整数索引；失败8查询在原wait／copy前后全234，复制前查询结束约0.71µs后进入复制时间窗。55坏段全部逐位同前次192数据输入复制同偏移，两个晚源94080字节正确。七项落盘和3个47760字节输入／62条组合元数据完好，原异常保留。

这不支持在当前观测点通过等待到234改善数据，不能把原假设当修复结果；公开计数仍非DMA/cache fence。下一设计SDK-own30240／16800 scratch连续搬运，无NPU先验后有限VPU并发，按已有公开defaultMemRegion／mallocOn／copyFrom契约隔离生产者／搬运责任；未执行新scratch或映射。SDK内部状态mask5/A的硬件完成语义须匹配核验，不按反汇编地址直接读写。

合7正确105700值，失败300图像270网络／1来源28关节只前缀，正确inv1/2未捕获、2尾缺，非正常LAST。两abort STREAMOFF0／子回收256／source0／Engine join后销毁／内核同／端口与代理连接关闭；规整0、CMA／BOOT／SDK未改。原复制／数据根因尚未解决，103／性能／长期未通过。[完整结果](../tools/pose-v1/PRODUCER-COUNT-RESULTS-20261009.md)及[完成审查](../tools/pose-v1/evidence/producer-count-20261009-r2/completion-review.json)。本机失败审查初版字段关键字语法错误仅改审查适配器，初版保留，未改门禁或板测重跑。
''';p.write_text(t,encoding='utf-8',newline='\n')
p=root/'ADR/ADR_20.md';t=p.read_text(encoding='utf-8');t+='\n接续2026-10-09新独立[ADR_21](ADR_21.md)：192失败时原wait／copy前后公开计数234，1728坏索引55段同前次数据复制；不默认增加wait-to234，保存机制继续保持，搬运一致性受控验证另设门检。\n';p.write_text(t,encoding='utf-8',newline='\n')
print('Producer192 results, ADR_21 and current project/checkpoint entries archived.')
