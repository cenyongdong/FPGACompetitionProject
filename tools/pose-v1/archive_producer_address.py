"""Archive high-band reduced data failure without hardware retry or repaired outputs."""
from pathlib import Path
import ast,hashlib,json,shutil
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-address-20261011-r2';B=R/'.local/pose-v1-build/producer-address-20261011-r2';assert not (E/'completion-review.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text());m=load(B/'build-result.json')
assert sha(B/'pose_producer_high_check')==m['program_sha256']
for p,h in m['sources'].items():assert sha(R/p)==h
base=load(R/'.local/pose-v1-read-phase/package-20261011-r3/manifest.json');frozen={p:v['sha256'] for p,v in base['build_files'].items() if p.startswith('software/')};assert len(frozen)==152
for p,h in frozen.items():assert sha(R/p)==h
for mode,count in [('four',4),('off',100)]:
    r=load(E/(mode+'.phase-review.json'));assert r['calls']==r['forward_calls']==count and r['FP32_values']==count*11760 and r['exit']==0
failure=load(E/'on.failure-review.json');assert failure['completed_correct']==49 and failure['forward_calls']==50 and failure['outputs']['4386']['changed_count']==800 and failure['outputs']['4390']['changed_count']==0
video=load(E/'on.video-review.json');assert video['decoded_images']==214 and video['copy_overlap_spans']==100 and not video['normal_drain_LAST_pass']
final=load(E/'final-return/final/review.json');assert final['kernel_unchanged'] and final['test_ports_clear'] and final['pose_processes']==0
assert (E/'final-return/final/dmesg.txt').read_bytes()==(E/'on-return/run-on/after.dmesg.txt').read_bytes()
resource=load(E/'resources-return/resources-on/review.json');assert resource['writes']==0 and resource['before_units512KiB']==resource['after_units512KiB']==254
for mode in ('four','off','on'):
    P=E/(mode+'-return/run-'+mode+'/results');assert load(P/'prefix-release.json')['after_prefix_drop_chunks']==load(P/'release.json')['remaining_sdk_chunks']==0
    assert not (P/'prefix-release.error.txt').exists()
for name in ('build-result.json','symbols.txt','encoder-symbols.txt'):shutil.copyfile(B/name,E/name)
shutil.copyfile(B/'build.log',E/'build.txt')
old=R/'.local/pose-v1-build/producer-address-20261011-r1';shutil.copyfile(old/'build-result.json',E/'r1-unexecuted-build.json');shutil.copyfile(old/'build.log',E/'r1-unexecuted-build.txt')
shutil.copyfile(old/'source/producer_high_sdk.cpp',E/'r1-unexecuted-producer_high_sdk.cpp')
def insert(path,body):
    p=R/path;a,b=p.read_text(encoding='utf-8').split('\n',1);p.write_text(a+'\n\n'+body.strip()+'\n'+b,encoding='utf-8',newline='\n')
