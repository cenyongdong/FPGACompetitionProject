"""Archive lease/Host read validation and pre-forward directory timeout accurately."""
from pathlib import Path
import json,hashlib,ast,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r2';B=R/'.local/pose-v1-build/producer-source-read-20261011-r2';assert not (E/'completion-review.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text());m=load(B/'build-result.json');assert sha(B/'pose_producer_read_check')==m['program_sha256']
for p,h in m['sources'].items():assert sha(R/p)==h
base=load(R/'.local/pose-v1-read-phase/package-20261011-r3/manifest.json');frozen={p:v['sha256'] for p,v in base['build_files'].items() if p.startswith('software/')};assert len(frozen)==152
for p,h in frozen.items():assert sha(R/p)==h
for mode,count in [('four',4),('off',100)]:
    r=load(E/(mode+'.phase-review.json'));assert r['calls']==r['forward_calls']==count and r['FP32_values']==count*11760 and r['exit']==0
failure=load(E/'on.failure-review.json');assert failure['completed_correct']==failure['forward_calls']==49 and failure['late_source_read_calls']==0
assert failure['directory_span']['ms']==915.85662 and not failure['failed_slot_outputs_exist']
video=load(E/'on.video-review.json');assert video['decoded_images']==221 and video['copy_overlap_spans']==video['copy_spans_total']==98 and not video['normal_drain_LAST_pass']
final=load(E/'final-return/final/review.json');assert final['kernel_unchanged'] and final['pose_processes']==0 and final['test_ports_clear']
assert (E/'final-return/final/dmesg.txt').read_bytes()==(E/'on-return/run-on/after.dmesg.txt').read_bytes()
resource=load(E/'resources-return/resources-on/review.json');assert resource['writes']==0 and resource['before_units512KiB']==resource['after_units512KiB']==196
for mode,n in [('four',4),('off',100),('on',49)]:
    P=E/(mode+'-return/run-'+mode+'/results');leases=load(P/'lease-summary.json');assert leases['opened']==leases['closed']==n and leases['forced_expired']==leases['source_read_calls']==leases['failure_capture_calls']==0
    assert not (P/'lease-release.error.txt').exists() and load(P/'prefix-release.json')['after_prefix_drop_chunks']==load(P/'release.json')['remaining_sdk_chunks']==0
host=E/'host-return/run-host/read-host';refs=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns';host_bytes=0
for pattern in range(2):
    for round in range(2):
        for v in (4386,4390):
            p=host/(str(pattern)+'-'+str(round)+'-'+str(v)+'.f32');assert p.read_bytes()==(refs/('pattern-'+str(pattern))/('output-'+str(v)+'.f32')).read_bytes();host_bytes+=p.stat().st_size
assert host_bytes==188160
for n in ('build-result.json','symbols.txt','encoder-symbols.txt'):shutil.copyfile(B/n,E/n)
shutil.copyfile(B/'build.log',E/'build.txt');old=R/'.local/pose-v1-build/producer-source-read-20261011-r1';assert b'incomplete type' in (old/'build.log').read_bytes();shutil.copyfile(old/'build.log',E/'r1-build-failure.txt');shutil.copyfile(old/'source/producer_read_host_check.cpp',E/'r1-producer_read_host_check.cpp')
def insert(path,body):
    p=R/path;a,b=p.read_text(encoding='utf-8').split('\n',1);p.write_text(a+'\n\n'+body.strip()+'\n'+b,encoding='utf-8',newline='\n')
