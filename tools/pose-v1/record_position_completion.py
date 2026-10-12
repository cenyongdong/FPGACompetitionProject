"""Bind legal source position, actual returned bytes, VPU and closed resources."""
import json,re
import mixed_validation_gate as g
root=g.ROOT;e=root/'tools/pose-v1/evidence/plddr-position-20261010-r1'
def load(n):return g.load(e/n)
def write(n,v):p=e/n;assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
base=load('baseline.acceptance.json');contracts=load('contracts.acceptance.json');stages={s:load(s+'.acceptance.json') for s in ('dynamic','vpu')};video=load('video.review.json')
assert base['Native_position_refusals']==contracts['ARM_position_refusals']==12 and base['Native_refusals']==contracts['ARM_refusals']==8
assert not base['Host107_new_run'] and base['Host107_reused']==107
assert all(x['source_addresses']==[100667392,100697664] and x['pairs']==100 and x['FP32_compared']==1194000 and x['SDK_chunks_released']==4 for x in stages.values())
archives={'manager-return.tar':'f90aebee931b23d8e0c4a4736d325df98b3a13f415dd3baaeccaa779790ec8a0','contracts.tar':'ad55c59865a3c1b75789039db8106844514bf8ecf802c05bef1f998dff1e16a8','dynamic.tar':'d3a271405f993cd7efa79b9400c0161e0c81b44ba17e84915948356f4c5cebfd'}
# VPU return hash is separately checked against the board-published archive identity.
archives['vpu.tar']=load('vpu-archive-identity.json')['board_sha256']
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
for stage in ('contracts','dynamic','vpu'):
    r=e/(stage+'-return')/('run-'+stage);g.verify(r);assert (r/'exit.txt').read_text().strip()=='0' and (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes();kernels.append((r/'dmesg.after.log').read_bytes())
    snapshots.extend(snap(r,prefix,stage+'.'+prefix) for prefix in ('before','after'))
    assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (r/'final.processes').read_text().splitlines()[1:])
    assert all(port not in (r/'final.ports').read_text() for port in (':39001 ',':8554 '))
