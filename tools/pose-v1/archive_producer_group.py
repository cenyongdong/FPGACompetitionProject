"""Archive independent group results, exact limitations and resumable next gate."""
from pathlib import Path
import json,hashlib,ast,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-group-20261011-r2';old=R/'tools/pose-v1/evidence/producer-group-20261011-r1'
assert not (E/'completion-review.json').exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((E/'data-review.json').read_text());final=json.loads((E/'final-r2-review.json').read_text());assert data['FP32_values']==47040 and final['kernel_unchanged'] and final['owned_manager_and_programs_ended']
b=R/'.local/pose-v1-build/producer-group-20261011-r2';build=json.loads((b/'build-result.json').read_text())
for p,h in build['sources'].items():assert sha(R/p)==h
assert sha(b/'pose_producer_group_check')==build['program_sha256']
base=json.loads((R/'.local/pose-v1-read-phase/package-20261011-r3/manifest.json').read_text())
frozen={p:v['sha256'] for p,v in base['build_files'].items() if p.startswith('software/')};assert len(frozen)==152
for p,h in frozen.items():assert sha(R/p)==h
shutil.copyfile(b/'build-result.json',E/'build-result.json');shutil.copyfile(b/'build.log',E/'build.txt')
before=(E/'physical-return/run-physical/after.dmesg.txt').read_bytes();first=(E/'final-return/final/dmesg.txt').read_bytes();last=(E/'final-r2-return/final-r2/dmesg.txt').read_bytes()
assert before!=first and before==last
assert first.replace(b'\\xc2\\xa9',b'\xc2\xa9')==before
(E/'final-locale-review.json').write_text(json.dumps({'status':'old_boot_copyright_rendering_only','initial_byte_equal':False,'initial_retained_archive_sha256':sha(E/'return-final.tar'),'UTF8_new_readonly_capture_byte_equal':True,'physical_rerun':False},indent=2)+'\n')
assert json.loads((old/'mock.exit-review.json').read_text())['exit']==1
for log in ('piw24_zg330backend_0.log','piw24_zg330backend_0_memopt.log'):
    p=E/'physical-return/run-physical/work/.icraft/logs/piw24'/log
    if p.exists():shutil.copyfile(p,E/('physical-'+log.replace('.log','.txt')))
def insert(path,body):
    p=R/path;s=p.read_text(encoding='utf-8');a,b=s.split('\n',1);p.write_text(a+'\n\n'+body.strip()+'\n'+b,encoding='utf-8',newline='\n')
