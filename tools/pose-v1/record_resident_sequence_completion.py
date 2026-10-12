"""Bind numerical, video, resource and lifetime evidence of the single run."""
import collections,json,re
import mixed_validation_gate as g
from review_resident_sequence_build_base import identities,rows
root=g.ROOT;e=root/'tools/pose-v1/evidence/resident-sequence-20261010-r1'
def put(name,value):
    p=e/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
def snapshot(label,p,prefix,separator='.',suffix=''):
    def path(name):return p/(prefix+separator+name+suffix)
    units=0
    for line in path('pagetypeinfo').read_text().splitlines():
        m=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
        if m:
            counts=list(map(int,m[2].split()));assert len(counts)==11;units+=sum(counts[i]*2**(i-7) for i in range(7,11))
    mem={m[1]:int(m[2]) for m in re.finditer(r'^(\w+):\s+(\d+) kB$',path('meminfo').read_text(),re.M)}
    return dict(label=label,ordinary_512KiB_units=units,MemAvailable_KiB=mem['MemAvailable'],CmaFree_KiB=mem['CmaFree'],files_SHA256={n:g.sha(path(n)) for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat')})
m,b,n=identities(root/'.local/pose-v1-resident-sequence/package-20261010-r1',root/'.local/pose-v1-build/mixed-20261010-resident-sequence-r1')
base=g.load(e/'baseline.acceptance.json');contracts=g.load(e/'contracts.acceptance.json');result=g.load(e/'resident.acceptance.json');objects=g.load(e/'resident.objects.json');counts=g.load(e/'resident.counts.json');video=g.load(e/'resident.video.json')
assert result['status']=='resident_stage_passed' and result['correct']==107 and result['FP32_compared']==1615700 and result['kernel_unchanged']
assert objects['rows']==1712 and objects['copied_inputs']==856 and not objects['object_changed_across_copy']
assert counts['query_rows']==856 and counts['metadata_rows']==963 and counts['combined_rows']==1819 and not counts['below234'] and not counts['query_errors']
assert video['decoded_frames']==518 and video['stream_bytes']==93978 and video['actual_PTS_match'] and video['model_inference_frames']==0
archives={'contracts.tar':'11b7b50d37294fa48984ff3b9a8677e36a0ce6c03ed5a962f979a8a784f2c5a9','resident.tar':'41a00e2405e0bb82d3e5c589991dd318f7a30c9c3f32b8a9d2cbed1e495e8c55'}
assert g.sha(root/'.local/pose-v1-resident-sequence/transfer-20261010-r1.tar')=='9e4182bc00de772c0a456e10dfbe1436bb4e56ec031a312da72111378f5e6f28'
for name,digest in archives.items():assert g.sha(e/name)==digest
r=e/'resident-return/run-resident';out=r/'results';g.verify(r);events=rows(out/'vpu/encoder/events.jsonl');life=rows(out/'lifecycle.jsonl');timing=rows(out/'timing.jsonl')
mapped=[x for x in events if x['event']=='mapped_total'];assert len(mapped)==2 and all(x['buffers']==2 for x in mapped) and sum(x['bytes'] for x in mapped)==6959104
assert len([x for x in events if x['event']=='identity'])==1 and len([x for x in events if x['event']=='streamon'])==2 and len([x for x in events if x['event']=='streamoff'])==2
assert not any(x['event'] in ('abort_streamoff','dqbuf_error') for x in events)
snapshots=[];kernels=[]
for label in ('contracts','resident'):
    p=e/(label+'-return')/('run-'+label);g.verify(p);assert (p/'exit.txt').read_text().strip()=='0'
    assert (p/'dmesg.before.log').read_bytes()==(p/'dmesg.after.log').read_bytes();kernels.append((p/'dmesg.after.log').read_bytes())
    assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (p/'final.processes').read_text().splitlines()[1:])
    assert all(port not in (p/'final.ports').read_text() for port in (':39001 ',':8554 '))
    for prefix in ('before','after'):snapshots.append(snapshot(label+'.'+prefix,p,prefix))
assert kernels[0]==kernels[1]
prep=e/'resident-return/resources-before';decision=g.load(prep/'decision.json');assert decision['compaction_writes']==1 and decision['kernel_unchanged'] and not any(decision[k] for k in ('drop_caches','reboot','CMA_changed','numerical_fault_fixed'))
assert (prep/'before.dmesg').read_bytes()==(prep/'after.dmesg').read_bytes()
for prefix in ('before','after'):snapshots.append(snapshot('resources.'+prefix,prep,prefix))
allocation=[]
for x in events:
    if x['event']=='memory_snapshot':allocation.append(snapshot(x['stage'],out/'vpu/encoder/memory',x['prefix'],'-','.txt'))
put('resource-review.json',dict(status='resident_resources_one_context_and_cleanup_checked',snapshots=snapshots,allocation_snapshots=allocation,compaction_decision=decision,mapped_bytes=6959104,VPU_contexts=1,first_startup_succeeded_this_run=True,ordinary_units_compaction_before=9,ordinary_units_compaction_after=28,agent_compactions=1,kernel_raw_contracts_and_resident_identical=True,programs_remaining=0,ports_released=True,not_leak_or_permanent_startup_proof=True))
data=rows(out/'tensor-identities/objects.jsonl');pairs=collections.defaultdict(list);align=set()
for x in data:
    if x['op_id']==192 and x['point']=='after_copy':pairs[x['invocation']].append(x['source']['address_identity']);align.add(x['destination']['address_identity']%64)
assert all(v==[109232128,109285376] for v in pairs.values()) and len(pairs)==107
completion=[x for x in rows(out/'copy-observations/metadata.jsonl') if x['kind']!='post_copy_Host_shadow'];assert len(completion)==107 and all(x['op_id']==582 and x['initial']==x['final']==638 and x['polls']==1 for x in completion)
assert not (out/'failed-host-inputs').exists() and not (out/'failed-invocation-inputs').exists()
refs=['build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json','resident.acceptance.json','resident.objects.json','resident.counts.json','resident.video.json','resource-review.json']
report=dict(status='single_resident_VPU_Engine_three_then103_passed_fault_unresolved',program_SHA256=b['resident_binary_sha256'],manifest_SHA256=b['package_manifest_sha256'],original_main_SHA256=b['binary_sha256'],old_model_VPU_SHA256=b['model_vpu_binary_sha256'],payloads=n,build_sources=len(m['build_files']),Host107_new_run=False,Host107_reused=107,registry_reused=12,CPU_FP32_reused=59600,Native_ARM_contracts_each={'sequence':13,'producer':16,'load':6,'run':9},phases=[{'offset':0,'calls':4,'FP32':60400,'period_ns':500000000},{'offset':4,'calls':103,'FP32':1555300,'period_ns':200000000}],correct_calls=107,FP32_compared=1615700,all_raw_inputs_full100_scores_and_poses_saved_before_gate=True,unique_calls_and_frames=True,source_addresses=[109232128,109285376],object_rows=1712,shadow_rows=856,producer192_queries=856,all192_counts234=True,copy_metadata=963,completion582_extra_polls=0,Host_destination_mod64=sorted(align),VPU_contexts=1,Engine_instances=1,Engine_init_ms=life[1]['init_ms'],VPU_synthetic_images=518,VPU_stream_bytes=93978,VPU_packets=520,VPU_actual_PTS_and_pixels_verified=True,VPU_first_ready_may_be_parameter_packet=True,drain_LAST_and_two_STREAMOFF=True,worker_joined_before_Engine_destroyed=True,synthetic_frames_not_pose_throughput=True,stage103_actual_begin_span_ms=(timing[-1]['process_begin_ns']-timing[4]['process_begin_ns'])/1e6,agent_compactions=1,compaction_elapsed_ms=decision['elapsed_ns']/1e6,final_MemAvailable_KiB=snapshots[3]['MemAvailable_KiB'],final_CmaFree_KiB=snapshots[3]['CmaFree_KiB'],final_ordinary_units=snapshots[3]['ordinary_512KiB_units'],normal_source_reads_added=0,exception_late_source_reads_triggered=0,old_exception_and_two_late_reads_retained=True,root_cause_fixed=False,VPU_model_fault_cause_proven=False,permanent_first_startup_accepted=False,performance_accepted=False,long_term_accepted=False,render_display_network_HDMI=False,BOOT_SDK_model_math_changed=False,active_tests=False,services_running=False,all_agent_sessions_closed=True,archive_SHA256=archives,evidence_SHA256={name:g.sha(e/name) for name in refs})
put('completion-review.json',report)
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-resident-sequence/package-20261010-r1',build='.local/pose-v1-build/mixed-20261010-resident-sequence-r1',board='/tmp/pose-resident-sequence-20261010-r1',program_SHA256=report['program_SHA256'],manifest_SHA256=report['manifest_SHA256'],completion_review_SHA256=g.sha(e/'completion-review.json'),compactions=1,resume='Read RESIDENT-SEQUENCE-RESULTS/NEXT-20261010.md and ADR_28/ADR_02. Approved single-lifecycle run completed107 correct forward/1615700FP32,518 synthetic images; old failure remains unresolved. No rerun or background. Next only prepare one real owned-image/render factor in same lifecycle, source/PTS/pixel and three/103 gates; no display child/network/HDMI yet. First startup under one recorded compaction is not permanent reliability; retain old exceptions/two late source reads and frozen model/SDK/BOOT. No5Hz/long-term/zero-copy acceptance.')
put('next-checkpoint.json',checkpoint);(e/'active-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:report[k] for k in ('status','correct_calls','FP32_compared','VPU_synthetic_images','agent_compactions','final_ordinary_units')}))
