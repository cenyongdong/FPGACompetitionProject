"""Archive this stopped batch, resources and independently checked evidence."""
import json,re
from pathlib import Path
import mixed_validation_gate as g
def main():
    e=g.ROOT/'tools/pose-v1/evidence/invocation-guard-20261009-r1'
    def load(n):return g.load(e/n)
    def write(n,x):
        p=e/n;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n')
    host=load('host-check.acceptance.json');three=load('process-three.acceptance.json');failed=load('failed-load.numeric-review.json');pattern=load('bad-block-pattern-r2.json')
    assert host['Host_cases']==107 and host['CPU_FP32']==59600 and three['consumed']==4 and failed['consumed']==11
    assert load('failed.integration.json')['owned_bytes']==47760 and failed['all_persistence_tasks_saved'] and pattern['all_changed_bytes_equal_previous_copy_same_offset']
    dirs=[e/'host-return/resources-before-three',e/'three-return/resources-before-load',e/'failed-return/resources-final']
    resources=[]
    for d in dirs:
        units=0
        for line in (d/'pagetypeinfo').read_text().splitlines():
            match=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
            if match:
                counts=list(map(int,match[2].split()));assert len(counts)==11
                units+=sum(counts[i]*(2**(i-7)) for i in range(7,11))
        mem={m[1]:int(m[2]) for m in re.finditer(r'^(\w+):\s+(\d+) kB$',(d/'meminfo').read_text(),re.M)}
        resources.append(dict(path=str(d.relative_to(g.ROOT)),ordinary_512KiB_units=units,MemAvailable_KiB=mem['MemAvailable'],CmaFree_KiB=mem['CmaFree'],sha256={p.name:g.sha(p) for p in d.iterdir() if p.is_file()}))
    kernel=[(d/'dmesg').read_bytes() for d in dirs];assert kernel[0]==kernel[1]==kernel[2]
    for label,stage in [('host-return','host-check'),('three-return','process-three'),('failed-return','load-103')]:
        r=e/label/('run-'+stage);assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()==kernel[0]
    final=dirs[-1];assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (final/'processes').read_text().splitlines()[1:])
    ports=(final/'ports').read_text();assert ':39001 ' not in ports and ':8554 ' not in ports
    resource=dict(status='resource_identity_and_cleanup_checked',kernel_unchanged=True,compactions=0,reason='Ordinary high-order free blocks sufficient before both stages; no compact_memory write performed.',drop_caches=False,reboot=False,CMA_changed=False,program_processes_remaining=0,input_RTSP_ports_released=True,snapshots=resources,not_leak_or_permanent_startup_proof=True)
    write('resource-review.json',resource)
    archives={'host-check.tar':'2e1fa258d642f5c049070da8212d553938afcc718cd01056ded8e239315ee744','process-three.tar':'4d1ab00cd5a0b400cc23134737c545c69514790a485c3b849d0d109a6e707289','failed-load-103.tar':'63910dfeee1eae33a5d82ff5cee63b13035b3a1ce2c4c672150f26fb733c2b98'}
    for name,digest in archives.items():assert g.sha(e/name)==digest
    media={}
    for label in ('three','failed'):
        v=load('video-'+label+'/review.json');n=load('network-'+label+'/review.json')
        media[label]=dict(encoded=v['decoded_frames'],network=n['network_frames'],sources=v.get('inference_sources',v.get('decoded_inference_sources')),joint_checks=v['joint_visibility_checks'],complete=label=='three')
    refs=['build.acceptance.json','build.integration.json','host-check.acceptance.json','host.integration.json','process-three.acceptance.json','three.integration.json','three.shadow.json','reference-three-review.json','video-three/review.json','network-three/review.json','failed-load.numeric-review.json','failed.integration.json','failed-frame-golden.json','failed-Host-classification.json','source-readback-analysis.json','bad-block-pattern-r2.json','reference-failed-review.json','video-failed/review.json','network-failed/review.json','resource-review.json']
    report=dict(status='invocation_retention_integrated_Host_three_passed_load_failed192_evidence_complete',program_sha256=host['binary_sha256'],manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=74,Host_cases=107,registry_records=12,Host_FP32=59600,SDK_free_refusals_Native_ARM_each=12,finite_Host_probe_bytes=47040,old_Host_probe_source_read_bytes=94080,three_forwards=4,three_FP32=60400,load_correct_prefix=11,load_correct_FP32=166100,all_correct_forwards=15,all_correct_FP32=226500,failed_invocation=11,failed_frame=100011,failed_case='S21_31_349',failed_op=192,owned_failed_frame_inputs=3,owned_failed_frame_bytes=47760,Host_index_noninteger_values=496,changed_ranges=18,all_bad_blocks_equal_previous_copy_same_offset=True,post_copy_equals_post_kernel_staging=True,later_device_sources_both_gold=True,actual_late_device_source_bytes=94080,metadata_rows=102,normal_device_reads_added=0,original_CPU_exception_preserved=True,all_six_persistence_tasks_saved=True,finite_hardware_output_failure_triggered=False,media=media,load103_passed=False,performance_accepted=False,root_cause_fixed=False,compactions=0,BOOT_SDK_model_math_changed=False,all_agent_sessions_closed=True,final_MemAvailable_KiB=resources[-1]['MemAvailable_KiB'],final_CmaFree_KiB=resources[-1]['CmaFree_KiB'],evidence_sha256={name:g.sha(e/name) for name in refs},archive_sha256=archives,source_sha256={p.name:g.sha(p) for p in (g.ROOT/'tools/pose-v1').glob('*invocation*.py')})
    write('completion-review.json',report)
    checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-invocation-guard/package-20261009-r1',build='.local/pose-v1-build/mixed-20261009-invocation-guard-r1',board='/tmp/pose-invocation-guard-20261009-r1',completion_sha256=g.sha(e/'completion-review.json'),next='Read INVOCATION-GUARD-RESULTS, ADR_20 and INVOCATION-GUARD-NEXT. New retention/independent persistence works, original CPU source reads kept. New103 stopped at inv11/op192;3 shadows47760 bytes,496 finite noninteger index values in18 blocks equal preceding data-input copy at same offsets. Both later SDK sources equal N1. Only582 fresh638 checked on11 completed calls; failed192 not covered. Next separately observe public producer234 counter before/after192 copying, retain bounded exact snapshots and audit SDK shared UDMA staging/sync; do not infer early read or stale DMA root from pattern alone. No retry this failed run, no cache/BOOT/CMA/math/ready guesses. Long-term/HDMI/zero-copy remain pending.')
    write('next-checkpoint.json',checkpoint)
    active=load('active-checkpoint.json');active.update(status=report['status'],active_stage=None,active_tests=False,services_running=False,SSH_SCP_closed=True,completion_sha256=checkpoint['completion_sha256']);(e/'active-checkpoint.json').write_text(json.dumps(active,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','all_correct_forwards','all_correct_FP32','Host_index_noninteger_values','all_six_persistence_tasks_saved','root_cause_fixed','all_agent_sessions_closed')}))
if __name__=='__main__':main()