insert('Agents.md','''- 独立19成员真实生产者本批完成（2026-10-11）：用户批准PRODUCER-REFERENCE-NEXT，新增ADR_39。r1 4a6a7251…a8da0494载荷ARM/9拒绝过，但mock第一输入返回全零99差异exit1；板端/FPAI mock库d6606416…1557776的PLDDR读写各ret，能力假设错误，不是正式坏索引证据，未物理NPU/重跑。新r2 0183e2a0…d17d7d5六匹配头/四SDK库/152冻结软件不变；Native/ARM载荷拥有值/9拒绝、mock部署及35360字节HostCPTR过。真实apply原19→9185/sync0→11，四边界非OCM、两输出61440/40960属SDK chunk/8467/8479别名；独立临时PLDDR35360字节往返在前向前逐位，代理核对后同Session固定A/B/A/B四调用，保存后比较47040FP32全有限/逐位/A≠B/重复同、每次0→11，SDK块释放0。单钟forward196.88–461.61μs/copy55.75–145.73μs仅四次局部跨度，不作纯NPU或性能；首reset至末拥有约10.04ms/管理器9.16秒不混。原CPU/Gather/桥/模型/RAW/SDK/BOOT/CMA、745及异常读取保持，无VPU/显示/TCP/新Host107/规整/清缓存/重启，仅4次帧reset(1)。只读收尾C locale旧启动©转义原字节差异保留，新UTF8只读与物理阶段逐位同，未硬件重跑；最终BOOT/SDK/内核同/FPGA operating/程序管理器结束/代理SSH/SCP闭，750384/26472KiB仅现场。当前PRODUCER-GROUP-RESULTS/NEXT、ADR_39及producer-group-20261011-r2 completion/next-checkpoint。低地址无视频四调用未复现正式并发，根因未修，83/100/103/严格5Hz/长期/HDMI待。下一同身份无/有VPU各固定100次5.05Hz有界对照仅方案准备，未接入/运行，原异常读取不删。以下当前为历史。''')
insert('Done.md','''## 2026-10-11：独立真实19成员部署、内存与四调用通过

### 工程内容总结

新增隔离载荷／SDK适配／编排目标，保持原152冻结软件、CPU／Gather／桥／模型／RAW／SDK／BOOT。r2程序0183e2a0…d17d7d5，六匹配头／四库；Native与ARM两图案、拥有值、9拒绝通过。r1把mock当数据存储的假设导致全零／99差异exit1保留，匹配板端/FPAI mock读写ret证实不支持搬运；新r2采用Host CPTR契约、mock部署及真实SDK自有临时区前置门检，两种实际往返各35360字节通过，不改SDK或吞错。

真实公开apply保持原19成员、唯一ZG组9185／sync0→11，四边界非OCM且范围属于SDK chunk，两输出61440／40960为8467／8479别名。代理回传核对后，在同一Session放行固定A/B/A/B四调用；全部两个实际输出保存后比较，47040 FP32与独立参考逐位／有限，交替不同、重复同，每次0→11。释放后SDK块0。forward196.88–461.61μs与copy55.75–145.73μs仅四次局部跨度，不计纯NPU或整机性能。

### 对后续开发的参考

低地址无VPU的独立生产者可正确运行，尚未复现正式并发坏片段。下一准备同身份有／无VPU固定100次诊断，保留源、同步、整数／有限门禁与原异常读取，不晚读修补。原745和CPU分工保持；本批无完整模型／新Host107／视频／HDMI／RTSP或规整，管理83/100保持。只读收尾初次旧启动©的locale转义差异保留，新UTF8采集逐位同；BOOT／SDK／内核同、FPGA operating、所有本批程序／管理器及代理连接结束，最终750384／26472KiB仅快照。[结果](tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md)／[ADR_39](ADR/ADR_39.md)／[下一](tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-group-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md','''## 当前：独立真实19成员四调用过，正式高并发首次读根因未修

真实部署、独立临时PLDDR往返及同Session固定A/B/A/B通过，47040 FP32逐位参考、0→11与释放正确。mock不支持搬运的r1失败已查明，r2使用Host CPTR／真实内存前置门检，不把mock当物理证据。原152冻结软件、模型、SDK与BOOT不变，未新完整模型／VPU／Host107或长期门检。下一有／无VPU各固定100调用方案仅准备，原异常读取保持。仍处首版闭环后的高并发可靠性定位，主观管理估计83/100不变，不是通过率／工期；103／严格5Hz／长期／HDMI待验。本批代理程序／管理器／连接结束，规整0，内核同。

[结果](tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md)／[ADR_39](ADR/ADR_39.md)／[下一](tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-group-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
for p in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(p,'2026-10-11最新：[ADR_39](ADR/ADR_39.md)记录独立19成员物理部署／四调用、mock无数据搬运的门检修正与locale只读核验。47040 FP32／0→11／释放通过，正式并发根因未修；[结果](tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md)／[下一有无VPU对照](tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-group-20261011-r2/next-checkpoint.json)。100调用未实施，原异常读取保持，以下当前为历史。')
insert('ADR/README.md','最新：[ADR_39](ADR_39.md)独立真实19成员四调用：47040 FP32逐位／0→11／SDK块释放通过；mock能力假设以Host CPTR和真实临时区门检修正，旧失败保留，正式并发根因未修。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[独立生产者结果](PRODUCER-GROUP-RESULTS-20261011.md)，原19成员真实部署／内存／同Session四调用47040 FP32通过。mock只有分配、读写ret，原失败保留；r2 Host CPTR及真实临时区前置门检通过。正式并发根因未修，原异常读取保持；[ADR_39](../../ADR/ADR_39.md)／[下一有无VPU对照](PRODUCER-GROUP-NEXT-20261011.md)／[恢复](evidence/producer-group-20261011-r2/next-checkpoint.json)。以下当前为历史。')
checkpoint={'active_work':False,'user_paused':False,'all_agent_programs_connections_closed':True,'services_running':False,'root_cause_resolved':False,'current_stage':'independent_physical_four_calls_complete','next_entry':'tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md','next':'prepare same identity off/on VPU bounded 100 alternating calls; not implemented yet','preserve_original_failure_and_reads':True,'original_final_count':745,'independent_count':11,'scope':'low PL addresses, no video, exact synthetic patterns','management_estimate':83}
(E/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
tools=['tools/pose-v1/'+n for n in ('build_producer_group.py','build_producer_group_r2.py','board_producer_run.py','execute_producer_group.py','execute_producer_group_r2.py','review_producer_group.py','audit_mock_memory.py','final_producer_group_audit.py','final_producer_group_audit_r2.py','archive_producer_group.py','ssh_memory_transport.py')]
for p in tools:ast.parse((R/p).read_text(encoding='utf-8-sig'))
docs=['Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/ADR_39.md','ADR/README.md','tools/pose-v1/README.md','tools/pose-v1/PRODUCER-GROUP-RESULTS-20261011.md','tools/pose-v1/PRODUCER-GROUP-NEXT-20261011.md','.gitignore']
report={'status':'independent_physical_group_four_calls_passed_formal_root_unresolved','program_sha256':build['program_sha256'],'build_source_hashes':build['sources'],'tool_hashes':{p:sha(R/p) for p in tools},'frozen_software_sources_unchanged':len(frozen),'frozen_software_hashes':frozen,'new_NPU_calls':4,'full_model_calls':0,'FP32_values':47040,'physical_memory_roundtrip_bytes':35360,'HostCPTR_roundtrip_bytes':35360,'new_Host107_runs':0,'VPU_used':False,'compactions':0,'frame_reset1_calls':4,'root_cause_resolved':False,'kernel_final_byte_equal':True,'BOOT_SDK_unchanged':True,'agent_processes_connections_closed':True,'management_estimate':83,'reviews':{n:sha(E/n) for n in ('mock.review.json','deployment.review.json','physical.exit-review.json','data-review.json','final-r2-review.json','final-locale-review.json')},'archives':{n:sha(E/n) for n in ('transfer.tar','return-mock.tar','return-physical.tar','return-final.tar','return-final-r2.tar')},'retained_r1_failure':{'archive_sha256':sha(old/'return-mock.tar'),'mock_library_sha256':json.loads((old/'mock-driver-audit/review.json').read_text())['library_sha256'],'program_sha256':json.loads((R/'.local/pose-v1-build/producer-group-20261011-r1/build-result.json').read_text())['program_sha256']},'documents':{p:sha(R/p) for p in docs},'checkpoint_sha256':sha(E/'next-checkpoint.json')}
(E/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Archived four calls, frozen152, SHA256',sha(E/'completion-review.json'))
