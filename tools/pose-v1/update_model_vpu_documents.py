"""Archive the finite contrast and its startup blocker without rewriting failures."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
T=ROOT/'tools/pose-v1';E=T/'evidence/model-vpu-20261010-r2'
r=json.loads((E/'completion-review.json').read_text());assert r['correct_calls']==111 and not r['failed_stage']['Engine_created']
def fresh(path,text):
    assert not path.exists();path.write_text(text,encoding='utf-8',newline='\n')
def prepend(path,text):
    old=path.read_text(encoding='utf-8');head,sep,tail=old.partition('\n');path.write_text(head+'\n\n'+text.strip()+'\n\n'+tail.lstrip('\n'),encoding='utf-8',newline='\n')
fresh(T/'MODEL-VPU-RESULTS-20261010.md','''# 同一程序模型／合成VPU对照结果

2026-10-10。前三个阶段通过，第四阶段在VPU首次capture之前失败，按停止条件结束；并发103未通过，原模型坏块根因仍未解决。

## 身份与契约

同一ARM程序SHA256 `4bab1a1d61c54fdebde33eaa71a1ec378e3159c964c5dcd8e6e198aa749aab2a`，manifest `28d76b0245bc7b406fc9f66d1a5ed92699e1d25ba48ee9e7ac3de4b46cde6da0`，403载荷102来源。原主、Engine／桥／CPU数学／模型／RAW／SDK／BOOT保持。Native／ARM生命周期各6拒绝、原Run各9拒绝及拥有值／独立flush过；Host107／12注册／59600仅冻结身份复用，非新入口Host107。

## 实际阶段

| 阶段 | 结果 | 完整FP32对照 | 编码 |
|---|---|---:|---|
| model-three | 4次完整正确，exit0 | 60,400 | 无 |
| vpu-three | 4次完整正确，exit0 | 60,400 | 310合成NoInput图像，56,930字节 |
| model-103 | 103次完整正确，exit0 | 1,555,300 | 无 |
| vpu-103 | DQBUF EIO，exit1；Engine未创建，前向0 | 0 | 首次capture0，码流0字节 |

合111实际前向／1,676,100 FP32逐位旧参考，完整CSI、输入、100候选分数／姿态均先保存后比较；192真实来源109232128／109285376保持，1776对象行／888拥有快照和888计数查询稳定，计数全234，999复制元数据。111次582检查首次638/poll1。六计算Host／七ZG组、1173融合及0→745通过，profiling-off。Host目标mod64含0／16／32／48均FP32对齐正确，不认定64对齐修复。

三窗VPU实际非空capture后创建主线程Engine，310帧ID、全部像素、实际PTS、owned packet／drain／LAST及join后Engine销毁核验过。首次ready可以是参数集，不能称首次图像。合成NoInput不计姿态吞吐，不是实际骨架／RTSP／显示测试。

## 第四阶段失败位置

VPU成功协商原两缓冲／NV12／H264／cookie并排入两个原始输入，STREAMON后CAPTURE DQBUF errno5。新增内核明确记录order7／512KiB `GFP_KERNEL|__GFP_NORETRY|__GFP_ZERO`申请失败，路径`mvx_mmu_alloc_contiguous_pages → map_protocol_v2 → mvx_fw_factory`。故障瞬间普通512KiB及以上空闲块为0，约104MiB总空闲不等于连续页可用。

取证序列：entry普通512KiB折算9→raw REQBUFS后7→capture REQBUFS后0，之后prime／两STREAMON均0。快照不是分配承诺；映射长度也不证明所有内核内部物理分配方式。首次capture0、Engine未创建、前向0，因此没有192／ScatterND模型失败输入或晚源触发。`Engine_destroyed`记录仅是空指针reset清理点，不能当实际创建／销毁证明。

失败后两abort STREAMOFF返回0，worker已join，七项独立保存成功。最后阶段91文件完整核验，没有输出门禁或伪造视频通过。成功阶段内核原字节不变；最后新增分配错误保留，不白名单隐藏。所有项目程序／端口及代理连接结束。

## 资源准备与限制

自主取证规整共3次：共同准备3→10单位／61.46912ms；VPU三窗前6→6／15.20305ms；VPU103前8→9／14.12106ms。每次都有buddyinfo／pagetypeinfo／meminfo／vmstat及内核前后、原因与耗时；不是失败后循环规整或重跑。三窗成功与末阶段失败之前资源准备不同，因此不是严格相同内存条件。

策略16单位只是历史映射6.64MiB加固件512KiB的准备裕量，非已证分配下界。规整后仍失败，不能把规整写成首启动可靠性修复。CMA仍256MiB，未清缓存、重启、改BOOT／CMA／内核／驱动／SDK／数学。最终MemAvailable740060KiB／CmaFree40KiB／普通单位8是释放后现场；不能反证申请瞬间0或证明泄漏、永久可靠性。

## 结论与恢复

同一程序无视频103完整正确，仅加合成编码的三窗也正确；最后的103组合没有模型计算，不构成VPU导致旧模型坏块的因果证据。旧坏块、前次数据残留、稍后正确设备源和异常两轮读取继续保留。完整并发103、持续5Hz／长期／HDMI／零拷贝仍待；管理粗估83/100保持。

传输恢复由用户明确批准；实际本机bundled Git缺scp.exe，已换本机完整Git SSH/SCP，并校验既有ED25519密钥、远端包哈希。认证秘密仅在传输进程内存中使用；用户另明确要求将连接配置记录到Agents.md。审批超时记录与原失败保留。

证据：[完成审查](evidence/model-vpu-20261010-r2/completion-review.json)、[资源审查](evidence/model-vpu-20261010-r2/resource-review.json)、[启动失败](evidence/model-vpu-20261010-r2/vpu-103.failed-review.json)、[恢复点](evidence/model-vpu-20261010-r2/next-checkpoint.json)、[ADR_27](../../ADR/ADR_27.md)、[ADR_02](../../ADR/ADR_02.md)。下一先按[资源生命周期方案](MODEL-VPU-NEXT-20261010.md)准备，旧失败不重跑。
''')
fresh(T/'MODEL-VPU-NEXT-20261010.md','''# 下一步：先恢复VPU首次启动条件，再完成长序列对照

本批在异常后安全结束；以下仅准备方案，不是新板测验收。先读[结果](MODEL-VPU-RESULTS-20261010.md)、[ADR_27](../../ADR/ADR_27.md)／[ADR_02](../../ADR/ADR_02.md)和[恢复点](evidence/model-vpu-20261010-r2/next-checkpoint.json)。不重跑旧vpu-103，不循环规整／清缓存／重启。

## 当前判断

MVX固件512KiB普通连续页失败已明确，不能用总可用内存或空闲CMA承诺成功。本次capture REQBUFS阶段普通高阶页9→7→0，规整后仍失败；扩大CMA、改MOVABLE或用户态SDK占位不能直接成为驱动固件的合法内存来源。

优先复用已验收的同进程常驻上下文策略：一旦实际capture就绪，让同一VPU工作者和MMAP在三窗、103窗口之间保留，不在阶段切换重开。它减少重复申请机会，仍不解决第一次启动；新入口必须分别报告首次启动与常驻内容正确性。

## 准备工作与门检

1. 本机审计原匹配amvx二进制／发布包，整理firmware申请、raw／capture缓冲分配顺序及公共V4L2可用接口。不修改原驱动；找不到匹配源码时明确证据限制，不猜测预加载协议或直接移交SDK块。
2. 设计独立资源生命周期编排：编码首次capture后创建主线程Engine，同一上下文保持三窗→103，两窗口之间只切输入调度；错误传播、owned packet、最大帧数／时间、join后Engine销毁保持。修正清理证据标签，区分实际Engine创建／销毁和空指针释放点。冻结r2与所有失败证据。
3. 先Native／ARM资源所有权和跨阶段失败停止契约；身份变化时重新审查，而非直接复用旧门禁。Host107仅原CPU数学／注册身份完全相同时复用。
4. 新目录仅一次有界首次启动。资源快照和可选一次规整记录完整前后；若首次capture失败即保存停止，不增加重试计数或放宽错误。取得首次capture后才三窗完整参考，再103；103失败完整保存，不替换成短窗通过。总预算、首次5秒／Engine60秒及1000编码帧保持有界，具体新入口预算在实施前审查。
5. 若普通连续申请仍不能可靠取得，另立具体驱动分配方案审查：匹配源码、设备DMA／MMU、cache同步、固件地址／大小／生命周期和释放均需证明；修改CMA／DTB／内核／BOOT须独立备份与恢复方案。本批没有此配置变更授权。

只有首次启动和常驻103都取得完整证据，才继续加入一个真实绘图／拥有画面因素；显示子进程／网络分开。旧192模型残留仍是另一未解决问题，异常Host暂存及两晚源读取不得删除。NoInput不算新姿态吞吐，单次通过不当30分钟／稳定5Hz／HDMI验收。
''')
summary='''同ELF模型／合成VPU对照r2已结束：Native／ARM6生命周期及9运行拒绝过，原Host107／12注册59600身份复用；model-three4、vpu-three4及model-103共111前向1676100FP32逐位旧参考，310合成图像／实际PTS过。最后vpu-103在首次capture前DQBUF EIO，内核MVX固件order7／512KiB普通页失败；Engine未创建、前向0，无模型坏块复现。规整3次有记录但仍失败，不是首启动可靠性修复；两abort STREAMOFF／join／七项保存过，成功内核同而最后新增错误完整保留。原数学／模型／SDK／BOOT与异常两晚源保持，全程序／端口／代理连接结束。根因未修、并发103／长期／5Hz／HDMI未过，83/100保持。'''
prepend(ROOT/'Done.md','''## 2026-10-10：同程序模型／VPU对照与首次启动阻断归档

### 工程内容总结

'''+summary+'''

### 对后续开发的参考

普通高阶页在raw／capture申请期间9→7→0，即使约104MiB总空闲仍不能满足固件512KiB连续申请。减少上下文重复初始化可降低再次分配机会，但首次启动仍须独立验收；不将CMA空闲、规整或策略16单位当分配保证。无视频103正确、视频三窗正确，视频103未进入Engine，不能推断VPU导致192残留。下一只准备资源生命周期和同上下文跨阶段方案。[结果](tools/pose-v1/MODEL-VPU-RESULTS-20261010.md)／[ADR_27](ADR/ADR_27.md)／[下一方案](tools/pose-v1/MODEL-VPU-NEXT-20261010.md)／[恢复点](tools/pose-v1/evidence/model-vpu-20261010-r2/next-checkpoint.json)。以下当前为历史。''')
prepend(ROOT/'PROJECT-PROGRESS.md','## 当前：同身份对照前三阶段通过，VPU首次启动仍阻断\n\n'+summary+'\n\n[结果](tools/pose-v1/MODEL-VPU-RESULTS-20261010.md)／[下一方案](tools/pose-v1/MODEL-VPU-NEXT-20261010.md)／[恢复点](tools/pose-v1/evidence/model-vpu-20261010-r2/next-checkpoint.json)。首版全流程已贯通，目前处于并发数值可靠性与编码启动资源治理阶段；管理粗估83/100不变，不是功能通过率。以下当前为历史。')
prepend(ROOT/'DIFFICULTIES.md','2026-10-10当前：[ADR_27](ADR/ADR_27.md)同程序对照前三阶段通过，最后VPU启动512KiB普通连续页不足，规整后仍失败；Engine创建前退出，不归因192模型坏块。[ADR_02](ADR/ADR_02.md)同决策追加首次启动反例，明确常驻与首次启动分别验收。[结果](tools/pose-v1/MODEL-VPU-RESULTS-20261010.md)／[下一方案](tools/pose-v1/MODEL-VPU-NEXT-20261010.md)。以下当前为历史。')
prepend(ROOT/'AGENTS.md','- 同程序模型／合成VPU对照结束（2026-10-10）：'+summary+' r2 4bab1a1d…49aab2a／manifest28d76b02…cde6da0，403包102来源；1776对象／888shadow、888查询234、999元数据稳定。资源规整61.46912／15.20305／14.12106ms，共同与两VPU前各一次，非失败后循环重试。末次9→7→0普通高阶页，释放后740060KiB／CmaFree40／普通8仅现场。清理Engine_destroyed为null reset点，不证明创建。ADR_27／02、MODEL-VPU-RESULTS/NEXT及model-vpu-20261010-r2 completion/next-checkpoint为当前入口；下一资源生命周期仅准备，旧当前／传输阻断为历史。')
prepend(ROOT/'ADR/README.md','2026-10-10当前：[ADR_27](ADR_27.md)同ELF模型／合成VPU对照：前三阶段通过，末次固件512KiB申请失败、Engine未创建。规整后仍失败，补充[ADR_02](ADR_02.md)同决策结果，不认定模型坏块根因或稳定并发103通过。[结果](../tools/pose-v1/MODEL-VPU-RESULTS-20261010.md)／[下一](../tools/pose-v1/MODEL-VPU-NEXT-20261010.md)。以下当前为历史。')
prepend(T/'README.md','> 2026-10-10当前：[同程序模型／VPU对照结果](MODEL-VPU-RESULTS-20261010.md)。前三阶段111前向1676100FP32及310合成图像通过，第四阶段首次capture前固件512KiB申请失败，Engine未创建。全部服务／连接关闭；[恢复点](evidence/model-vpu-20261010-r2/next-checkpoint.json)／[下一资源生命周期](MODEL-VPU-NEXT-20261010.md)。以下当前入口为历史。')
prepend(ROOT/'ADR/ADR_27.md','''## 当前结果（2026-10-10）

'''+summary+'''

实际前三阶段分别4／4／103，1776对象／888快照／888计数234、999元数据稳定。最后新内核故障为固件普通连续页申请，raw／capture阶段普通单位9→7→0；没有Engine、模型坏输入或晚源触发。成功内核原字节相同，最后新错误保留；阶段91文件及清理独立核验，未生成vpu-103门禁。规整61.46912／15.20305／14.12106ms，三处条件差别明确，不是首启动修复。

传输由用户明确恢复授权，认证成功；bundled Git缺scp.exe，以本机完整Git SSH/SCP修正，保持ED25519主机密钥与包哈希。原审批超时和工具失败留档。旧“板测未执行／全部待传输”为历史，不再当前。

[实际结果](../tools/pose-v1/MODEL-VPU-RESULTS-20261010.md)／[完成审查](../tools/pose-v1/evidence/model-vpu-20261010-r2/completion-review.json)／[下一资源生命周期](../tools/pose-v1/MODEL-VPU-NEXT-20261010.md)。下一先处理首次启动条件与常驻上下文，不直接增加并发因素或扩大CMA。''')
with (ROOT/'ADR/ADR_02.md').open('a',encoding='utf-8',newline='\n') as f:f.write('''

## 2026-10-10补充：规整后首次启动反例

同程序模型／合成VPU对照前三阶段111前向／1676100FP32正确，310合成码流通过；第四阶段在Engine之前DQBUF EIO，内核同一路径order7／512KiB普通连续申请失败。启动前有记录规整8→9单位／14.12106ms，raw REQBUFS后7、capture REQBUFS后0，约104MiB总空闲不能满足该连续申请；失败后释放恢复普通8并不反证瞬间不足。没有新模型坏块，不能将此错误归为192／ScatterND早读。

本批总3次资源准备规整，不清缓存、重启、改CMA／BOOT／驱动。两abort STREAMOFF成功／worker join／七项落盘保存，未重试旧失败。该反例将“规整可诊断并偶尔推进”与“可靠首次启动”明确分开；常驻能减少重新分配，但第一次成功仍要单独取得。下一仅准备同上下文跨短／长阶段编排和匹配驱动分配路径审计，安全连续申请／CMA修改另议。[结果](../tools/pose-v1/MODEL-VPU-RESULTS-20261010.md)／[ADR_27](ADR_27.md)／[下一](../tools/pose-v1/MODEL-VPU-NEXT-20261010.md)。
''')
prepend(T/'MODEL-VPU-RESUME-20261010.md','## 当前恢复点已更新\n\n传输已恢复，前三阶段完成，第四阶段VPU固件分配失败已完整回传并结束。全部连接关闭，无后台；不重跑失败。[结果](MODEL-VPU-RESULTS-20261010.md)／[下一](MODEL-VPU-NEXT-20261010.md)／[检查点](evidence/model-vpu-20261010-r2/next-checkpoint.json)。以下待传输说明为历史。')
print('Documents archived; failed VPU103 remains failed, no new board execution.')
