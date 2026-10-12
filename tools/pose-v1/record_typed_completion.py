"""Bind three controlled stages, real types, compaction and closed lifetimes."""
import json,re
import mixed_validation_gate as g
root=g.ROOT;e=root/'tools/pose-v1/evidence/typed-scratch-20261010-r1'
def load(n):return g.load(e/n)
def write(n,v):p=e/n;assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n')
base=load('baseline.acceptance.json');contracts=load('contracts.acceptance.json');stages={s:load(s+'.acceptance.json') for s in ('static','dynamic','vpu')};video=load('video.review.json')
assert not base['Host107_new_run'] and base['Host107_reused']==107 and contracts['ARM_refusals']==base['Native_refusals']==8
assert all(v['pairs']==100 and v['FP32_compared']==1194000 for v in stages.values()) and video['decoded_frames']==226
archives={'contracts.tar':'b34a893a8bb189cc0760187f6edadb75477bb5f85d2c3c3c01abedab2dff95b5','static.tar':'69f97fe80427eae14fce7479ae591d932dc7a27927898e414d6047b2abbac5dd','dynamic.tar':'4c4104b609e4d03055b5595527e06afe31e50cc6075f6cbf88b0a5737eec4919','vpu.tar':'9482f6a588fb47b075aaf41541e203804f20faa116611e4c830547ad5fc38199'}
for n,digest in archives.items():assert g.sha(e/n)==digest
def snap(d,prefix,label):
    units=0
    for line in (d/(prefix+'.pagetypeinfo')).read_text().splitlines():
        m=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
        if m:
            counts=list(map(int,m[2].split()));assert len(counts)==11;units+=sum(counts[i]*2**(i-7) for i in range(7,11))
    mem={m[1]:int(m[2]) for m in re.finditer(r'^(\w+):\s+(\d+) kB$',(d/(prefix+'.meminfo')).read_text(),re.M)}
    return dict(label=label,ordinary_512KiB_units=units,MemAvailable_KiB=mem['MemAvailable'],CmaFree_KiB=mem['CmaFree'],sha256={n:g.sha(d/(prefix+'.'+n)) for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat')})
snapshots=[];kernels=[]
for stage in ('contracts','static','dynamic','vpu'):
    r=e/(stage+'-return')/('run-'+stage);g.verify(r);assert (r/'exit.txt').read_text().strip()=='0'
    assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes();kernels.append((r/'dmesg.after.log').read_bytes())
    snapshots.extend(snap(r,prefix,stage+'.'+prefix) for prefix in ('before','after'))
    assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (r/'final.processes').read_text().splitlines()[1:])
    ports=(r/'final.ports').read_text();assert ':39001 ' not in ports and ':8554 ' not in ports
assert all(k==kernels[0] for k in kernels)
comp=e/'vpu-return/compaction-before-vpu';decision=g.load(comp/'decision.json');assert decision['compaction_writes']==1 and decision['elapsed_ns']==217374570 and decision['ordinary_512KiB_units_before']==14 and decision['kernel_unchanged']
before_kernel=(comp/'before.dmesg').read_bytes();after_kernel=(comp/'after.dmesg').read_bytes()
assert before_kernel==after_kernel
# Python3's UTF8 locale coercion changes dmesg escaping for this one boot line.
# Whitelist the complete observed line; every other byte must still match.
escaped=b'[    1.729153] jffs2: version 2.2. (NAND) \\xc2\\xa9 2001-2006 Red Hat, Inc.\n'
literal=escaped.replace(b'\\xc2\\xa9',bytes([0xc2,0xa9]))
assert kernels[0].count(escaped)==before_kernel.count(literal)==1
assert before_kernel.replace(literal,escaped)==kernels[0]
assert g.sha(e/'vpu-return/compact_typed_before_vpu.py')==g.sha(root/'tools/pose-v1/compact_typed_before_vpu.py')
cs=[snap(comp,p,'compaction.'+p) for p in ('before','after')];assert cs[0]['ordinary_512KiB_units']==14 and cs[1]['ordinary_512KiB_units']==143
write('resource-review.json',dict(status='typed_scratch_cleanup_and_resource_policy_checked',kernel_events_unchanged=True,each_stage_raw_kernel_unchanged=True,compaction_raw_kernel_unchanged=True,cross_capture_boot_copyright_escape_only=True,cross_capture_exact_whitelist_line=escaped.decode(),format_diff_sha256=g.sha(e/'dmesg-format-diff.json'),snapshots=snapshots,compaction_snapshots=cs,decision=decision,agent_compactions=1,compaction_ms=217.37457,drop_caches=False,reboot=False,CMA_changed=False,program_processes_remaining=0,input_RTSP_ports_released=True,not_leak_or_permanent_startup_proof=True))
regions=[]
for stage in ('static','dynamic','vpu'):
    meta=g.load(e/(stage+'-return')/('run-'+stage)/'results/sdk/regions.json')
    assert [v['address'] for v in meta['sources']]==[4096,34368] and meta['padding_address']==34336
    regions.append(dict(stage=stage,source_addresses=[v['address'] for v in meta['sources']],region_object=meta['region_identity'],types=[v['actual_type'] for v in meta['sources']]))
refs=['build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json','static.acceptance.json','dynamic.acceptance.json','vpu.acceptance.json','video.review.json','resource-review.json']
report=dict(status='actual_types_static_dynamic_and_VPU_scratch_passed_model_fault_unresolved',program_sha256=stages['static']['typed_binary_sha256'],original_main_sha256=base['binary_sha256'],manifest_sha256=base['package_manifest_sha256'],payloads=403,build_sources=90,Host107_new_run=False,Host107_reused=107,registry_reused=12,Host_FP32_reused=59600,Native_ARM_refusals_each=8,Native_patterns=101,unique_Native_slot_fingerprints=202,static_pairs=100,dynamic_pairs=100,VPU_dynamic_pairs=100,FP32_compared=3582000,source_normal_reads_per_stage=1,source_normal_reads_between_pairs=0,pattern_indices_dynamic=[1,100],SDK_write_pairs_excluding_initial=200,stage_copy_spans_ms={s:v['copy_span_ms'] for s,v in stages.items()},source_regions=regions,VPU_packets=228,VPU_image_frames=226,VPU_header_packets=1,VPU_empty_LAST=1,VPU_stream_bytes=video['stream_bytes'],actual_PTS_match=True,all_encoded_ids_decoded=True,VPU_drained=True,SDK_on_encoder_thread=False,workers_join_before_SDK_destruction=True,full_model_Session=False,NPU_forward=False,model_inference_frames=0,model_fault_reproduced=False,root_cause_fixed=False,VPU_exonerated_in_all_conditions=False,DMA_cache_fence_proven=False,zero_copy_verified=False,performance_accepted=False,long_term_accepted=False,agent_compactions=1,compaction_ms=217.37457,BOOT_SDK_model_math_changed=False,all_agent_sessions_closed=True,final_MemAvailable_KiB=snapshots[-1]['MemAvailable_KiB'],final_CmaFree_KiB=snapshots[-1]['CmaFree_KiB'],final_ordinary_512KiB_units=snapshots[-1]['ordinary_512KiB_units'],evidence_sha256={n:g.sha(e/n) for n in refs},archive_sha256=archives,limitations=['Real types, full-valid distributions, changing FP32 data and one VPU context passed only at SDK-owned low source addresses.','Graph deserialization and heap/log allocations perturb timing; do not attribute absence solely to type.','VPU resource preparation used one recorded compaction; not first-start/permanent numerical reliability proof.','No model Session or NPU forward; remaining actual model source position and producer path differ.'])
write('completion-review.json',report)
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-typed-scratch/package-20261010-r1',build='.local/pose-v1-build/mixed-20261010-typed-scratch-r1',board='/tmp/pose-typed-scratch-20261010-r1',completion_sha256=g.sha(e/'completion-review.json'),next='Read TYPED-SCRATCH-RESULTS-20261010, ADR_24 and TYPED-SCRATCH-NEXT-20261010. Real type static100, dynamic100, dynamic+VPU100 all pass at SDK-owned addresses4096/34368; no model/NPU forward. Compaction1 recorded14to143 ordinary512KiB units,217.37457ms. Old inv72 bad bytes kept; no model fault fix. Next prepare public MemManager info and legal allocator-owned elevated-position scratch, no fixed model address/private cursor/mapping/register/cache/SDK/BOOT/CMA guess. If capacity/ownership not confirmable stop; NPU production path remains a separate difference. Model103/long-term/HDMI/zero-copy pending.')
write('next-checkpoint.json',checkpoint);active=load('active-checkpoint.json');active.update(status=report['status'],active_stage=None,active_tests=False,services_running=False,SSH_SCP_closed=True,completion_sha256=checkpoint['completion_sha256']);(e/'active-checkpoint.json').write_text(json.dumps(active,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','FP32_compared','VPU_image_frames','agent_compactions','final_ordinary_512KiB_units','root_cause_fixed')}))
