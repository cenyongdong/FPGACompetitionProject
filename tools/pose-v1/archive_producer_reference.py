"""Bind RAW/math/mock evidence, retained failures and current recovery point."""
from pathlib import Path
import hashlib,json,ast,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-reference-20261011-r2'
assert not (E/'completion-review.json').exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=json.loads((E/'reference-review.json').read_text());replay=json.loads((E/'reference-replay.json').read_text());mock=json.loads((E/'mock.review.json').read_text());raw=json.loads((E/'raw.review.json').read_text())
assert reference['FP32_values_verified']==23520 and replay['replay_bitwise_equal'] and mock['exit']==0
baseline=json.loads((R/'tools/pose-v1/mixed-fusion-baseline.json').read_text());group=next(x for x in baseline['groups'] if x['effective_op_id']==9186)
assert group['members']==[8174,8507,8626,8627,8628,8629,8630,8631,8655,8656,8797,8798,8799,8800,8801,8802,9074,9126,9127]
assert mock['contract']['sync_start']==0 and mock['contract']['layers']==11
model_manifest=json.loads((R/'.local/pose-v1-read-phase/package-20261011-r3/manifest.json').read_text())
unchanged={p:v['sha256'] for p,v in model_manifest['build_files'].items() if p.startswith('software/')}
assert len(unchanged)>100,'Frozen software inventory must be nonempty'
for p,h in unchanged.items():assert sha(R/p)==h,('Frozen source changed',p)
for name,x in reference['models'].items():assert sha(E/'transfer/models'/name)==x['sha256']
build_raw=R/'.local/pose-v1-build/producer-raw-20261011-r2';build_mock=R/'.local/pose-v1-build/producer-mock-20261011-r1'
for build,program in ((build_raw,'pose_producer_raw_audit'),(build_mock,'pose_producer_mock_contract')):
    m=json.loads((build/'build-result.json').read_text());assert sha(build/program)==m['program_sha256']
    for p,h in m['sources'].items():assert sha(R/p)==h
assert json.loads((build_mock/'build-result.json').read_text())['libraries']['libicraft_zg330backend.so']==baseline['zg_library_sha256']
failed=R/'.local/pose-v1-build/producer-raw-20261011-r1'
shutil.copyfile(failed/'build.log',E/'build-failed-r1.txt');shutil.copyfile(failed/'source/producer_raw_audit.cpp',E/'producer-raw.failed-r1.cpp.txt')
for build,prefix in ((build_raw,'raw'),(build_mock,'mock')):
    shutil.copyfile(build/'build.log',E/(prefix+'-build.txt'));shutil.copyfile(build/'build-result.json',E/(prefix+'-build-result.json'))
mock_root=E/'mock-return/run-mock';raw_root=E/'raw-return/run-raw'
assert (raw_root/'dmesg.before.log').read_bytes()==(mock_root/'dmesg.after.log').read_bytes()
assert not (raw_root/'stderr.log').read_bytes() and not (mock_root/'stderr.log').read_bytes()
assert not any(x.split()[1].startswith('pose_') for x in (mock_root/'processes.txt').read_text().splitlines()[1:] if len(x.split())>1)
sdk=mock_root/'sdk-logs/logs/piw24'
shutil.copyfile(sdk/'piw24_zg330backend_0.log',E/'mock-deployment-main.txt')
(E/'mock-deployment-memopt.json').write_text(json.dumps(json.loads((sdk/'piw24_zg330backend_0_memopt.log').read_text()),indent=2)+'\n',encoding='utf-8',newline='\n')
def insert(path,body):
    p=R/path;s=p.read_text(encoding='utf-8');head,tail=s.split('\n',1);p.write_text(head+'\n\n'+body.strip()+'\n'+tail,encoding='utf-8',newline='\n')