insert('Agents.md','''- 单调用输出租约本批结束（2026-10-11）：用户批准PRODUCER-ADDRESS-NEXT，ADR_43。r2 9772a0e1…30853b28，Native/ARM范围/代次/线程/寿命/拥有值/零正常读/诊断清理失败仍原错过，ARM Host CPTR8输出188160字节逐位，无物理Device/Session。新Opaque Scope保留真实outputs到compare结束，正常关闭，下次reset拒绝活租约，销毁Session前失效；失败四read/94080字节模块已构建，实际尚未触发。four4/off100/on前49合153前向1799280FP32及输入全逐位/有限/0→11，租约4/100/49开关相等、forced0/源读0。on计划inv49/B目录create915.85662ms CPU0.29944ms自愿切换2缺页0，随后Host/journal约0.92314ms；原绝对截止在reset/forward前拒绝exit1，保存B输入无outputs/trace/late-source/call50，未当on100通过或原DATA800修复。4842事件，阶段allocstall/reclaim/OOM/compact/pgmajfault全0；目录API内等待已定位但FS/存储/调度责任未证。225raw/224归还/222ownedpacket41056字节/221 NoInput解码ID0–220正确，1340Q/DQ两缓冲单线程/98copy全交叠非fence，尾四未解码/两abort STREAMOFF0/正常drain-LAST未过；join后Scope/Session毁/prefix1→0/allSDK0。资源只读普通512单位196→196（早off197），规整0/无清缓存重启CMABOOTSDK模型变化，最终733520/27876KiB仅快照，stage/final内核同/FPGA operating/本批程序管理器端口代理连接全闭。r1 Host缺Network头编译失败及误续审计衍生缺build-result保留，r2补头分开构建审计，无r1板测/失败Session重跑。原152软件/745/数学waitcopy保存/正式异常读回保持。ADR_43、PRODUCER-SOURCE-READ-RESULTS/NEXT、producer-source-read-20261011-r2 completion/next-checkpoint当前；下一放行前预建目录/有界一次令牌仅准备，不同时移动数据落盘，继续失败只读但不强行触发，根因/完整103/严格5Hz/长期/HDMI待，管理83/100保持。以下当前为历史。''')
insert('Done.md','''## 2026-10-11：单调用输出租约完成，目录等待阻断物理晚源读触发

### 工程内容总结

新增SDK无关租约Guard／原错保留助手及公开输出源封装，正常只延长真实Tensor句柄到原compare结束，闭合后再下一reset；Native／ARM范围、线程、代次、失效、拥有值、正常零读与异常传播过。ARM Host CPTR公开Tensor::read八输出188160字节逐位；r2程序9772a0e1…30853b28，四调用／off100／on前49合153实际前向1799280FP32全逐位、0→11，租约打开关闭一致、forced0、源读0。

VPU第50个计划时隙inv49，目录创建915.85662ms／CPU0.29944ms／自愿切换2，准备完成后的绝对截止在reset／forward前拒绝，未产生该次输出或晚源读；DATA800旧失配未复现，物理两轮read模块尚未触发，不当已验证。225raw／224归还、222packet41056字节／221 NoInput图像连续解码，98copy全交叠；两abort STREAMOFF成功、join后Scope／Session毁／prefix1→0／allSDK0，正常drain-LAST未过。

### 对后续开发的参考

目录API内等待已定位，FS／存储／调度责任未证；下一仅预先准备唯一空call目录，以有界内存令牌热路径领取，数据保存和比较仍在原位置，不同时改批尾落盘或增加截止。继续保留原错和失败只读，不强行制造失配。原152软件／模型／RAW／SDK／BOOT／745／正式异常读取保持，管理83/100及103／严格5Hz／长期／HDMI待。r1缺Network头和衍生审计错误保留，r2新目录补头、依赖操作分开，无硬件重跑。资源只读196单位、规整0／无清缓存重启／CMA变更，最终733520／27876KiB仅快照。所有本批程序／管理器／端口和代理连接结束，内核身份同。[结果](tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md)／[ADR_43](ADR/ADR_43.md)／[下一](tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-source-read-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md','''## 当前：源租约和Host read过，目录等待在前向前被截止门检拦截

四调用/off100/on前49共153前向1799280 FP32逐位，正常租约关闭／零源读；有VPUinv49目录创建915.86ms阻塞，绝对时隙在reset前拒绝，不产生错误输出、物理晚源read尚未触发。目录内部等待责任及原DATA800根因仍待。221 NoInput视频前缀和abort清理过，原152软件／模型SDKBOOT及异常读取保持。全部程序连接关闭，规整0；下一放行前空目录与有界领取令牌仅准备，数据仍原位保存。当前仍处首版闭环后并发可靠性定位，管理83/100保持（非通过率／工期），完整103／严格整机5Hz／长期／HDMI待。

[结果](tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md)／[ADR_43](ADR/ADR_43.md)／[下一](tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-source-read-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
for p in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(p,'2026-10-11最新：[ADR_43](ADR/ADR_43.md)记录源租约/Host188160字节read过、153前向正确、有VPUinv49目录等待915.86ms且准备截止成功拦截，物理晚源read未触发／根因未修；[结果](tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md)／[下一目录预备](tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-source-read-20261011-r2/next-checkpoint.json)。221 NoInput视频前缀/abort清理过，所有连接结束，原异常读取保持，下一未执行，以下当前为历史。')
insert('ADR/README.md','最新：[ADR_43](ADR_43.md)单调用租约与Host read过；有VPU目录等待在前向前超截止，物理两轮源read未触发，根因未修。[结果](../tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md)／[下一](../tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md)。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[单调用源租约结果](PRODUCER-SOURCE-READ-RESULTS-20261011.md)，Native/ARM/Host188160字节read过、153前向逐位；on计划inv49目录915.86ms被准备截止拦截，无forward或晚源读。221 NoInput视频前缀/abort释放过，原异常读取保持，所有连接结束。[ADR_43](../../ADR/ADR_43.md)／[下一目录预备](PRODUCER-SOURCE-READ-NEXT-20261011.md)／[恢复](evidence/producer-source-read-20261011-r2/next-checkpoint.json)。以下当前为历史。')
checkpoint={'active_work':False,'user_paused':False,'all_agent_programs_connections_closed':True,'services_running':False,'root_cause_resolved':False,
            'current_stage':'lease_verified_on_directory_deadline_before_forward_no_late_read','next_entry':'tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md',
            'next_implemented':False,'next':'prepare unique empty call directories before gate; bounded one-use directory tokens; retain original data writes and failure-only source reads',
            'physical_late_source_capture_verified':False,'no_hardware_retry':True,'preserve_original_failure_and_reads':True,'original_final_count':745,'independent_count':11,'management_estimate':83}
(E/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
names=('prepare_producer_read_tools.py','prepare_producer_read_r2.py','build_producer_read.py','build_producer_read_r2.py','board_producer_read_run.py',
       'execute_producer_read.py','execute_producer_read_r2.py','review_producer_read.py','review_producer_read_r2.py','review_producer_read_failure.py','review_producer_read_deadline.py',
       'review_producer_read_video.py','review_producer_read_abort_video.py','producer_read_resources.py','producer_read_resources_r2.py','prepare_producer_read_resources.py','prepare_producer_read_resources_r2.py',
       'board_producer_read_final.py','board_producer_read_final_r2.py','collect_producer_read_final.py','collect_producer_read_final_r2.py','audit_producer_read_api.py','audit_producer_read_api_r2.py',
       'archive_producer_source_read.py','ssh_memory_transport.py','archive_bytes.py')
tools=['tools/pose-v1/'+x for x in names]
for p in tools:ast.parse((R/p).read_text(encoding='utf-8-sig'))
docs=['Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/ADR_43.md','ADR/README.md','tools/pose-v1/README.md',
      'tools/pose-v1/PRODUCER-SOURCE-READ-RESULTS-20261011.md','tools/pose-v1/PRODUCER-SOURCE-READ-NEXT-20261011.md','.gitignore']
reviews=('host.review.json','api-audit.json','four.phase-review.json','off.phase-review.json','on.failure-review.json','on.phase-spans.json','on.video-review.json',
         'four.exit-review.json','off.exit-review.json','on.exit-review.json','four-deployment.review.json','off-deployment.review.json','on-deployment.review.json','resources-return/resources-on/review.json','final-return/final/review.json')
r={'status':checkpoint['current_stage'],'program_sha256':m['program_sha256'],'build_source_hashes':m['sources'],'frozen_software_hashes':frozen,'frozen_software_sources_unchanged':152,
   'tool_hashes':{p:sha(R/p) for p in tools},'forward_calls':153,'correct_FP32_values':1799280,'frame_reset1_calls':153,'Host_CPTR_read_bytes':188160,'Host_CPTR_outputs':8,
   'physical_late_source_capture_verified':False,'physical_source_read_calls':0,'lease_open_close_counts':[4,100,49],'forced_expired':0,
   'failed_planned_invocation':49,'failed_slot_forwarded':False,'directory_wait_ms':915.85662,'new_Host107_runs':0,'full_model_calls':0,
   'VPU_packets':222,'decoded_NoInput_images':221,'ioctl_records':1340,'copy_overlap_spans':98,'normal_drain_LAST_pass':False,'compactions':0,
   'BOOT_SDK_model_kernel_unchanged':True,'root_cause_resolved':False,'agent_programs_connections_closed':True,'management_estimate':83,
   'reviews':{p:sha(E/p) for p in reviews},'archives':{p.name:sha(p) for p in E.glob('*.tar')},'sdk_diff_sha256':sha(E/'sdk-lease.diff'),'app_diff_sha256':sha(E/'application-lease.diff'),
   'r1_missing_header_build_failure_log_sha256':sha(E/'r1-build-failure.txt'),'r1_no_board_execution':True,
   'documents':{p:sha(R/p) for p in docs},'checkpoint_sha256':sha(E/'next-checkpoint.json')}
(E/'completion-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('Archived source lease/153 correct, directory blocked beforeforward; physical late read NOT verified; SHA',sha(E/'completion-review.json'))
