"""Archive approved one-lifecycle results; preserve historical failed runs."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[2];t=root/'tools/pose-v1';e=t/'evidence/resident-sequence-20261010-r1'
r=json.loads((e/'completion-review.json').read_text());assert r['correct_calls']==107 and r['VPU_contexts']==1
def fresh(p,s):assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
def prepend(p,s):
    old=p.read_text(encoding='utf-8');head,_,tail=old.partition('\n');p.write_text(head+'\n\n'+s.strip()+'\n\n'+tail.lstrip('\n'),encoding='utf-8',newline='\n')
fresh(t/'RESIDENT-SEQUENCE-RESULTS-20261010.md','''# 单次常驻生命周期结果（2026-10-10）

本批首次VPU启动、同一上下文三窗→103、完整数值及合成视频核验通过。旧192／ScatterND坏块未复现，根因未修；一次启动成功不等于永久首启动可靠性。

## 身份与实现

程序SHA256 `c4c5caaf83f82c07e663eedae2b94ae0723884e8f134e88bd8b9b1863c601822`，manifest `45dfbd83e7fcc422b11ef96866c3e6613b25a77b4bde96f303d7763701f0fc8a`，403载荷108来源。旧主fbf330d7…cb8702d、旧model-vpu4bab1a1d…49aab2a及原Engine／数学／桥／编码／模型／RAW／SDK／BOOT保持。Host107／12注册／59600冻结身份复用，非新入口Host107。

SDK-free Sequence仅负责阶段转换；新入口组合冻结Run与公开Engine接口，单VPU实际非空capture后创建主线程Engine。三窗4次→同上下文103次，调用0–106／帧100000–100106连续，阶段切换不join、不重开、不重建Session。错误停止下一窗口，原暂存与两晚源保持；末尾七项独立保存，join后销毁Engine。实际清理与null reset分开记录。

旧诊断计数限824只支持103次；新隔离实现仅行限改为856，旧源码和旧主程序保持。Native／ARM阶段13拒绝、107计数边界16拒绝、原生命周期6及Run9拒绝全部过；第108次被拒绝。对象2048行／4MiB、元数据2048行保持。源码生成GBK误读与旧审查器824行拒绝保留为工具修正历史，均非板测失败／重试。

## 实际内容与生命周期

| 阶段 | 调用编号 | 正确前向 | 完整FP32逐位旧参考 |
|---|---|---:|---:|
| 三窗＋重复308 | 0–3 | 4 | 60,400 |
| 27来源循环103次 | 4–106 | 103 | 1,555,300 |
| 合计 | 0–106 | 107 | 1,615,700 |

CSI原始载荷、10800输入、100分数、100×14×3姿态全部先保存后比较。六计算Host／七ZG组、1173融合与0→745协议通过，SDK profiling关闭。192实际源109232128／109285376保持；1712对象／856shadow稳定、856查询全234、963元数据（与查询合1819），107次582首次638/poll1，未增加等待。Host目标mod64为0／16／32均FP32对齐正确，不是64对齐修复。

驱动身份事件一次、两端各2缓冲，映射6,959,104字节，NV121280×720／原cookie保持。两个stage_started记录同一Engine／VPU对象。Engine初始化29321.69921ms；103阶段首末开始跨度20407.15648ms只作预算诊断，不据此验收5Hz。

VPU518合成NoInput图像、520packet（1参数集＋518图像＋1空LAST）、93,978字节，全部解码ID／像素／实际PTS正确；submitted=returned=518，drain／LAST／两STREAMOFF正常，worker join后Engine销毁。首次ready可以是参数集，实际首图像另有时间，不能混称。没有真实骨架图像、显示子进程、TCP／RTSP或HDMI；重复合成图像不算姿态吞吐。

## 资源与清理

新目录一次运行、没有重试。准备时普通512KiB折算9，按授权规整一次144.80296ms后28；进入编码器31→raw REQBUFS后29→capture REQBUFS后21→首次capture20。与上批9→7→0后固件失败的资源条件不同；这支持普通高阶页可用性的重要性，不能归因常驻策略独自修复第一次启动，也不推定16单位是保证阈值。

全部buddyinfo／pagetypeinfo／meminfo／vmstat、原内核日志、耗时和14＋完成阶段快照保存。契约与本次前后原内核字节相同，旧分配失败仍在历史内核日志中，未隐藏或白名单忽略新错误。未清缓存、重启、改CMA／内核／BOOT／驱动／SDK。

结束MemAvailable745488KiB／CmaFree28892KiB／普通单位30是释放后的现场，非泄漏或永久可靠性证明。七项落盘成功、exit0／stderr空，所有项目程序、端口及代理连接已结束；979文件回传哈希核验完整。

## 范围与后续

单次常驻合成VPU＋真实NPU生产107完整正确，旧异常设备源读触发0，异常机制继续保留。不能将未复现写成缓存／DMA／数学或VPU根因修复；整机持续5Hz／30分钟／HDMI／采集终版／安全连续申请／零拷贝仍待。管理粗估83/100保持。

[完成审查](evidence/resident-sequence-20261010-r1/completion-review.json)、[资源](evidence/resident-sequence-20261010-r1/resource-review.json)、[数值](evidence/resident-sequence-20261010-r1/resident.acceptance.json)、[视频](evidence/resident-sequence-20261010-r1/resident.video.json)、[ADR_28](../../ADR/ADR_28.md)、[恢复点](evidence/resident-sequence-20261010-r1/next-checkpoint.json)。下一[真实拥有画面单因素方案](RESIDENT-SEQUENCE-NEXT-20261010.md)仅准备，未新板测。
''')
fresh(t/'RESIDENT-SEQUENCE-NEXT-20261010.md','''# 下一单因素：常驻上下文中的真实拥有画面

当前批准的单次常驻方案已完成并安全结束。先读[结果](RESIDENT-SEQUENCE-RESULTS-20261010.md)、[ADR_28](../../ADR/ADR_28.md)及[恢复点](evidence/resident-sequence-20261010-r1/next-checkpoint.json)。以下仅准备，不自动执行新硬件阶段。

1. 继续单VPU首次capture→主线程单Engine→三窗完整参考→103，保持正常drain／LAST、两缓冲／cookie／SDK复制／ready/reset(1)／745、原异常Host暂存和两晚源。第一次启动仍独立报告，资源按现场决策，不循环规整／重开／清缓存／重启或改CMA／BOOT。
2. 将合成NoInput内容替换为当前前向实际最高分姿态生成的拥有NV12画面；原冻结骨架渲染／显示层变换保持，不修改模型候选、坐标、阈值或数学。通过明确public producer接口和容量2拥有值队列连接编码，编码worker不接触Engine／SDK／结果私有状态，不包含其他功能.cpp。尚未决定让渲染与NPU交叠；首轮优先主线程生成以减少并发因素，记录增加的时序与资源差别，不宣称严格单一物理条件。
3. 队列所有权、覆盖／最新采样、重复标记、来源序号和实际PTS先做SDK-free契约；保存每次实际模型结果及来源映射，重复旧画面不算新姿态。数据上限与异常传播有界，冻结本批全部源／包／失败。
4. 新身份构建、Native／ARM契约／CPU基线审查后，在一个新上下文内先4帧＋重复，再103。先2Hz来源节奏并明确总预算（预计1.5＋51秒调度、初始化≤60秒、首次≤5秒，外部仍180秒），生成／编码10fps独立；不以慢端补帧伪造实时性。最大发布107、编码1000；每次前向保存完整输出后严格旧参考比较，异常立即保存并停止。
5. 主机核验完整FP32、NV12字节、解码骨架像素／关节、全部来源／采用／重复／覆盖和实际PTS、端口／队列／线程释放。首批不接显示子进程、网络／RTSP或HDMI，取得真实画面107后再引入下一个因素。

旧并发坏块根因未修，本批阴性结果仅缩小条件；新画面引入复制、渲染、堆与时序影响须如实记录。5Hz／长期性能、永久首次启动可靠性和零拷贝不纳入该有限内容门检。
''')
summary='单次常驻r1 c4c5caaf…c601822／manifest45dfbd83…1f0fc8a，403包108来源；Native／ARM阶段13、107计数16、原生命周期6／Run9拒绝过，原Host107／12注册59600身份复用。实际单VPU／单主线程Engine连续三窗4＋103合107前向1615700FP32逐位旧参考、518合成图像／实际PTS／像素通过，520packet／93978字节／正常drain-LAST／两STREAMOFF／join后Engine销毁。192源109232128／109285376保持，1712对象／856shadow、856查询234、963元数据稳定；原模型／SDK／BOOT／数学／ready/reset(1)／745和异常两晚源保持。一次规整144.80296ms／普通9→28，编码进入31→29→21／首次20；不是永久首启动修复或已证阈值。exit0／stderr空／原内核同／七项保存成功，所有项目程序／端口／代理连接结束，最终745488KiB／CmaFree28892／普通30仅现场。旧坏块未复现／根因未修，未显示／网络／HDMI／持续5Hz／长期／零拷贝；83/100保持。'
links='[结果](tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md)／[ADR_28](ADR/ADR_28.md)／[下一](tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md)／[恢复点](tools/pose-v1/evidence/resident-sequence-20261010-r1/next-checkpoint.json)。'
prepend(root/'Done.md','## 2026-10-10：单次常驻上下文三窗→103完成\n\n### 工程内容总结\n\n'+summary+'\n\n### 对后续开发的参考\n\n常驻减少阶段间重新申请机会，本次首次启动资源条件改善后成功，不能单独归因于常驻或规整。旧诊断824行与107总调用不兼容，以隔离856行实现和第108次拒绝契约解决，旧程序／审查器保留。计数审查初次仍用旧上限失败，新独立审查器修正，无板测重跑或数值阈值放宽。下一只准备真实拥有骨架画面的单因素接入，保留源读取。'+links+'以下当前为历史。')
prepend(root/'PROJECT-PROGRESS.md','## 当前：单次常驻合成VPU＋真实模型107通过\n\n'+summary+'\n\n首版全流程已贯通，当前在并发数值可靠性与首次启动资源治理阶段；本次有限通过不增加管理粗估，也不代表整机／长期验收。'+links+'以下当前为历史。')
prepend(root/'Agents.md','- 单次常驻生命周期完成（2026-10-10）：'+summary+' 诊断仅新目标824→856行，旧主fbf330d7…cb8702d／旧model-vpu4bab1a1d…49aab2a保持。全局调用0–106、帧100000–100106，无阶段重开／重建；stage日志同对象，清理actual/null分开。979返回文件核验，旧计数审查器824限制的本机错误保留，新适配器856修正，未重跑板测。ADR_28／02及RESIDENT-SEQUENCE-RESULTS/NEXT、resident-sequence-20261010-r1 completion/next-checkpoint为当前入口；下一真实拥有画面仅准备，旧当前为历史。')
prepend(root/'DIFFICULTIES.md','2026-10-10当前：[ADR_28](ADR/ADR_28.md)单次常驻三窗→103通过，解决阶段重复申请的编排与107诊断容量／编号碰撞边界；旧192坏块未复现，首次启动在一次规整及普通高阶余量条件下成功，不认定永久可靠。[结果](tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md)／[下一](tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md)。以下当前为历史。')
prepend(root/'ADR/README.md','2026-10-10当前：[ADR_28](ADR_28.md)独立记录单VPU／单Engine跨三窗与103的107调用编排及诊断上限问题，Native／ARM／完整数值／518合成码流通过。首次启动与长期可靠性分开，旧模型坏块根因仍待；[结果](../tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md)／[下一](../tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md)。以下当前为历史。')
prepend(t/'README.md','> 2026-10-10当前：[单次常驻生命周期结果](RESIDENT-SEQUENCE-RESULTS-20261010.md)，107实际前向1615700FP32／518合成图像过，一次规整／原内核同，服务和连接结束；[恢复点](evidence/resident-sequence-20261010-r1/next-checkpoint.json)／[下一真实拥有画面](RESIDENT-SEQUENCE-NEXT-20261010.md)仅准备。旧故障未修、永久首启动／5Hz／长期／HDMI待。以下当前为历史。')
adr=root/'ADR/ADR_28.md';text=adr.read_text(encoding='utf-8').replace('状态：用户批准实施；本批结果待验证。','状态：本批单次常驻有限验证完成，永久首次启动及旧数值故障根因仍待。')
text+='''

## 本批实际解决与结果

'''+summary+'''

阶段0调用0–3／阶段1调用4–106连续，stage记录同Engine与VPU对象；驱动身份一次／两端各2缓冲／映射6959104字节，正常资源释放。Engine初始化29321.69921ms，目标200ms仅调度，103首末开始跨度20407.15648ms不作5Hz验收。Host目标mod64含0／16／32均正确，不认定64对齐修复。

旧计数审查器仍硬限824导致本机AssertionError，实际856记录已完整保存；新增独立审查器绑定resident生产者自检856规格，16拒绝／第108次拒绝／856计数源关联／1819组合记录过。没有修改旧源码、数据、阈值或重跑硬件。原异常机制未触发，不能把未复现解释为复制、等待或数学修复。

[完成审查](../tools/pose-v1/evidence/resident-sequence-20261010-r1/completion-review.json)／[结果](../tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md)／[恢复点](../tools/pose-v1/evidence/resident-sequence-20261010-r1/next-checkpoint.json)／[下一单因素](../tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md)。本批获批有限门检结束，不自动启动新增真实绘图／网络负载。
''';adr.write_text(text,encoding='utf-8',newline='\n')
with (root/'ADR/ADR_02.md').open('a',encoding='utf-8',newline='\n') as f:f.write('''

## 2026-10-10补充：单次上下文保持通过，首次资源条件仍需区分

按新[ADR_28](ADR_28.md)，一次VPU实际capture后创建同一主线程Engine，连续三窗4＋103完整通过，107前向1615700FP32／518合成图像正确；窗口切换无VPU／MMAP／Engine重建。准备规整9→28单位／144.80296ms，实际进入31、raw后29、capture后21、首capture20；与上批9→7→0的失败条件不同。保留context可避免阶段重开，但不能声称因此独自修复第一次启动或普通页分配永久可靠。

原两缓冲／cookie／6.64MiB映射／CMA256MiB／驱动／BOOT保持，正常drain-LAST／两STREAMOFF、join后Engine销毁，最终原内核同／进程结束。未清缓存／重启／改CMA／内核。进一步安全连续申请仍须匹配DMA／MMU／cache／固件与释放路径，不能由本次成功跳过。[实际结果](../tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md)。
''')
prep={'status':'old_count_reviewer_rejected107_rows_isolated_adapter_fixed','source':'transcribed tool output; not an original process stderr file','old_tool':'review_model_only_counts.py','old_tool_SHA256':__import__('hashlib').sha256((t/'review_model_only_counts.py').read_bytes()).hexdigest(),'exception':'AssertionError at counts and len(counts)<=824','actual_query_rows':856,'new_tool':'review_resident_counts.py','numeric_rules_relaxed':False,'board_rerun':False,'original_source_generation_failure':'System GBK attempted to read UTF-8 PowerShell; corrected explicit UTF-8 before build; identical partial generated files retained.'}
fresh(e/'tool-failure-history.json',json.dumps(prep,indent=2)+'\n')
print('Resident results, ADR and recovery documents archived; no new board test.')