insert('Agents.md','''- 真实融合组参考本轮完成（2026-10-11）：用户批准PRODUCER-CONTRACT-NEXT，新增ADR_38。沿既有manifest找到原adapted图，19个来源／Value／dtype全对应；XIR-only RAW检查器1c26d038…7bfb3af通过三原RAW的MD5，22项导出、6144指令字节，8507实际96字节42个FP16一＋6零，adapted逐位同／optimized42个FP32一。公开lazyFileOffset源字节核验，两FP16/TF32精确可表示图案23520FP32与标量地址／原Matmul逐位同、重放同，逻辑TF32数组不作物理19位编码或一般舍入证明。mock7cc0e0b6…c028884公开19成员view创建/apply过，有效组9185/sync0→11，边界400/17280/30240/16800、四非OCM／输出别名；两日志8016/655字节，模拟地址不作物理地址。mock有模拟Device/Session，无物理NPU或forward；正式9186/223→234/最终745、CPU/Gather/数学/桥/模型/RAW/SDK/BOOT保持，Host107引用旧批不新跑。r1 HardOp→bool编译失败，新r2 defined()修正，旧源码/日志保留；tar板钟警告保留不改钟。两阶段exit0/stderr空/跨阶段内核同，规整0，无VPU/TCP/重启/清缓存/CMA变化；程序/SSH/SCP结束，最终751576/21992KiB仅现场。当前PRODUCER-REFERENCE-RESULTS/NEXT、ADR_38及producer-reference-20261011-r2 completion/next-checkpoint。下一独立物理apply核对真实段／sync再固定A/B/A/B四调用，尚未物理候选/前向；原异常读取保留、根因未修、83/100/103/严格5Hz/长期/HDMI待。以下当前为历史。''')
insert('Done.md','''## 2026-10-11：原19成员真实参数、受限参考与模拟部署闭合

### 工程内容总结

根据既有manifest找到原adapted图，19来源、Value及dtype逐项对应硬化图。XIR-only检查器1c26d038…7bfb3af仅读三RAW并校验MD5，导出22项／6144指令字节；8507的96字节真实权重为42个FP16一＋6零，与adapted逐位一致，optimized权重为42个FP32一。未替换真实参数或猜文件偏移。

两种有限、FP16／TF32精确可表示图案按19成员真实属性生成完整参考，23520个FP32分别与独立标量地址遍历／原optimized Matmul逐位同，重放同。仅逻辑TF32值，不外推物理19位编码或通用舍入。mock7cc0e0b6…c028884通过原19成员公开view部署，生成有效9185/sync0→11，四边界非OCM，输出是中间层别名；两官方日志8016／655字节。mock创建模拟Device／Session，未打开物理NPU或调用forward。

### 对后续开发的参考

数学参考缺口已闭合，物理MMU／首次读完成仍待。正式模型223→234／最终745、原CPU／Gather／桥／模型／RAW／SDK／BOOT保持。下一独立物理apply核对真实范围，再固定A/B/A/B四调用、先保存后比较，不晚读修补或用首物理输出作金标准。r1句柄转bool编译失败由新r2 defined()修正，旧失败保留；无新Host107／NPU数值／VPU／并发验收。两阶段exit0／stderr空／内核跨阶段同、规整0／无配置变化／所有会话结束，最终751576／21992KiB仅现场。根因未修，83/100保持。[结果](tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md)／[ADR_38](ADR/ADR_38.md)／[下一](tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-reference-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md','''## 当前：真实19成员参考与mock范围已闭合，首次物理读取根因仍待

本轮完成原RAW公开仅读、实际权重／指令身份、adapted 19来源映射、两图案23520 FP32独立参考及重放；mock独立部署sync0→11过。无物理NPU forward／新视频／Host107或并发门检。下一先独立物理apply核对真实段，再固定四调用，保留原异常读取。项目仍处首版闭环后的高并发可靠性定位，管理83/100不变（主观工作包估计，非通过率／工期），103／严格5Hz／长期／HDMI待。规整0、内核同、程序和连接关闭。

[结果](tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md)／[ADR_38](ADR/ADR_38.md)／[下一](tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-reference-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
for p in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(p,'2026-10-11最新：[ADR_38](ADR/ADR_38.md)记录真实参数／19来源映射／受限FP16-TF32参考及mock独立0→11。数学参考已闭合，物理读取根因未修；[结果](tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md)／[下一](tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-reference-20261011-r2/next-checkpoint.json)。无新物理前向／并发通过，全部程序和连接结束，以下当前为历史。')
insert('ADR/README.md','最新：[ADR_38](ADR_38.md)原19成员真实RAW、受限独立参考与mock部署；23520 FP32参考和0→11模拟范围通过，物理NPU首次读未验证，根因未修。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[原生产者参考结果](PRODUCER-REFERENCE-RESULTS-20261011.md)：原RAW权重／指令与19来源闭合，两图案23520 FP32参考／重放通过，mock独立0→11部署通过；未物理forward／新并发验收。原异常读取保持。[ADR_38](../../ADR/ADR_38.md)／[下一物理门检](PRODUCER-REFERENCE-NEXT-20261011.md)／[恢复](evidence/producer-reference-20261011-r2/next-checkpoint.json)。以下当前为历史。')
scripts=['tools/pose-v1/'+n for n in ('build_producer_raw_audit.py','build_producer_raw_audit_r2.py','execute_producer_raw_audit.py','review_producer_reference.py','build_producer_mock_contract.py','execute_producer_mock_contract.py','archive_producer_reference.py','ssh_memory_transport.py','archive_bytes.py')]
for p in scripts:ast.parse((R/p).read_text(encoding='utf-8-sig'))
sources=scripts+['software/pose_v1/src/producer_raw_audit.cpp','software/pose_v1/src/producer_mock_contract.cpp','tools/pose-v1/run-producer-raw.sh','tools/pose-v1/run-producer-mock.sh']
docs=['Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/ADR_38.md','ADR/README.md','tools/pose-v1/README.md','tools/pose-v1/PRODUCER-REFERENCE-RESULTS-20261011.md','tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md','.gitignore']
checkpoint={'active_work':False,'user_paused':False,'all_programs_connections_closed':True,'services_running':False,'root_cause_resolved':False,'current_stage':'original_group_math_reference_and_mock_scope_complete','next_entry':'tools/pose-v1/PRODUCER-REFERENCE-NEXT-20261011.md','next':'prepare independent physical apply gate; verify actual segments and sync0→11 before fixed A/B/A/B; no physical candidate run yet','preserve_original_failure_and_reads':True,'reference_scope':'exactly representable synthetic FP16/TF32 patterns only','original_final_count':745,'mock_independent_count':11}
(E/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
report={'status':'real_RAW_reference_and_mock_scope_complete_physical_root_unresolved','programs':{'RAW':raw['program_sha256'],'mock':json.loads((build_mock/'build-result.json').read_text())['program_sha256']},'new_physical_forwards':0,'new_Host107_runs':0,'reference_FP32_values':23520,'replay_bitwise_equal':True,'kernel_unchanged':True,'compactions':0,'physical_device_opened':False,'mock_Device_and_Session_created':True,'root_cause_resolved':False,'frozen_software_sources_unchanged':len(unchanged),'frozen_software_hashes':unchanged,'reviews':{n:sha(E/n) for n in ('raw.review.json','reference-review.json','reference-replay.json','mock.review.json')},'archives':{n:sha(E/n) for n in ('transfer.tar','return-raw.tar','mock-transfer.tar','return-mock.tar')},'documents':{p:sha(R/p) for p in docs},'source_hashes':{p:sha(R/p) for p in sources},'retained_r1_source_sha256':sha(E/'producer-raw.failed-r1.cpp.txt'),'retained_r1_build_log_sha256':sha(E/'build-failed-r1.txt'),'checkpoint_sha256':sha(E/'next-checkpoint.json'),'management_estimate':83,'connections_closed':True}
(E/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Archived reference/mock stage, frozen software',len(unchanged),'SHA256',sha(E/'completion-review.json'))
