"""Bind completed phase experiment, preserved package failure and next diagnostic."""
from pathlib import Path
import ast,hashlib,json,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-phase-20261011-r2';B=R/'.local/pose-v1-build/producer-phase-20261011-r2'
assert not (E/'completion-review.json').exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
m=load(B/'build-result.json');assert sha(B/'pose_producer_phase_check')==m['program_sha256']
for name,h in m['sources'].items():assert sha(R/name)==h
base=load(R/'.local/pose-v1-read-phase/package-20261011-r3/manifest.json');frozen={p:x['sha256'] for p,x in base['build_files'].items() if p.startswith('software/')};assert len(frozen)==152
for name,h in frozen.items():assert sha(R/name)==h
for mode in ('off','on'):
    r=load(E/(mode+'.phase-review.json'));assert r['calls']==r['forward_calls']==r['reset_calls']==100 and r['FP32_values']==1176000 and r['exit']==0
    P=E/(mode+'-return/run-'+mode+'/results');ev=[json.loads(x) for x in (P/'phases.jsonl').read_text().splitlines()];assert len(ev)==9800
    for i in range(100):
        identity=load(P/('call-'+str(i))/'identity.json');ends=[x for x in ev if x['invocation']==i and x['edge']=='end' and x['phase'] in ('deadline','end_check')]
        assert len(ends)==2 and all(identity['planned_ns']<=x['wall_ns']<identity['planned_ns']+198019801 for x in ends)
video=load(E/'on.video-review.json');assert video['decoded_images']==307 and video['normal_drain_LAST'] and video['copy_overlap_spans']==200
final=load(E/'final-return/final/review.json');assert final['kernel_unchanged'] and final['test_ports_clear'] and final['pose_processes']==0
assert (E/'final-return/final/dmesg.txt').read_bytes()==(E/'on-return/run-on/after.dmesg.txt').read_bytes()
resource=load(E/'resources-return/resources-on/review.json');assert resource['writes']==1 and resource['elapsed_ns']==326368280
for name in ('build-result.json','symbols.txt','encoder-symbols.txt'):shutil.copyfile(B/name,E/name)
shutil.copyfile(B/'build.log',E/'build.txt')
failed=R/'tools/pose-v1/evidence/producer-phase-20261011-r1';assert b"can't open file 'board_producer_phase_run.py'" in (failed/'host-transport-3.txt').read_bytes()

def insert(path,body):
    p=R/path;a,b=p.read_text(encoding='utf-8').split('\n',1);p.write_text(a+'\n\n'+body.strip()+'\n'+b,encoding='utf-8',newline='\n')