assert all(k==kernels[0] for k in kernels)
resource=e/'vpu-return/resource-before-vpu';decision=g.load(resource/'decision.json');assert decision['compaction_writes']==0 and decision['ordinary_512KiB_units_before']==24 and decision['kernel_unchanged']
bk=(resource/'before.dmesg').read_bytes();ak=(resource/'after.dmesg').read_bytes();assert bk==ak
escaped=b'[    1.729153] jffs2: version 2.2. (NAND) \\xc2\\xa9 2001-2006 Red Hat, Inc.\n';literal=escaped.replace(b'\\xc2\\xa9',bytes([0xc2,0xa9]))
assert kernels[0].count(escaped)==bk.count(literal)==1 and bk.replace(literal,escaped)==kernels[0]
assert g.sha(e/'vpu-return/compact_typed_before_vpu.py')==g.sha(root/'tools/pose-v1/compact_typed_before_vpu.py')
rs=[snap(resource,p,'resource.'+p) for p in ('before','after')]
write('resource-review.json',dict(status='position_scratch_resource_and_cleanup_checked',decision=decision,agent_compactions=0,snapshots=snapshots,pre_VPU_snapshots=rs,kernel_events_unchanged=True,each_stage_raw_kernel_unchanged=True,resource_raw_kernel_unchanged=True,cross_capture_boot_copyright_escape_only=True,exact_whitelist_line=escaped.decode(),drop_caches=False,reboot=False,CMA_changed=False,program_processes_remaining=0,input_RTSP_ports_released=True,not_leak_or_permanent_startup_proof=True))
vsummary=g.load(e/'vpu-return/run-vpu/results/vpu/summary.json');assert vsummary['submitted']==vsummary['returned']==video['decoded_frames']
refs=['manager.acceptance.json','build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json','dynamic.acceptance.json','vpu.acceptance.json','video.review.json','resource-review.json']
tools=['build_plddr_manager.py','prepare_plddr_position_r1.py','run-plddr-manager.sh','run-position-scratch.sh','review_position_build.py','review_position_scratch.py','run_position_native.py','position_scratch_transfer.py','record_position_completion.py']
report=dict(status='public_allocator_and_elevated_position_dynamic_VPU_scratch_passed_model_fault_unresolved',program_sha256=stages['dynamic']['position_binary_sha256'],original_main_sha256=base['binary_sha256'],manifest_sha256=base['package_manifest_sha256'],payloads=403,build_sources=94,Host107_new_run=False,Host107_reused=107,registry_reused=12,Host_FP32_reused=59600,Native_ARM_position_refusals_each=12,Native_ARM_byte_refusals_each=8,source_addresses=[100667392,100697664],padding_address=100697632,prefix_bytes=100663296,prefix_address=4096,prefix_data_operations=0,pool_declared_range=[4096,4294967296],physical_full_pool_capacity_proven=False,all_self_allocated_chunks_released=True,dynamic_pairs=100,VPU_dynamic_pairs=100,FP32_compared=2388000,source_normal_reads_per_stage=1,source_normal_reads_between_pairs=0,SDK_write_pairs_excluding_initial=200,stage_copy_spans_ms={s:v['copy_span_ms'] for s,v in stages.items()},VPU_packets=vsummary['packets'],VPU_image_frames=video['decoded_frames'],VPU_header_packets=video['SPS_PPS_packets'],VPU_empty_LAST=1,VPU_stream_bytes=video['stream_bytes'],actual_PTS_match=True,all_encoded_ids_decoded=True,VPU_drained=True,SDK_on_encoder_thread=False,workers_join_before_SDK_destruction=True,full_model_Session=False,NPU_forward=False,model_inference_frames=0,model_fault_reproduced=False,root_cause_fixed=False,DMA_cache_fence_proven=False,zero_copy_verified=False,performance_accepted=False,long_term_accepted=False,agent_compactions=0,BOOT_SDK_model_math_changed=False,all_agent_sessions_closed=True,final_MemAvailable_KiB=snapshots[-1]['MemAvailable_KiB'],final_CmaFree_KiB=snapshots[-1]['CmaFree_KiB'],final_ordinary_512KiB_units=snapshots[-1]['ordinary_512KiB_units'],evidence_sha256={n:g.sha(e/n) for n in refs},review_tools_sha256={n:g.sha(root/'tools/pose-v1'/n) for n in tools},archive_sha256=archives,limitations=['Allocator-owned sources are near96MiB, not exact old model109232128/109285376.','No model Session/NPU producer; typed metadata and new graph parsing alter heap/timing.','Successful declared-region byte copies do not certify the entire4GiB physical capacity.','VPU uses synthetic NoInput; not inference throughput, stable103, or permanent startup reliability.'])
write('completion-review.json',report)
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-plddr-position/package-20261010-r1',build='.local/pose-v1-build/mixed-20261010-plddr-position-r1',board='/tmp/pose-plddr-position-20261010-r1',completion_sha256=g.sha(e/'completion-review.json'),next='Read PLDDR-POSITION-RESULTS-20261010, ADR_25 and PLDDR-POSITION-NEXT-20261010. SDK public capacity/ownership and96MiB prefix confirmed; actual100667392/100697664 dynamic100 andVPU100 pass. No model/NPU forward, no compaction this batch; model inv72 failure preserved and unresolved. Next audit a public minimal NPU-producer contrast design, separate approval, no fixed model address/private mappings/cache/BOOT/CMA guesses. Stable103/long-term/HDMI/zero-copy pending.')
write('next-checkpoint.json',checkpoint);write('active-checkpoint.json',checkpoint)
print(json.dumps({k:report[k] for k in ['status','FP32_compared','VPU_image_frames','agent_compactions','root_cause_fixed','final_ordinary_512KiB_units']}))
