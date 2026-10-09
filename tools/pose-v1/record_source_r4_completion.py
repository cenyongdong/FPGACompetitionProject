"""Separate implementation/regression success from unobserved hardware error capture."""
from pathlib import Path
import json
import mixed_validation_gate as old
root=old.ROOT;e=root/'tools/pose-v1/evidence/source-readback-20261009-r4'
host=old.load(e/'host-check.acceptance.json');local=old.load(e/'local-result-review.json');numeric=old.load(e/'process-three-stream-ready.numeric-review.json');video=old.load(e/'video-stream-ready/review.json');network=old.load(e/'network-stream-ready/review.json')
assert host['CPU_FP32']==59600 and numeric['full_numeric_bitwise'] and numeric['consumed']==4 and local['full_FP32_bitwise']==60400
r=e/'process-three-stream-ready';out=r/'results';assert not (out/'failed-host-inputs').exists()
assert numeric['encoded']==video['decoded_frames']==499 and network['network_frames']==469 and network['all_sources_present'] and network['new_inference_sources']==4
assert video['joint_visibility_checks']==2730
sourceProbe=old.load(e/'Host-source-probe-review.json');assert sourceProbe['additional_source_read_bytes']==94080 and not sourceProbe['source_hardware_read']
assert all(x['staging_to_round0_changed_FP32']==x['staging_to_round1_changed_FP32']==x['round0_to_round1_changed_FP32']==0 for x in sourceProbe['comparisons'])
timeout=e/'process-three';old.verify(timeout);assert (timeout/'exit.txt').read_text().strip()=='1'
assert 'Timing complete window exceeds5s' in (timeout/'stderr.log').read_text() and not (timeout/'results/inference.jsonl').read_bytes()
assert not (timeout/'results/failed-host-inputs').exists() and (timeout/'dmesg.before.log').read_bytes()==(timeout/'dmesg.after.log').read_bytes()
final=e/'final-audit-stream-ready';old.verify(final)
pre=old.load(r/'preflight.json');fp=old.load(final/'preflight.json');assert all(pre[k]==fp[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
assert (final/'dmesg.log').read_bytes()==(r/'dmesg.after.log').read_bytes()
assert ':8554' not in (final/'listeners.txt').read_text() and ':39001' not in (final/'listeners.txt').read_text()
assert not any('pose_live_pipeline_check' in x or 'pose_display_worker' in x for x in (final/'processes.txt').read_text().splitlines())
mechanism=root/'.local/pose-v1-source-readback/sdk-mechanism'
assert old.sha(mechanism/'libicraft_xrt.so')=='a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'
sdkReport=dict(status='matching_ARM_binary_entry_route_audit_only',library_sha256=old.sha(mechanism/'libicraft_xrt.so'),library_matches_board=True,Tensor_copyFrom_address='0x682f8',Tensor_copyFrom_size='0x70',Tensor_read_address='0x6bf90',Tensor_read_size='0x410',copy_route='Tensor::copyFrom -> MemChunk::copyFrom -> MemRegion::memcpy',read_route='Tensor::read -> MemChunk::read -> MemRegion::read',concrete_region_DMA_cache_implementation_fully_proven=False,root_cause_proven=False,window_sha256={p.name:old.sha(p) for p in mechanism.glob('*.txt')},note='Disassembly windows may include neighboring functions; entry sizes and call sites define this limited conclusion.')
(e/'sdk-mechanism-review.json').write_text(json.dumps(sdkReport,indent=2)+'\n')
report=dict(status='r4_source_capture_implemented_Host_and_bounded_live_regression_passed_fault_not_reproduced',program_sha256=host['binary_sha256'],package_manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=63,Host_cases=107,CPU_FP32=59600,Host_probe_source_read_bytes=94080,source_Host_rounds_bitwise=True,model_forwards=8,full_model_FP32_bitwise=120800,local_encoded_first=495,live_encoded=499,live_network_frames=469,live_joint_checks=2730,Host_probe_source_hardware_reads=False,model_source_readback_triggered=False,actual_model_error_source_hardware_reads=0,source_fault_reproduced=False,root_cause_fixed=False,control_timeout_preserved=True,control_404_preserved=True,first_URI_ready_control_fixed=True,board_binary_package_math_thresholds_unchanged_across_control_variants=True,compactions=0,no_cache_clear_reboot_BOOT_CMA_changes=True,final_resources_released=True,all_sessions_closed=True,performance_5Hz_verified=False,long_103_executed=False)
(e/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n')
checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-source-readback/package-20261009-r4',build='.local/pose-v1-build/mixed-20261009-source-readback-r4',board='/tmp/pose-source-readback-20261009-r4-stream-ready',program_sha256=host['binary_sha256'],completion_sha256=old.sha(e/'completion-review.json'),next='Read SOURCE-READBACK-R4-RESULTS-20261009.md and ADR_17. Preserve R3 bad blocks, control failures and R4 captures. No error occurred in two four-frame contexts; actual device-source error reads remain unverified. Keep capture for the next agreed bounded coverage or natural startup, review exact region DMA/cache implementation; do not force failures/reboot/cache or treat this as root-cause repair. Strict5Hz/old spike/103/HDMI/30min pending.')
(e/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n');print(json.dumps(report,indent=2))
