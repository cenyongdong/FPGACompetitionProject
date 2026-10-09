"""Review identity, saved failure bytes and cleanup; never emit acceptance."""
from pathlib import Path
import json
import mixed_validation_gate as old
from review_forward_r3_stage import identities,rows,sha
root=old.ROOT;e=root/'tools/pose-v1/evidence/forward-trace-20261009-r3';r=e/'process-three';out=r/'results'
m,b,_=identities(root/'.local/pose-v1-forward-trace/package-20261009-r3',root/'.local/pose-v1-build/mixed-20261009-forward-trace-r3')
returned=old.verify(r);assert (r/'exit.txt').read_text().strip()=='1'
assert sha(r/'pose_live_pipeline_check')==b['binary_sha256'] and sha(r/'pose_display_worker')==b['display_worker_sha256']
assert sha(r/'executed-runner.sh')==sha(root/'tools/pose-v1/run-forward-trace-r3.sh')
assert (r/'dmesg.before.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
pre=old.load(r/'preflight.json');baseline=old.load(e/'host-check/preflight.json')
assert all(pre[k]==baseline[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
old.registry(out/'engine/registry.jsonl');old.fusion_binding_review(out/'engine',old.load(root/'tools/pose-v1/mixed-fusion-baseline.json'))
assert not rows(out/'inference.jsonl') and not rows(out/'timing.jsonl') and not (out/'summary.json').exists()
for name in ('readiness.jsonl','operator-execution.jsonl','monotonic-spans.jsonl'):assert (out/'engine'/name).stat().st_size==0
assert not old.load(out/'engine/sdk-profile-setting.json')['enabled']
params=rows(out/'engine/host-parameters.jsonl');assert len(params)==4 and all(x['loaded_from_real_RAW'] for x in params)
# New actual RAW values are independently checked against the accepted previous deployment.
previous=root/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-one/results'
for op in (188,437,582,649):assert (out/f'engine/op{op}.param1.f32').read_bytes()==(previous/f'op{op}.param1.f32').read_bytes()
meta=old.load(out/'failed-host-inputs/failure.json');assert meta['op_id']==188 and meta['invocation']==0 and meta['frame_id']==100000 and not meta['device_read']
assert not (out/'failed-host-inputs/capture-error.txt').exists()
data=old.load(e/'failed-TopK188-input-analysis.json');assert data['inputs'][0]['NaN']==1
block=old.load(e/'TopK188-block-comparison.json');assert block['changed_FP32']==96 and block['unchanged_FP32']==84
assert 'CPU_CANDIDATE[finite]: NaN/Inf input is prohibited' in (r/'stderr.log').read_text()
parent=rows(out/'display/parent.jsonl');assert parent[-1]['event']=='error_cleanup_reaped'
streamoffs=[x for x in rows(out/'encoder/events.jsonl') if x['event']=='abort_streamoff'];assert len(streamoffs)==2 and all(x['result']==0 for x in streamoffs)
assert rows(out/'network/events.jsonl')[-1]['sources_live']==0
assert [x['event'] for x in rows(out/'lifecycle.jsonl')]==['Engine_created','workers_joined','Engine_destroyed']
final=e/'final-audit';old.verify(final);old.verify(e/'resources-before-three')
fp=old.load(final/'preflight.json');assert all(fp[k]==pre[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
listeners=(final/'listeners.txt').read_text();assert ':8554' not in listeners and ':39001' not in listeners
assert not any('pose_live_pipeline_check' in x or 'pose_display_worker' in x for x in (final/'processes.txt').read_text().splitlines())
report=dict(status='r3_first_forward_rejected_saved_periodic_Host_data_blocks_root_cause_pending',returned_files=returned,program_sha256=b['binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],Host_cases=107,CPU_FP32=59600,failure_capture_probe_passed=True,full_model_forward_completed=0,failed_op=188,failed_invocation=0,failed_transport_id=100000,owned_Host_input_bytes=720,NaN_index=11,NaN_bits='0xffffffff',changed_FP32_against_same_CSI_r6=96,unchanged_FP32=84,diagnostic_frames=0,timing_frames=0,extra_readiness_queries=False,SDK_profiling=False,source_device_read_performed=False,additional_query_only_hypothesis_insufficient=True,root_cause_proven=False,frame_protocol_unchanged=True,dmesg_unchanged=True,child_reaped=True,VPU_streamoff_success=True,network_sources_live=0,ports_released=True,Engine_destroyed_after_workers=True,compactions=0,BOOT_SDK_model_unchanged=True,all_sessions_closed=True,five_Hz_trace_executed=False,long_load_executed=False,phase_label_note='Capture occurs after CPU adapter exception; this finite validation rejection precedes the TopK kernel.')
(e/'failure-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
