"""Bind isolated scratch results and cleanup; this script never connects to Lite."""
import json, re
import mixed_validation_gate as g

root = g.ROOT
e = root/'tools/pose-v1/evidence/scratch-copy-20261010-r3'
def write(name, value):
    p = e/name
    assert not p.exists()
    p.write_text(json.dumps(value, indent=2)+'\n')

baseline = g.load(e/'baseline.acceptance.json')
contracts = g.load(e/'contracts.acceptance.json')
memory = g.load(e/'memory.acceptance.json')
vpu = g.load(e/'vpu.acceptance.json')
video = g.load(e/'video.review.json')
assert baseline['Host107_new_run'] is False and baseline['Host_cases_reused']==107
assert contracts['ARM_pattern_refusals']==contracts['Native_pattern_refusals']==10
assert memory['pairs']==vpu['pairs']==100 and video['decoded_frames']==200
archives = {'contracts.tar':'2274ded3a4591af4ca0f90f3052a7b321820994493f4ac72e778be254a967811',
            'memory.tar':'ee335ec8714d7e91f8868ee3722cc39304a962d59388e36a920f72de38410546',
            'vpu.tar':'0e3f33ee4b020493cfefee7d6e8245fd1c2c342fa9b5601fca035c7548b10909'}
for name, digest in archives.items():
    assert g.sha(e/name)==digest
snapshots=[]
kernels=[]
for stage in ('contracts','memory','vpu'):
    r=e/(stage+'-return')/('run-'+stage)
    assert g.verify(r)>0 and (r/'exit.txt').read_text().strip()=='0'
    assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
    kernels.append((r/'dmesg.after.log').read_bytes())
    for when in ('before','after'):
        page=r/(when+'.pagetypeinfo'); units=0
        for line in page.read_text().splitlines():
            m=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
            if m:
                counts=list(map(int,m[2].split()));assert len(counts)==11
                units+=sum(counts[i]*2**(i-7) for i in range(7,11))
        mem={m[1]:int(m[2]) for m in re.finditer(r'^(\w+):\s+(\d+) kB$',(r/(when+'.meminfo')).read_text(),re.M)}
        snapshots.append(dict(stage=stage,when=when,ordinary_512KiB_units=units,
                              MemAvailable_KiB=mem['MemAvailable'],CmaFree_KiB=mem['CmaFree'],
                              sha256={n:g.sha(r/(when+'.'+n)) for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat')}))
    processes=(r/'final.processes').read_text().splitlines()[1:]
    assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in processes)
    ports=(r/'final.ports').read_text();assert ':39001 ' not in ports and ':8554 ' not in ports
assert all(k==kernels[0] for k in kernels)
for stage in ('memory','vpu'):
    meta=g.load(e/(stage+'-return')/('run-'+stage)/'results/sdk/regions.json')
    assert [x['address'] for x in meta['sources']]==[4096,34368]
    assert meta['padding_address']==34336 and meta['padding_bytes']==32
write('resource-review.json',dict(status='scratch_resources_and_cleanup_checked',snapshots=snapshots,
    kernel_unchanged=True,agent_compactions=0,reason='Ordinary high-order pages present; no compaction needed for this batch.',
    drop_caches=False,reboot=False,CMA_changed=False,program_processes_remaining=0,input_RTSP_ports_released=True,
    not_leak_or_permanent_startup_proof=True))
write('local-corrections.json',dict(status='local_tools_corrected_without_board_retry',
    corrections=[
      'r1 natural SDK B address34336 was mod64=32; preserved successful100-pair memory evidence, no r1 VPU run. r2 adds SDK-owned32-byte padding, no fixed source address.',
      'r2 explicitUTF8 preparation corrects Windows GBK read failure; partial generated source asserted identical and retained. r2 built only, no ARM device run.',
      'Before r2 hardware transfer, audit found first-copy owned bytes lost on second-copy throw; r3 caller-owned Pair/saveAvailable and independent two late reads added. Native/ARM partial-byte tests passed.',
      'Initial local video review counted SPS/PPS capture as image. Corrected by parsing actual per-capture NAL types:1 header packet,200 VCL packets,1 empty LAST;200 decoded IDs and actual queued/capture PTS match. No source/package/board rerun.'
    ],hardware_failures_this_batch=0,automatic_retry=False))
refs=['build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json','memory.acceptance.json',
      'vpu.acceptance.json','video.review.json','resource-review.json','local-corrections.json']
report=dict(status='isolated_SDK_scratch100_memory_and100_VPU_passed_model_fault_unresolved',
    scratch_program_sha256=memory['scratch_binary_sha256'],original_main_sha256=memory['binary_sha256'],
    manifest_sha256=memory['package_manifest_sha256'],payloads=403,build_sources=85,
    Host107_new_run=False,Host107_reused=107,registry_records_reused=12,Host_FP32_reused=59600,
    Native_ARM_refusals_each=10,memory_pairs=100,VPU_pairs=100,FP32_compared=2388000,
    memory_copy_span_ms=memory['copy_span_ms'],VPU_copy_span_ms=vpu['copy_span_ms'],
    VPU_packets=202,VPU_image_frames=200,VPU_header_packets=1,VPU_empty_LAST=1,VPU_stream_bytes=video['stream_bytes'],
    actual_PTS_match=True,all_encoded_ids_decoded=True,VPU_drained=True,all_source_addresses_mod64=0,
    SDK_scratch_source_addresses=[4096,34368],SDK_owned_padding_bytes=32,
    first_nonempty_VPU_capture_was_SPS_PPS=True,SDK_on_encoder_thread=False,
    main_owns_SDK=True,workers_join_before_SDK_destruction=True,SDK_free_contracts_partial_capture_verified=True,
    full_model_Session=False,NPU_forward=False,model_inference_frames=0,model_fault_reproduced=False,
    root_cause_fixed=False,VPU_exonerated_in_all_conditions=False,DMA_cache_fence_proven=False,
    zero_copy_verified=False,performance_accepted=False,long_term_accepted=False,
    agent_compactions=0,BOOT_SDK_model_math_changed=False,all_agent_sessions_closed=True,
    final_MemAvailable_KiB=snapshots[-1]['MemAvailable_KiB'],final_CmaFree_KiB=snapshots[-1]['CmaFree_KiB'],
    evidence_sha256={name:g.sha(e/name) for name in refs},archive_sha256=archives)
write('completion-review.json',report)
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,
    SSH_SCP_closed=True,package='.local/pose-v1-scratch-copy/package-20261010-r3',
    build='.local/pose-v1-build/mixed-20261010-scratch-copy-r3',board='/tmp/pose-scratch-copy-20261010-r3',
    completion_sha256=g.sha(e/'completion-review.json'),
    next='Read SCRATCH-COPY-RESULTS-20261010, ADR_22 and SCRATCH-COPY-NEXT-20261010. Isolated same-length64-aligned SDK-owned copies pass100 without VPU and100 with VPU. No model Session/NPU. Constant1D scratch/low PL DDR addresses differ from real model type/layout/source position; model fault remains unresolved. Prepare minimal source/chunk/region/Host-destination identity observer without changing waits/copy/math or extra normal data reads. Preserve old bad bytes, late source reads, full candidate gates and bounded stop. No old failure retry/cache/mapping/register/BOOT/SDK/CMA guess. Long-term/HDMI/zero-copy pending.')
write('next-checkpoint.json',checkpoint)
print(json.dumps({k:report[k] for k in ('status','FP32_compared','VPU_image_frames','agent_compactions','root_cause_fixed')}))
