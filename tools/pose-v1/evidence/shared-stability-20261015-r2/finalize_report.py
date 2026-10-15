"""Publish only independently verified results, keeping historical failures intact."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;R=E.parents[3]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
a=load(E/'stress-analysis.json');assert a['status']=='passed'
tail=load(E/'latency-tail-analysis.json')
assert load(E/'final-cleanup-review.json')['passed']
n=a['inferences'];m=a['memory'];t=a['timing_ms'];duration=a['duration']['actual_duration_ms']/1000
run=E/'returned-stress/run-stress'
def meminfo(p):
 d={}
 for line in p.read_text().splitlines():
  k,v=line.split(':',1);d[k]=int(v.split()[0])
 return d
before=meminfo(run/'before.meminfo');after=meminfo(run/'after.meminfo')
release=dict(before_CmaFree_KiB=before['CmaFree'],after_CmaFree_KiB=after['CmaFree'],
 before_MemAvailable_KiB=before['MemAvailable'],after_MemAvailable_KiB=after['MemAvailable'],
 note='CMA includes reclaimable file pages; free count alone is not device allocation ownership proof',
 engine_destroyed=a['duration']['engine_destroyed'],no_task_process_remains=a['no_task_process_remains'])
(E/'final-resource-release.json').write_text(json.dumps(release,indent=2)+'\n',encoding='utf-8')
p=E/'REPORT.md';s=p.read_text(encoding='utf-8')
old='日期：2026-10-15。**当前：原编译包三窗和30秒常驻验证通过；用户批准的30分钟连续满速压力阶段正在执行，尚未作长时稳定性结论。** 最终结果将在原值完整回传后更新本报告。'
new=f'日期：2026-10-15。**完成原编译包三窗、30秒/1131次及30分钟/{n:,}次连续推理，数值和内存稳定性观察通过，未观察到崩溃或SDK异常。时延仍有长尾：11次超过1秒，最大4.158秒。** 全部实际输入/输出已回传并按SHA和现行数值规则独立复核；结论限三个冻结来源的串行循环，不称最坏时延或整机长期稳定性通过。'
assert old in s;s=s.replace(old,new)
start=s.index('## 压力阶段状态与分析规则')
s=s[:start]+f'''## 30分钟压力测试结果

初始化完成后实际连续运行 **{duration:.6f}秒**，完成并保存 **{n:,}次**，达到原1800秒时长，未触及90000次上限。含初始化/前后核验的控制器活动耗时1838.161016秒；退出后哈希、归档和回传不计推理时长。没有负载失败重试、延长测试或追加压力阶段。原生进程和控制器均exit0，Engine正常销毁；内核日志前后逐字节相同，SDK/BOOT身份不变、FPGA operating，最终本批进程全部结束。

独立复核了全部 **{n*60400:,}字节**实际流：输入{n*43200:,}字节、分数{n*400:,}字节、姿态{n*16800:,}字节，逐文件SHA与板端清单一致。每次输入/全部100分数逐位冻结参考，所有候选有限；score>0.2的同槽14关节最大三维偏差 **{a['max_checked_joint_delta_mm']:.9f}mm**，符合3mm上限。背景全量仍保存，所有槽最大关节差{a['max_all_joint_delta_mm']:.9f}mm；累计{a['excluded_background_overlimit_joints']:,}个背景关节比较超过3mm，按用户授权仅诊断，不改原值。相同共享图重复同一输入时，相对该来源首次输出的姿态字节变化帧数为{a['same_graph_repeat_pose_changed_frames']:,}，最大单坐标差{a['same_graph_repeat_max_coordinate_mm']:.9f}mm。

SDK融合成员独立核实1021个HardOp完整且唯一覆盖五ZG组，最终连续同步层数612；每次实际完成612，Host/ZG回调各5。常规复制元数据{m['regular_copy_metadata_rows']}条、tensor identity记录{m['regular_identity_rows']}条、时间线{m['timing_record_rows']}条，均限初始化和前三帧，未随62945次线性积累；异常Host原值/两次SDK晚源路径保留，但本轮没有触发，不能称异常分支已实测。

### 内存、句柄与退出释放

共{m['samples']}个资源采样点，暖机30秒后{m['steady_samples']}点。下表起/末为各5点中位数，范围为全部稳态采样。

| 项目 | 起段 | 末段 | 稳态最小–最大 | 变化 |
|---|---:|---:|---:|---:|
'''
for label,key in [('RSS KiB','RSS'),('PSS KiB','Pss'),('Private_Dirty KiB','Private_Dirty'),('VmData KiB','VmData'),('VmSize KiB','VmSize')]:
 v=m[key];s+=f"| {label} | {v['first_median_KiB']:.0f} | {v['last_median_KiB']:.0f} | {v['min_KiB']:.0f}–{v['max_KiB']:.0f} | {v['change_KiB']:+.0f} |\n"
for label,key in [('FD','fd_count'),('线程','Threads'),('映射','map_count')]:
 v=m[key];s+=f"| {label} | {v['first_median']:.0f} | {v['last_median']:.0f} | {v['min']}–{v['max']} | {v['last_median']-v['first_median']:+.0f} |\n"
s+=f'''
PSS拟合斜率{m['Pss']['linear_slope_KiB_per_minute']:.6f}KiB/min，Private_Dirty与VmData无增长，满足预定筛查：RSS/PSS/VmData中位增长≤8MiB、PSS斜率≤64KiB/min、FD末段≤起段+1、线程不增、映射≤起段+2。峰值RSS {m['peak_RSS_KiB']:,}KiB，最低MemAvailable {m['minimum_MemAvailable_KiB']:,}KiB。此负载下**未观察到持续内存泄漏迹象**；不同进程间的绝对RSS差不能用来判断泄漏。

退出前后系统CmaFree为{before['CmaFree']:,}→{after['CmaFree']:,}KiB，MemAvailable为{before['MemAvailable']:,}→{after['MemAvailable']:,}KiB。CMA空闲数受可回收文件页影响，不能仅凭该数推断分配所有权；正常Engine销毁、无本批进程、驱动无新增错误一并核验。未清缓存、规整、重启或更改系统配置。[释放记录](final-resource-release.json)、[最终清理审查](final-cleanup-review.json)。

![内存趋势](memory.png)

### 各阶段耗时

| 每次调用阶段 | 均值ms | 中位ms | P95 ms | 最大ms |
|---|---:|---:|---:|---:|
'''
for name,key in [('Engine完整process','process_ms'),('PS预处理','preprocess_ms'),('Session.forward','forward_ms'),('末端等待','final_wait_ms'),('最终输出读取','output_read_ms')]:
 v=t[key];s+=f"| {name} | {v['mean']:.6f} | {v['median']:.6f} | {v['p95']:.6f} | {v['max']:.6f} |\n"
s+=f'''
包含完整原值保存、数值比较和循环开销的实际提交速率 **{n/duration:.6f}次/秒**。Engine处理函数时间不包括外部保存/比较；forward包含回调等嵌套区间，各项不能直接相加当总耗时，未调用此前有负值的SDK getLayerTime。此为连续串行、保留证据的压力负载，不能等同无日志理论NPU吞吐或VPU/TCP整机吞吐。

**时延长尾单列为未解决项（D41）**：35次>50ms、12次>100ms、11次>1000ms；P99 {tail['percentiles_ms']['99']:.6f}ms，P99.9 {tail['percentiles_ms']['99.9']:.6f}ms，P99.99 {tail['percentiles_ms']['99.99']:.6f}ms。最大inv17191（0起）process4158.13099ms，其中forward4150.52165ms，而进程CPU时间仅20.177ms，保存0.28621ms、比较0.19545ms；尖峰不在该帧外部保存/比较区间，不能归为NPU纯算术耗时。所有尖峰仍数值通过，未触及20秒进度停滞停止线；原规则的运行完成不等于满足实时最坏时延。

系统累计出现movable分配停顿65次、major fault296次、后台/直接页回收，标准CMA空闲采样0–117968KiB，提示系统内存回收环境有变化；目前只保存了聚合vmstat与稀疏采样，**不能据此认定页回收、文件落盘、SDK调度或NPU为根因**。未追加定位负载或自动延长压力测试。完整前20个尖峰与邻近资源诊断见[latency-tail-analysis.json](latency-tail-analysis.json)。

![延迟趋势](latency.png)

### 原失败、归档恢复与适用边界

r1首次因可选/proc children接口缺失被观测器中止，未完成帧；原失败、强制清理和日志完整保留在[原报告](../shared-stability-20261015-r1/REPORT.md)。r2仅修复观测器兼容，两个ARM二进制不改，经用户明确“允许按原预算继续”后新目录/新Session执行。

推理结束后，3.80GB原值的xz压缩超过一次SSH助手180秒超时；只读确认原归档进程仍在工作，继续监测同一进程，完成后取回现有文件并安全解压、全量SHA复核。**未重跑推理、未重建或覆盖原归档**。该传输管理超时不计为NPU运行故障，但保留错误和恢复证据：[archive-return-recovery.json](archive-return-recovery.json)、`12-archive-status.txt`及`archive-watch-*.txt`。板端时钟与主机日期不同，归档时间戳不当作实际日期；1800秒预算依据单调时钟。

最终只读审查第一次直接SSH执行dmesg，将原启动日志版权符号UTF-8显示为字面\\xc2\\xa9，触发字节比较断言。采用与原控制器完全相同的Python subprocess.check_output捕获后，完整字节与结束时日志一致；差异仅该显示转义，未新增内核消息。首次断言及两份原日志均保留，见[final-cleanup-review.json](final-cleanup-review.json)。

本次只有三个冻结输入重复运行，无新增数据集准确率评估、首次冷启动保证、VPU/视频/TCP叠加或热稳定性验收；标准温度/频率节点不可用，温度未知。有限30分钟不能证明任意输入/异常路径/无限期运行绝对无泄漏，也不解除旧DATA调查暂停。正式演示/旧模型未替换，所有本批连接/子进程结束，FPAI已恢复停止。

完整结论以[stress-analysis.json](stress-analysis.json)、[逐帧记录](returned-stress/run-stress/results/frames.jsonl)、[资源采样](returned-stress/run-stress/resources.jsonl)、[控制器退出](returned-stress/run-stress/controller-summary.json)和[板端全文件SHA](returned-stress/run-stress/evidence-files.json)为准。原值位于同目录results的inputs.f32/scores.f32/poses.f32，压缩归档保留stress.tar.xz。源码冻结归档和交叉编译日志保留于r1证据目录；最终交付身份见[completion-review.json](completion-review.json)。
'''
p.write_text(s,encoding='utf-8')
overview=f'2026-10-15共享新包稳定性已完成：原编译包三窗、30秒/1131次及30分钟/{n:,}次实板串行推理的数值/内存观察通过，完整实际输入/输出回传后SHA及现行门禁独立复核通过。暖机后RSS75204→73628KiB、PSS73887→71779KiB，Private_Dirty/VmData不增，FD13/线程3/映射86保持；Engine均值{t["process_ms"]["mean"]:.6f}ms，含保存/比较速率{n/duration:.3f}次/秒。无崩溃/SDK异常/新增内核日志，但11次process超过1秒、最大4.158秒（forward4.151秒/进程CPU20.177ms），时延长尾原因未知，列D41，不称实时性通过。Engine正常销毁、本批进程和连接结束。r1可选/proc接口失败原样保留，r2兼容修复4项本机检查后经用户明确允许新Session继续；归档SSH超时只监测/取回原归档，未重跑推理。模型/RAW/数学/CPU注册/NPU分配/SDK/BOOT不改，常规诊断限前三帧，异常证据路径保留。仅三个冻结输入，无视频/网络叠加，不能扩展为整机或任意输入绝对无泄漏保证。[完整报告](tools/pose-v1/evidence/shared-stability-20261015-r2/REPORT.md)。正式演示不换，旧DATA继续暂停。'
p=R/'PROJECT-PROGRESS.md';s=p.read_text(encoding='utf-8');lines=s.splitlines()
lines[2]='更新日期：2026-10-15。最近实际验证：共享新包三窗、30秒/1131次及30分钟/62,945次实板串行推理完成，数值/内存观察通过、未观察到崩溃，全部原值回传独立复核；11次>1秒、最长4.158秒的时延长尾待定位（D41）。仅三个冻结来源，无视频/网络叠加；现行score>0.2/3mm规则保持，旧失败原值保留。正式核心原CPU107/整机复核仍待另验，旧DATA暂停。历史快照见[归档索引](ADR/history/20261013/README.md)。'
s='\n'.join(lines)+'\n';start=s.index('2026-10-15新包稳定性测试正在执行：');end=s.index('\n\n',start);s=s[:start]+overview+s[end:]
s=s.replace('本次无新上板/部署，旧运行exit1不回写。新源码/ARM包已准备','该门禁修改阶段无新上板/部署（后续独立稳定性实板结果见本页首段），旧运行exit1不回写。新源码/ARM包当时已准备')
s=s.replace('永久首启动、严格整机5Hz、30分钟、HDMI、真实采集与零拷贝未验收','永久首启动、严格整机5Hz、整机30分钟、HDMI、真实采集与零拷贝未验收（共享图独立串行30分钟已通过）')
p.write_text(s,encoding='utf-8')
p=R/'REFERENCES.md';s=p.read_text(encoding='utf-8');start=s.index('2026-10-15共享新包稳定性：');end=s.index('\n\n',start);s=s[:start]+overview+s[end:];p.write_text(s,encoding='utf-8')
p=R/'DIFFICULTIES.md';s=p.read_text(encoding='utf-8');s=s.replace('30分钟压力阶段仍执行中，不能预先记为稳定性通过',f'后续30分钟/{n}次独立实板及完整原值复核通过，未观察到持续内存/句柄增长；仅三冻结来源串行，无视频叠加。归档SSH超时监测原压缩进程并取回，不重跑推理');p.write_text(s,encoding='utf-8')
p=R/'DIFFICULTIES.md';s=p.read_text(encoding='utf-8');assert '| D41 |' not in s
row='| D41 | 共享图30分钟串行推理出现11次>1秒时延尖峰，最大process4158.13099ms，forward4150.52165ms、CPU20.177ms；全部数值仍过、无崩溃/内存增长 | 全62945次无裁剪：均值23.27822ms、P9523.45126ms、P9924.49497ms；保留逐帧、粗粒度资源与vmstat，movable分配停顿/回收存在但未能对应根因。[长尾证据](tools/pose-v1/evidence/shared-stability-20261015-r2/latency-tail-analysis.json)、[报告](tools/pose-v1/evidence/shared-stability-20261015-r2/REPORT.md) | 运行完成及内存观察通过不代表实时最坏时延通过；阻塞发生在forward区间，SDK/调度/页回收/设备责任未知；未追加定位负载或恢复旧DATA调查 |'
lines=s.splitlines();i=next(i for i,v in enumerate(lines) if v.startswith('| D40 |'));lines.insert(i+1,row);p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
p=R/'ADR/ADR_48.md';s=p.read_text(encoding='utf-8');s=s.replace('本次没有新板端推理、部署或Session，新ARM包已准备但未上板；','上述门禁修改和离线回放阶段没有新板端推理、部署或Session，当时新ARM包已准备但未上板；')
heading='## 2026-10-15后续独立实板与30分钟验证'
assert heading not in s
s+='\n'+heading+'\n\n'+overview.replace('](tools/','](../tools/')+'\n\n旧逐位/v1超限运行exit1及原值不回写。上述新运行exit0只针对v2条件与新Session，未将背景漂移或物理偏置假设改写为已验证原因。\n';p.write_text(s,encoding='utf-8')
p=R/'Done.md';s=p.read_text(encoding='utf-8');heading='## 2026-10-15：共享新包实板验证与30分钟连续压力测试'
assert heading not in s
entry=heading+'\n\n### 工程内容总结\n\n'+overview+'\n\nWindows工作目录D:/FPGACompetitionProject，FPAI/GCC9.4复用原核心构建常驻入口，Lite SDK3.39.0/ZG330新目录部署原编译包与常驻包。先3窗，再30秒，审查通过后一次1800秒/最多90000次；未触及次数上限，无自动重试或延长。先保存每次60400字节完整实际输入/输出再比较；有限性、score>0.2的3mm同槽三维门限和输入/全部分数逐位均过，实际612完成计数/5 Host/5 ZG覆盖全检。3.80GB原值/逐帧日志/资源与哈希全部取回，SDK/BOOT/内核同，最终清理审查通过。未规整/清缓存/重启、未改启动配置，未人为触发异常分支。\n\n### 对后续开发的参考\n\n板端/proc可选字段需能力探测，mandatory RSS/PSS不能降级为缺省值；进程组所有权和启动身份绑定用于独立清理。常规诊断应固定采样上限，完整输出流式保存，避免诊断本身线性吃内存。内存按同进程暖机基线比较RSS/PSS/Private_Dirty/VmData及FD/线程/映射，文件页缓存增长不直接归因匿名泄漏。压缩/哈希/回传与推理预算分开；归档工具超时先检查原进程/文件，不能因此重跑负载或覆盖证据。有限三输入30分钟无泄漏迹象不扩展为任意输入/异常路径或整机可靠性证明；SDK硬件负时间计时不调用，独立Engine/墙钟用于实测。文档前后身份另存documentation-revision.json，历史失败及旧完成清单不改。\n\n'
s=s.replace('# 已完成工作记录\n\n','# 已完成工作记录\n\n'+entry,1);p.write_text(s,encoding='utf-8')
docs=[]
for item in load(E.parent/'shared-stability-20261015-r1/documentation-before.json'):
 p=Path(item['Path']);docs.append(dict(path=str(p),before_sha256=item['Hash'].lower(),after_sha256=sha(p)))
assert docs[0]['before_sha256']==docs[0]['after_sha256'],'Agents must not change'
(E/'documentation-revision.json').write_text(json.dumps(dict(reason='Actual completed board validation; prior completion manifests remain immutable',files=docs),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(report=str(E/'REPORT.md'),inferences=n,status='published_verified_results'),indent=2))
