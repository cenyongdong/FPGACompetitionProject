"""Update status documents and bind completed evidence; no new execution."""
from pathlib import Path
import hashlib,json,ast
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/axi-pair-20261011-r4';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def insert(path,text):
    p=R/path;data=p.read_text(encoding='utf-8');head,tail=data.split('\n',1);p.write_text(head+'\n\n'+text.strip()+'\n'+tail,encoding='utf-8',newline='\n')
done='''## 2026-10-11：AXI／UDMA匹配实现核验，双模式动态内存与VPU对照完成

### 工程内容总结

匹配AXI/XRT库和当前板端UDMA模块只读审查，确认16MiB共享暂存、DMA锁／状态轮询、UDMA缓存同步再memcpy；copyFrom与read应用入口不同但共享底层读取路径。不能把软件存在同步扩大为NPU写入已完成证明。新增独立公开API适配及SDK所有者／有界编排，r4主程序b2f7db68…73fec7、manifestde0ace33…bf975，25来源；原CPU/Gather、模型、SDK、BOOT未改。

Host两方法／四代／两实际类型376320字节、8拒绝过；copy/read及两VPU模式共400动态对4704000 FP32完整C++逐位正确，NumPy独立核对全部指纹和保存141120 FP32字节。地址100667392／100697664，96MiB自有前缀不访问，真实dtype／布局／全有效分布保持，无模型Session或NPU生产。Host107沿用前批身份，本轮没有重跑原推理器。

两VPU模式226／229合成图像全部ID／实际PTS／解码内容通过，正常drain-LAST、两STREAMOFF、所有自有块归还、join后SDK毁／内核同，全部测试与会话结束，无后台。普通512KiB单位17／83，规整0；最终MemAvailable714320KiB/CmaFree37544KiB仅现场。r1打包／r2与r3构建问题、修正和回传权限兼容难点保留在ADR_36；原归档和数据不覆盖。

### 对后续开发的参考

本轮未复现模型坏索引，不认定VPU无责、cache／DMA根因已修或read包装器可替代完整修复。仍缺NPU输出可见性、DMA状态退出保证及共享锁所有实例覆盖三项匹配契约。下一据正式依据准备真实NPU生产者对照，不猜寄存器／delay或用晚源修补。原异常读取及整数门检保持，103完整／严格5Hz／长期／HDMI待，管理83/100不变。[结果](tools/pose-v1/AXI-READ-RESULTS-20261011.md)／[ADR_36](ADR/ADR_36.md)／[下一](tools/pose-v1/AXI-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/axi-pair-20261011-r4/next-checkpoint.json)。以下当前为历史。
'''
insert('Done.md',done)
status='''## 当前：双模式内存读取通过，剩余生产者／DMA完成责任待证

匹配AXI/XRT与板端UDMA模块审查确认锁、轮询和缓存同步路径。独立两应用方法在无VPU／合成VPU下共400动态对4704000 FP32正确，两VPU共455图像／实际PTS／解码正确，无NPU／完整模型。当前未复现原192坏片段；不能把内存对照通过称为模型并发修复。

项目仍处于首版全链之后的并发数据可靠性定位阶段，管理估算83/100保持（非通过率／工期）。完整103／严格5Hz／长期／HDMI待。本批批准范围结束，程序／连接全关闭，规整0／内核同／原模型SDKBOOT保持；下一匹配生产完成契约及最小真实NPU对照仅准备。

[结果](tools/pose-v1/AXI-READ-RESULTS-20261011.md)／[ADR_36](ADR/ADR_36.md)／[下一](tools/pose-v1/AXI-READ-NEXT-20261011.md)／[当前恢复](tools/pose-v1/evidence/axi-pair-20261011-r4/next-checkpoint.json)。以下当前为历史。
'''
insert('PROJECT-PROGRESS.md',status)
agent='''- AXI／UDMA读取对照本批完成（2026-10-11）：用户批准READ-PHASE-NEXT，ADR_36。匹配AXI/XRT/板端UDMA模块确认16MiB暂存、mutex/状态轮询、CPU缓存同步；不能视为NPU/DDR完成证明。独立r4主b2f7db68…73fec7/Hosta1823244…86406c/manifestde0ace33…bf975，25来源；Host376320字节/8拒绝、四模式400动态对4704000FP32过，NumPy400指纹/保存141120FP32过；真实192 dtype/布局/全有效声明，较高PL地址100667392/100697664，前缀不访问。原CPU/Gather源哈希同，Host107引用上批非新跑，无Session/NPU。两VPU226/229合成图像实际PTS/解码/drain-LAST/STREAMOFF10/9/全块归还/join后SDK毁/内核同通过，NoInput不计姿态吞吐。页准备17/83，规整0；最终MemAvailable714320/CmaFree37544KiB仅现场，项目进程端口及SSH/SCP全结束，无后台。r1头名/r2命名空间与char*Werror/r3const签名失败保留，r4修正；原归档权限以byte-only readable副本解决审查，不改数据。未复现旧坏索引，根因未修，原首次快照与异常两晚源保持。当前AXI-READ-RESULTS/NEXT/RESPONSIBILITY及evidence/axi-pair-20261011-r4 completion/next-checkpoint；下一生产者/事务完成契约方案未执行，不猜同步/延时/私有映射或改SDK/BOOT，83/100、103完整/严格5Hz/长期/HDMI待。以下实施状态为历史。'''
insert('Agents.md',agent)
for path in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(path,'2026-10-11最新：[ADR_36](ADR/ADR_36.md)匹配AXI／UDMA责任审查及两方法／四条件内存对照完成；400动态对过，无NPU生产，原模型根因未修。锁／轮询／cache同步存在但生产完成未知。[结果](tools/pose-v1/AXI-READ-RESULTS-20261011.md)／[责任证据入口](tools/pose-v1/AXI-READ-RESPONSIBILITY-20261011.md)／[下一](tools/pose-v1/AXI-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/axi-pair-20261011-r4/next-checkpoint.json)。本批已结束、无规整／后台；以下当前为历史。')
insert('ADR/README.md','最新：[ADR_36](ADR_36.md)匹配AXI／UDMA读取责任边界与独立双模式对照，400动态对及455合成VPU图像通过；无NPU生产，模型根因未修。[结果](../tools/pose-v1/AXI-READ-RESULTS-20261011.md)／[下一](../tools/pose-v1/AXI-READ-NEXT-20261011.md)。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[AXI／UDMA审查与双模式对照](AXI-READ-RESULTS-20261011.md)已完成，Host契约、400动态对、455合成图像过。无NPU生产，根因未修；原异常读取保留。[ADR_36](../../ADR/ADR_36.md)／[责任入口](AXI-READ-RESPONSIBILITY-20261011.md)／[下一](AXI-READ-NEXT-20261011.md)／[恢复](evidence/axi-pair-20261011-r4/next-checkpoint.json)。本批连接／程序全结束，未用户暂停，以下当前为历史。')
documents=['Done.md','PROJECT-PROGRESS.md','Agents.md','ADR/ADR_36.md','ADR/README.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','tools/pose-v1/README.md','tools/pose-v1/AXI-READ-RESULTS-20261011.md','tools/pose-v1/AXI-READ-NEXT-20261011.md','tools/pose-v1/AXI-READ-RESPONSIBILITY-20261011.md']
data=json.loads((E/'data-review.json').read_text())
completion={'status':'matching_AXI_read_audit_and_four_pattern_contrasts_passed_model_root_unresolved','date':'2026-10-11','data_review_sha256':sha(E/'data-review.json'),'programs':data['programs'],'manifest_sha256':data['manifest_sha256'],'Host_bytes':376320,'Host_refusals':8,'Host107_new_run':False,'Host107_prior_completion_sha256':data['Host107_prior_completion_sha256'],'dynamic_pairs':400,'Cpp_FP32_bitwise':4704000,'NumPy_pattern_trace_pairs':400,'NumPy_saved_FP32_bitwise':141120,'VPU_decoded':455,'VPU_packets':459,'full_model_Session':False,'NPU_forward':False,'root_fixed':False,'compactions':0,'kernel_unchanged':True,'all_programs_connections_closed':True,'management_estimate':83,'estimate_is_not_acceptance_rate':True,'documents_sha256':{p:sha(R/p) for p in documents},'scripts_sha256':{p.name:sha(p) for p in (R/'tools/pose-v1').glob('*axi*py')},'runner_sha256':sha(R/'tools/pose-v1/run-axi-pair.sh'),'build_failures_sha256':{tag:sha(R/('.local/pose-v1-build/axi-pair-20261011-'+tag+'/build.log')) for tag in ('r2','r3')},'new_build_sha256':sha(R/'.local/pose-v1-build/axi-pair-20261011-r4/build-result.json')}
(E/'completion-review.json').write_text(json.dumps(completion,indent=2)+'\n',encoding='utf-8',newline='\n')
checkpoint={'status':completion['status'],'user_paused':False,'active_tests':False,'services_running':False,'SSH_SCP_closed':True,'completion_sha256':sha(E/'completion-review.json'),'root_fixed':False,'board':'/tmp/pose-axi-pair-20261011-r4','package':'.local/pose-v1-axi-pair/package-20261011-r4','build':'.local/pose-v1-build/axi-pair-20261011-r4','next':'Read AXI-READ-RESULTS/NEXT/RESPONSIBILITY and ADR_36. Approved scope complete; no new model/NPU experiment. Preserve original first-return/CPU snapshots and all failure late reads. Confirm matched producer and DMA completion contract before new minimal producer contrast; do not replay failed Engine, add delay, patch indices, guess registers/private mappings or change SDK/BOOT/CMA. Strict5Hz/103/long-term/HDMI pending.'}
(E/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Archived current completion and recovery point',sha(E/'completion-review.json'))
