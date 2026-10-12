"""Archive this stopped batch without rewriting historical evidence."""
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def new(rel,text):
    p=root/rel;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
def prefix(rel,text):
    p=root/rel;old=p.read_text(encoding='utf-8');head,tail=old.split('\n',1);p.write_text(head+'\n\n'+text.strip()+'\n'+tail,encoding='utf-8',newline='\n')
new('tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md', '''# 单帧拥有值与独立落盘接入：本批结果

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

[完成审查](evidence/invocation-guard-20261009-r1/completion-review.json)、[失败前缀](evidence/invocation-guard-20261009-r1/failed-load.numeric-review.json)、[本帧输入](evidence/invocation-guard-20261009-r1/failed-frame-golden.json)、[块模式](evidence/invocation-guard-20261009-r1/bad-block-pattern-r2.json)、[晚源对照](evidence/invocation-guard-20261009-r1/source-readback-analysis.json)、[独立保存账本](evidence/invocation-guard-20261009-r1/failed-return/run-load-103/results/persistence-ledger.json)、[恢复点](evidence/invocation-guard-20261009-r1/next-checkpoint.json)。下一见[最小定位方案](INVOCATION-GUARD-NEXT-20261009.md)，旧失败不重跑。
''')
new('tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md','''# 下一最小定位：192生产完成与连续搬运残留

当前单帧拥有值／独立保存接入已通过Host和新三窗；103第12调用192失败，已停止本批，无后台。恢复先读[结果](INVOCATION-GUARD-RESULTS-20261009.md)、[ADR_20](../../ADR/ADR_20.md)及新检查点，不重跑此次run-load-103或旧start2／start3。

## 两个须区分的假设

1. 原Tensor就绪标志跨调用缓存，192生产组尚未完成即读取；当前只有582额外新查638，192应对应9186结束234。静态无当前Host依赖环不代替运行时证据。
2. 连续SDK搬运的UDMA中转／同步／覆盖未反映完整新数据；496个坏索引的18段全部等于前一次数据复制的同偏移。这个模式不能单独区分源更新、中转、CPU可见性或复制目标责任。

目标256字节对齐仍失败，暂不增加对齐要求或以CMA规整当数据修复。不把晚源正确值回填当前结果，不用索引取整、过滤、阈值或最高分骨架降级门禁。

## 拟议独立r2诊断，尚未执行

- 先本机核对匹配SDK的公开layerCount、AXI dmaRead／UDMA read互斥及sync_for_cpu属性调用、长度／错误处理、锁范围。区分跨区copy临时缓冲、设备DMA中转和最终Host目标；不修改SDK或驱动。
- 只对192两个输入，在原wait前／后、原copy前／后记录公开layerCount及同一steady_clock；绑定源producer、地址、偏移、容量及结束234。最多8读计数／调用，103时原927条＋824条≤2048。此类诊断会扰动时序，不作为低日志性能验收。
- 不更改原wait、copy、ready状态、数学、582等待和Gather注册；初始诊断不新增正常设备数据读回。计数按每inv检查0–745和单inv不倒退，不把等待前小于234当错误。
- 保留本轮全部拥有shadow／独立flush、原CPU暂存与两轮晚源读回；Host107／实际Host拒绝及线程／容量契约先过，再新三窗，最后一次有界103。异常保存后停止。
- 若确见192复制开始时计数小于234，再另建最小等待候选，只对该生产组使用公开完成检查，先证明依赖无环，保留所有门禁；通过不等于DMA/cache fence证明。
- 若复制开始已≥234而坏段仍出现，优先继续匹配SDK中转同步／长度／复制契约调查；未经明确公开映射与生命周期证据不实行零拷贝／私有指针或cache猜改。

本文件是接续方案，不是新构建或板测结果；当前批次已经结束。103完整回归、严格5Hz、长期、HDMI和合法零拷贝均未新增通过结论。
''')
prefix('Done.md','''## 2026-10-09：单帧取证和独立保存已接入，192索引残留复发

### 工程内容总结

隔离invocation-guard-r1程序a281cb1a…50a1e79／manifest c8de2aa8…08e2de，403载荷／74来源。原复制后拥有shadow通过SDK-free observer保留至整帧门检，单帧≤1MiB／8输入；六项保存独立执行，原异常及旧CPU两轮源读回保持。Native／ARM各12拒绝、Host107／12注册／59600FP32、真实Host前向后释放输入并模拟最终比较失败的47040字节保持通过。

新三窗4前向60400FP32、492编码462网络全部通过。唯一103运行前11次166100FP32正确，第12次S21_31_349／inv11在192拒绝496个有限非整数索引，立即停止；合15正确226500值。本次3个Host输入47760字节、102元数据、六项保存及11份ARM参考完整；314编码284网络只前缀、9来源238关节，inv9／10未捕获、3采样尾未出。规整0／内核同／两abort STREAMOFF0／子回收／Engine join后销毁／端口和所有代理会话关闭。

### 对后续开发的参考

坏索引18段全部逐位等于紧邻前一次192数据复制的相同偏移；188及192数据输入正确、目标模256为0，两个晚源读回94080字节均正确。原post-copy与异常暂存相同，坏值已在复制返回后存在；早读与UDMA中转／同步责任仍未区分。保存缺口已修补，数值根因未修复，103／性能未通过。[结果](tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md)、[ADR_20](ADR/ADR_20.md)、[接续方案](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)、[恢复点](tools/pose-v1/evidence/invocation-guard-20261009-r1/next-checkpoint.json)。以下同日条目为历史。
''')
prefix('Agents.md','''- 单帧取证接入本批结束（2026-10-09）：a281cb1a…50a1e79／c8de2aa8…08e2de，403包74来源。SDK-free observer从原拥有post-copy shadow保留主线程Frame至整帧门检，≤8输入／1MiB，下一inv清空；原SDK复制／数学／582638／reset(1)／745／Gather保持，正常额外设备数据读回0。六项独立flush、原异常及旧CPU两轮源读回保留。Native／ARM各12拒绝、Host107／12注册59600值及真实Host有限最终拒绝47040字节／原异常／后续保存通过。新三窗4正确60400值、492编码462网络全内容过；唯一103前11正确166100值，第12 S21_31_349/inv11/frame100011在192拒绝496有限非整数索引，停止无重跑，合15正确226500值。3输入47760字节、102元数据／91 shadow／11个638（失败192未到582）、六项保存／11ARM参考均完整。坏索引18段全部同前一次192数据复制同偏移，目标mod256=0；188及192数据输入正确，两晚设备源94080字节同旧CSI正确。原shadow／异常暂存相同；不证明早读或UDMA/cache根因，有限硬件输出异常未覆盖，CPU异常原机制实触发。失败314图像284网络9来源238关节只前缀，正确inv9/10未捕获、3尾缺；两abort STREAMOFF0／子回收256／source0／Engine join后销毁／内核同／端口和所有代理会话关闭。本批规整0、普通512KiB单位57→40→15，最终MemAvailable748128KiB/CmaFree2120仅现场。ADR_20/17及INVOCATION-GUARD-RESULTS/NEXT、invocation-guard-20261009-r1 completion/next-checkpoint为当前入口；下一单独192公开producer234前后计数观察＋匹配SDK中转同步审计方案已准备未实施。不重跑本次103或旧start2/start3，不放宽索引／完整候选，不猜ready、指针、缓存、CMA或BOOT。103、稳定5Hz、长期、HDMI、零拷贝待。
''')
p=root/'PROJECT-PROGRESS.md';text=p.read_text(encoding='utf-8');text=text.replace('## 当前检查点：2026-10-09 独立回归有限输出异常，先补齐取证','## 历史检查点：2026-10-09 独立回归有限输出异常，先补齐取证',1);p.write_text(text,encoding='utf-8',newline='\n')
prefix('PROJECT-PROGRESS.md','''## 当前检查点：2026-10-09 保存接入完成，192连续搬运残留待定位

单帧拥有字节与独立落盘已实现，Host107／真实Host最终拒绝及新三窗全内容通过；本批103第12次192索引拒绝，合15正确前向226500FP32。3输入47760字节和102元数据完整，496个坏索引18段同紧邻前次复制的同偏移，两晚源均正确；数值根因未证。测试／连接全结束，规整0。下一独立192 producer234公开计数观察与匹配SDK中转同步审计已规划，尚未执行。管理粗估83/100保持，不以取证完善增加为103／5Hz／长期／HDMI／零拷贝验收。[结果](tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md)／[下一方案](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)／[检查点](tools/pose-v1/evidence/invocation-guard-20261009-r1/next-checkpoint.json)。
''')
prefix('DIFFICULTIES.md','''2026-10-09当前：[ADR_20](ADR/ADR_20.md)单帧取证／独立落盘已接入，Host／三窗通过；新103第12次192索引496非整数拒绝。18坏段同前次数据复制同偏移，Host256对齐、两个晚源正确；早读与SDK DMA暂存／同步责任未证。六项保存、3输入47760字节、102元数据及ARM参考完整。[结果](tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md)／[下一定位](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)，没有新103／性能通过。以下“最新”为历史。
''')
prefix('REFERENCES.md','''2026-10-09当前恢复：[单帧取证接入结果](tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md)、[192完成与搬运定位方案](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)、[完成审查](tools/pose-v1/evidence/invocation-guard-20261009-r1/completion-review.json)、[当前检查点](tools/pose-v1/evidence/invocation-guard-20261009-r1/next-checkpoint.json)、[坏段字节模式](tools/pose-v1/evidence/invocation-guard-20261009-r1/bad-block-pattern-r2.json)。原有限输出和晚源证据不覆盖；SDK／映射资料继续适用。
''')
prefix('ToDoLists.md','''2026-10-09当前：单帧取证和独立落盘已接入，Host／新三窗完成。103第12次192拒绝，已停止、全会话关闭；不能勾选完整103或性能验收。下一按[最小方案](tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)先区分192生产组234完成与SDK连续搬运残留，保留所有原异常／门禁；不重跑旧失败，不猜缓存或零拷贝。完整稳定性／长期／HDMI／采集终版继续待。以下待办以其历史状态理解。
''')
p=root/'ADR/ADR_20.md';text=p.read_text(encoding='utf-8');text=text.replace('状态：失配已完整保存；独立SDK无关保存模块通过Native／ARM测试，尚未接入冻结推理程序；数值根因未解。','状态：单帧拥有值与独立落盘已隔离接入并通过Host／新三窗；103第12调用192索引失败，完整取证已保存；数值根因未解。',1)
text+='''
## 接入与本轮实际验证结果

2026-10-09按用户审查后的接入契约实施独立invocation-guard-r1。observer复制原拥有shadow，不重读Host指针；Frame由主线程拥有、每inv清空，六项保存分离，原异常和旧CPU暂存／两轮源读回保持。程序a281cb1a…50a1e79、manifest c8de2aa8…08e2de，403包74来源；原SDK／数学／等待／582638／Gather／模型／BOOT不变。

Host107／12注册／59600值、Native／ARM各12拒绝及真实Host前向后释放SDK输入再模拟完整输出比较拒绝通过。新三窗4前向60400值／492编码462网络全内容过。唯一103前11完整正确166100值，第12次S21_31_349／inv11／frame100011在GatherElements192拒绝496个有限非整数索引；停止，不重跑。合15正确226500值，没有103／性能验收。

本轮取得3输入47760字节、102条元数据、六项保存全部成功，以及11份ARM参考。188和192数据输入正确，192索引18段共496值全部逐位等于紧邻前次数据输入复制相同偏移；目标模256为0、容量与非重叠检查通过。原post-copy、持有Frame及CPU异常后的暂存相同，两个晚源设备读回94080字节均正确。坏值在复制返回后已经存在，但晚源不能证明原复制开始时源正确，残留模式不等于UDMA或缓存根因。当前只582新查638，失败192未到该检查；下一应独立观察192生产组234完成前后及连续搬运暂存／同步路径。

这解决了保存寿命／耦合落盘的工程缺口；真实有限硬件输出异常保存仍未触发，本次CPU异常保存实触发。失败314编码284网络9来源238关节仅前缀，正确inv9/10未捕获、3采样尾缺，非正常LAST。内核同／两abort STREAMOFF0／子回收256／source0／Engine join后销毁／端口与会话关闭；规整0，CMA／BOOT／SDK未改。详见[本轮结果](../tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md)、[完成审查](../tools/pose-v1/evidence/invocation-guard-20261009-r1/completion-review.json)及[下一方案](../tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)。旧有限姿态失败及缺失元数据继续保留，不回填或按候选排序解释当前索引错误。
''';p.write_text(text,encoding='utf-8',newline='\n')
prefix('ADR/README.md','''2026-10-09最新：同一决策[ADR_20](ADR_20.md)补充单帧取证／独立落盘实际接入与新103第12调用192失败证据；未另起重复ADR。保存缺口已修补，496坏索引18段同前次复制同偏移、晚源正确，数值根因继续待。[结果](../tools/pose-v1/INVOCATION-GUARD-RESULTS-20261009.md)／[下一方案](../tools/pose-v1/INVOCATION-GUARD-NEXT-20261009.md)。
''')
print('Current result, next plan, ADR_20 and project recovery entries archived; old failures retained.')
if __name__=='__main__': pass