insert('Agents.md','''- 独立高地址生产者本批结束（2026-10-11）：用户批准PRODUCER-PHASE-NEXT，ADR_42。复用匹配ARM分配链并核当前三头／XRTAXI身份，Native/ARM地址12拒绝、载荷9、Trace/时隙/ioctl过。r2 745a6aae…b0e9e3f，104MiB自动SDK前缀4096起/auto_free/4096对齐无读写，9块非重叠，输入109088768/109068288、输出109113344/109092864非OCM/owner/尺寸/别名正确，在104–105MiB带非正式精确布局。每Session放行前真实往返/部署核验；四调用47040＋off100 1176000＋on前49 576240全逐位/有限，合153完整1799280值。on第50次inv49/B两输出保存后数值exit1，call50不存在；4386 DATA800有限值全部逐位同inv48/A同偏移，31段12×64＋19×128字节/起点64对齐，4390 INDEX4200全正确，输入全B/0→11/source_ready真/地址身份稳，forward431.12μs/copy156.82及88.21μs无尖峰。既非候选微误差也未证明缓存或NPU责任，首次复制拥有值已错；隔离源局部句柄已结束，没有晚源read，不重开追读，原正式异常读取冻结保持。1282 Q/DQ单线程fd6/两端2，100copy全交叠非fence；216raw/215归还/215ownedpacket40561字节/214 NoInput解码ID0–213前缀正确，尾两未解码，两abort STREAMOFF0/join后Session毁/prefix1→0/allSDK0，正常drain-LAST未过，summary0不是实际无工作。资源只读254→254，规整0/无清缓存重启/CMABOOTSDK模型变化；stage/final内核同/FPGA operating/本批程序管理器端口代理连接全结束，最终694740/2024KiB仅快照。r1只编译未上传，r2加强异常Device存活期前缀销毁；本机失败审查事件数4898→4896修正不改程序/数据不重跑。原152软件/745/数学/wait/copy/保存保持，管理83/100/完整103/严格5Hz/长期/HDMI待。ADR_42、PRODUCER-ADDRESS-RESULTS/NEXT、producer-address-20261011-r2 completion/next-checkpoint当前；下一单调用公开源租约＋失败两轮Tensor::read仅准备，无新源读取、无读晚值修补。以下当前为历史。''')
insert('Done.md','''## 2026-10-11：高地址独立组缩小到有限前帧数据复用失配

### 工程内容总结

匹配ARM三头及XRT／AXI分配链身份核验，新增SDK无关地址合同与独立前缀所有权模块，Native／ARM12拒绝、载荷9、Trace／时隙／ioctl通过。r2程序745a6aae…b0e9e3f通过SDK自动保留104MiB前缀、不读写或指定地址，实际两输出109113344／109092864、9chunk归属非重叠／原别名／非OCM正确。原152冻结软件／数学／模型／RAW／SDK／BOOT保持。每阶段部署和真实往返回传后放行；四调用与无VPU100通过，有VPU前49通过，合153完整正确1799280FP32。

有VPU第50次inv49/B完整保存两输出后失配exit1，DATA4386的800有限值逐位同前帧A同位置，31段64／128字节对齐区间；INDEX4390全正确，输入全B、0→11、元数据稳，无1.764秒尖峰。失配源句柄已结束，本批未晚源read或重开设备；更小场景不需完整CPU／多组／网络即可出现，但生产／写入／DMA／缓存／Host责任未证。214 NoInput图像／215ownedpacket前缀解码正确，100copy全交叠，正常drain-LAST未过；两abort STREAMOFF、join后Session毁／prefix1→0／所有块0通过。

### 对后续开发的参考

下一新身份采用单调用公开输出证据租约，只在原比较失败后、源和Session有效时两轮Tensor::read，完整保存首次和晚值、重抛原错；不猜缓存修正，不读晚值填回，不重跑本批失败Session。r1只编译未上传，r2加强异常释放顺序；本机事件数审查修正4896保留，程序／数据不改。资源只读普通512单位254，本批规整0／无清缓存重启或CMA改变；BOOTSDK模型内核同、全部本批程序／管理器／端口及代理连接结束，最终694740／2024KiB仅快照。原正式异常读取／745保留，管理83/100，完整103／严格整机5Hz／长期／HDMI待。[结果](tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md)／[ADR_42](ADR/ADR_42.md)／[下一](tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-address-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md','''## 当前：高地址独立组＋VPU发生前帧数据复用，已获得更小失配场景

高地址四调用／off100／on前49共153完整1799280FP32正确，第50次DATA800有限值逐位同前帧A，INDEX正确、首次拥有输出已错、输入／计数／身份正常；尚无晚源证据，SDK/NPU/DMA/cache责任未证。不能以此称复现了原192索引错完全相同机制。214 NoInput视频前缀／异常清理过，正常drain-LAST未过；原152软件、模型SDKBOOT和异常读取保持，资源只读／规整0，程序连接全结束。下一单调用源租约及失败两轮只读证据仅准备。当前仍是首版闭环后的并发可靠性定位，管理83/100不变（非通过率／工期），完整103／严格5Hz／长期／HDMI待。

[结果](tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md)／[ADR_42](ADR/ADR_42.md)／[下一](tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-address-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
for path in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(path,'2026-10-11最新：[ADR_42](ADR/ADR_42.md)记录高地址SDK前缀控制、四调用/off100通过、on inv49 DATA800逐位前帧A的独立更小失配；首次输出已错但无晚源证据，责任未证。214 NoInput视频前缀/abort清理过，全部连接结束；[结果](tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md)／[下一失败只读租约](tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-address-20261011-r2/next-checkpoint.json)。下一未执行、原正式异常读取保留，以下当前为历史。')
insert('ADR/README.md','最新：[ADR_42](ADR_42.md)公开SDK高地址独立组：四调用/off100通过，有VPUinv49首次DATA800逐位前帧，INDEX正确，责任未证；[结果](../tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md)／[下一](../tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md)。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[高地址独立组结果](PRODUCER-ADDRESS-RESULTS-20261011.md)，four/off100及on前49正确，inv49 DATA800逐位前帧A、INDEX正确，首次拥有值已错，晚源尚未读取。214 NoInput视频前缀/abort清理过，所有连接结束；[ADR_42](../../ADR/ADR_42.md)／[下一](PRODUCER-ADDRESS-NEXT-20261011.md)／[恢复](evidence/producer-address-20261011-r2/next-checkpoint.json)。原异常读取保持、责任未证，以下当前为历史。')
checkpoint={'active_work':False,'user_paused':False,'all_agent_programs_connections_closed':True,'services_running':False,'root_cause_resolved':False,
            'current_stage':'high_address_on_inv49_finite_stale_DATA_failure_archived','next_entry':'tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md',
            'next_implemented':False,'next':'single-call public Tensor output evidence lease; failure-only two owned Tensor::read snapshots; preserve original error',
            'no_failed_hardware_retry':True,'preserve_original_failure_and_reads':True,'original_final_count':745,'independent_count':11,'management_estimate':83}
(E/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
names=('prepare_producer_address.py','prepare_producer_address_r2.py','build_producer_address.py','build_producer_address_r2.py','audit_producer_address_api.py',
       'board_producer_address_run.py','execute_producer_address.py','execute_producer_address_r2.py','review_producer_address.py','review_producer_address_r2.py',
       'review_producer_address_failure.py','review_producer_address_video.py','review_producer_address_abort_video.py',
       'producer_address_resources.py','prepare_producer_address_resources.py','board_producer_address_final.py','collect_producer_address_final.py',
       'archive_producer_address.py','ssh_memory_transport.py','archive_bytes.py')
tools=['tools/pose-v1/'+x for x in names]
for p in tools:ast.parse((R/p).read_text(encoding='utf-8-sig'))
docs=['Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/ADR_42.md','ADR/README.md','tools/pose-v1/README.md',
      'tools/pose-v1/PRODUCER-ADDRESS-RESULTS-20261011.md','tools/pose-v1/PRODUCER-ADDRESS-NEXT-20261011.md','.gitignore']
reviews=('host.review.json','api-audit.json','four.phase-review.json','off.phase-review.json','on.failure-review.json','on.phase-spans.json','on.video-review.json',
         'four.exit-review.json','off.exit-review.json','on.exit-review.json','four-deployment.review.json','off-deployment.review.json','on-deployment.review.json',
         'resources-return/resources-on/review.json','final-return/final/review.json')
report={'status':checkpoint['current_stage'],'program_sha256':m['program_sha256'],'build_source_hashes':m['sources'],'frozen_software_hashes':frozen,
        'frozen_software_sources_unchanged':152,'tool_hashes':{p:sha(R/p) for p in tools},'correct_calls':153,'forward_calls':154,'frame_reset1_calls':154,
        'FP32_values_correct_prefix':1799280,'failed_invocation':49,'changed_DATA_FP32':800,'INDEX_FP32_bitwise':4200,'late_source_reads':0,
        'full_model_calls':0,'new_Host107_runs':0,'normal_drain_LAST_pass':False,'VPU_packets':215,'decoded_NoInput_images':214,
        'copy_overlap_spans':100,'ioctl_records':1282,'compactions':0,'BOOT_SDK_model_kernel_unchanged':True,'root_cause_resolved':False,
        'agent_programs_connections_closed':True,'management_estimate':83,'reviews':{p:sha(E/p) for p in reviews},
        'archives':{p.name:sha(p) for p in E.glob('*.tar')},'sdk_r2_adaptation_diff_sha256':sha(E/'address-sdk-r2.diff'),
        'r1_compiled_not_uploaded_program_sha256':load(old/'build-result.json')['program_sha256'],'r1_compiled_source_hashes':load(old/'build-result.json')['sources'],
        'documents':{p:sha(R/p) for p in docs},'checkpoint_sha256':sha(E/'next-checkpoint.json')}
(E/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Archived153 correct/154 actual; DATA800 stale failure preserved; completionSHA',sha(E/'completion-review.json'))