insert('Agents.md','''- reset前分段及绝对时隙本批完成（2026-10-11）：用户批准PRODUCER-VPU-NEXT，ADR_41。同b81835cd…3c9e06f，新Trace有界16384／每阶段9800，Native／ARM载荷9拒绝、时隙／ioctl及容量线程异常返回值／迟到不前向合同过。SDK诊断副本仅观察＋reset前原绝对截止，原152冻结软件／producer_sdk／VPU源码／数学／等待／复制／数据保存位置／异常读取及SDK模型RAWBOOT保持。off100/on100共2352000FP32及输入全逐位／有限／0→11，准备结束与最终绝对时隙独立核验过，exit0/stderr空，旧1763ms尖峰及正式192坏读未复现未修；物理迟到拒绝未触发。最长leaf为输入486保存off46.84692ms CPU0.20014ms自愿切换1/on42.52643ms CPU0.33235ms自愿切换2、缺页0，区间等待已观测但IO/存储/调度根因未证；on Host分配0.06657/write0.03287/journal flush0.07562ms，forward最大3.72188ms CPU0.34671ms切换1非纯NPU。307raw提交归还、309ownedpacket56763字节含头及空LAST、307解码ID0–306/NoInput正确，1844公开Q/DQ单线程fd6/type10/9各2，200copy全交叠提交capture跨度非fence，正常drain-LAST/两STREAMOFF/join后SDK毁块0过，无新姿态吞吐／完整Engine／Host107／TCP/HDMI。一次自主规整326.36828ms普通512单位2→149，无清缓存/重启/CMABOOT变；最终694424/1864KiB仅快照，BOOTSDK模型内核同/FPGA operating/本批程序管理器端口代理连接全结束。r1打包旧管理器名错误在合同/Device前停止保留，r2新包复用同ELF修正并ARM过，非失败Session重跑。ADR_41、PRODUCER-PHASE-RESULTS/NEXT、producer-phase-20261011-r2 completion/next-checkpoint当前；下一公开SDK高地址布局可行性仅准备，不能猜地址或与保存优化同时改动。原异常读取／745保持，管理83/100／完整103／严格整机5Hz／长期／HDMI待。以下当前为历史。''')
insert('Done.md','''## 2026-10-11：reset前分段观察及无／有VPU各100调用通过

### 工程内容总结

新增SDK无关有界Trace和隔离SDK诊断副本，在保留原数据保存位置、数学／等待／复制的同时记录单steady_clock、线程CPU、缺页与切换计数，准备完成后按原planned绝对截止检查。Native／ARM容量／线程／异常／返回值／时隙边界合同过；每阶段9800事件，结束后落盘。原152冻结软件、模型／RAW／SDK／BOOT及异常读取保持。同b81835cd…3c9e06f程序，off100／on100共200调用2352000FP32和输入全逐位独立参考／有限，每次0→11，准备及最终时隙独立核验过，exit0／stderr空。

最长保存区间off46.84692ms／CPU0.20014ms、on42.52643ms／CPU0.33235ms，有自愿切换且缺页0；本轮存在保存区间等待，但旧1.764秒尖峰未复现，不能归因已证存储或调度。VPU307提交／归还、309packet含头及空LAST／56763字节，307 NoInput图像ID0–306完整解码；1844 ioctl和200次copy全交叠，正常drain／LAST／两STREAMOFF及join后SDK毁块0过，不计新姿态吞吐。

### 对后续开发的参考

正式高并发坏读根因未修，本批低地址19成员不是完整Engine／103／整机5Hz或长期通过，管理83/100保持。下一先公开SDK高地址前缀所有权／容量／释放可行性，不能猜物理地址，不与保存I/O优化同时改变变量。r1管理器文件名打包错误在Device前停止保留，r2复用同ELF的新包／新目录修正。自主规整一次326.36828ms、普通512单位2→149，无清缓存／重启／CMA变更；最终694424／1864KiB仅快照。BOOT／SDK／模型／内核同、全部程序／管理器／端口及代理连接结束。[结果](tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md)／[ADR_41](ADR/ADR_41.md)／[下一](tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-phase-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md','''## 当前：reset前已分段，无／有VPU各100过，正式高地址坏读仍待定位

200独立19成员调用／2352000 FP32及输入全逐位、0→11／绝对时隙过；307 NoInput图像与正常drain-LAST、资源释放过。旧1.764秒尖峰未复现，输入保存区间46／42ms等待有观测但底层责任未证；正式坏索引未修。原152软件及模型SDKBOOT保持，原异常读取保留。下一公开SDK高地址布局可行性仅准备，不猜映射或同时改保存策略。仍处首版闭环后的并发可靠性定位，管理83/100不变（非通过率／工期），完整103／严格整机5Hz／长期／HDMI待；一次有记录规整，所有本批程序／连接结束。

[结果](tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md)／[ADR_41](ADR/ADR_41.md)／[下一](tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-phase-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
for path in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(path,'2026-10-11最新：[ADR_41](ADR/ADR_41.md)归档reset前分段／准备后绝对时隙、off/on各100及307 NoInput视频正常回收。2352000 FP32逐位，旧1.764秒尖峰未复现，保存区间等待已观察但底层原因未证，正式坏读未修；[结果](tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md)／[下一公开高地址可行性](tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-phase-20261011-r2/next-checkpoint.json)。原异常读取保持、下一未执行、程序连接全结束，以下当前为历史。')
insert('ADR/README.md','最新：[ADR_41](ADR_41.md)reset前分段与绝对时隙，off/on各100／2352000 FP32及307 NoInput视频通过，旧尖峰未复现、正式坏读未修；[结果](../tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md)／[下一](../tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md)。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[reset前分段结果](PRODUCER-PHASE-RESULTS-20261011.md)，off/on各100／2352000FP32及307 NoInput视频正常drain过，旧尖峰未复现、正式坏读未修。保存区间等待不能自动归因底层，原异常读取保持。[ADR_41](../../ADR/ADR_41.md)／[下一](PRODUCER-PHASE-NEXT-20261011.md)／[恢复](evidence/producer-phase-20261011-r2/next-checkpoint.json)。全部本批程序连接结束，以下当前为历史。')
checkpoint={'active_work':False,'user_paused':False,'all_agent_programs_connections_closed':True,'services_running':False,'root_cause_resolved':False,
            'current_stage':'phase_off100_on100_complete_formal_fault_unresolved','next_entry':'tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md',
            'next_implemented':False,'next':'public ARM SDK region capacity/managed prefix ownership feasibility, then controlled higher address group only after review',
            'preserve_original_failure_and_reads':True,'original_final_count':745,'independent_count':11,'management_estimate':83}
(E/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
names=('prepare_producer_phase_sources.py','prepare_producer_phase_tools.py','build_producer_phase.py','board_producer_phase_run.py',
       'execute_producer_phase.py','execute_producer_phase_r2.py','prepare_producer_phase_r2_package.py',
       'review_producer_phase_events.py','review_producer_phase_events_r2.py','review_producer_phase_video.py',
       'producer_phase_resources.py','prepare_producer_phase_resources.py','board_producer_phase_final.py','collect_producer_phase_final.py',
       'archive_producer_phase.py','ssh_memory_transport.py','archive_bytes.py')
tools=['tools/pose-v1/'+x for x in names]
for p in tools:ast.parse((R/p).read_text(encoding='utf-8-sig'))
docs=['Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/ADR_41.md','ADR/README.md',
      'tools/pose-v1/README.md','tools/pose-v1/PRODUCER-PHASE-RESULTS-20261011.md','tools/pose-v1/PRODUCER-PHASE-NEXT-20261011.md','.gitignore']
reviews=('host.review.json','off.phase-review.json','on.phase-review.json','on.video-review.json','off.exit-review.json','on.exit-review.json',
         'off-deployment.review.json','on-deployment.review.json','resources-return/resources-on/review.json','final-return/final/review.json')
r={'status':checkpoint['current_stage'],'program_sha256':m['program_sha256'],'build_source_hashes':m['sources'],'frozen_software_hashes':frozen,
   'frozen_software_sources_unchanged':152,'source_count':len(m['sources']),'tool_hashes':{p:sha(R/p) for p in tools},
   'off_completed':100,'on_completed':100,'FP32_values_verified':2352000,'frame_reset1_calls':200,'full_model_calls':0,'new_Host107_runs':0,
   'phase_events_per_stage':9800,'physical_late_preparation_rejection_triggered':False,'normal_drain_LAST_pass':True,
   'VPU_packets':309,'decoded_NoInput_images':307,'copy_overlap_spans':200,'ioctl_records':1844,
   'compactions':1,'compaction_elapsed_ns':326368280,'BOOT_SDK_model_kernel_unchanged':True,'root_cause_resolved':False,
   'agent_programs_connections_closed':True,'management_estimate':83,'reviews':{p:sha(E/p) for p in reviews},
   'archives':{p.name:sha(p) for p in E.glob('*.tar')},'sdk_adaptation_diff_sha256':sha(E/'sdk-adaptation.diff'),
   'r1_retained_package_failure':{'archive_sha256':sha(failed/'transfer.tar'),'failure_log_sha256':sha(failed/'host-transport-3.txt'),'no_device_initialization':True,'same_ELF_r2':True},
   'documents':{p:sha(R/p) for p in docs},'checkpoint_sha256':sha(E/'next-checkpoint.json')}
(E/'completion-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('Archived200/2352000 values, frozen152, completionSHA',sha(E/'completion-review.json'))
