"""Archive actual passes and unresolved stops; never synthesize a27-window gate."""
import hashlib,json
from pathlib import Path
import mixed_validation_gate as old
root=old.ROOT;base=root/'tools/pose-v1/evidence';directory=base/'tcp-evidence-20261008-r1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
guarded=[load(base/'guarded-live-20261008-r1'/(s+'.acceptance.json')) for s in ('host-check','live-three','live-27')]
assert all(s['status']=='live_stage_passed' for s in guarded)
three=load(base/'tcp-live-20261008-r1-controlled/live-three.acceptance.json')
assert three['complete_online_stage_verified'] and three['TCP_input_independent_mapping_verified']
host=load(directory/'host-check.acceptance.json');assert host['Host_cases']==107 and host['failure_capture_contracts']
r=directory/'live-three';count=old.verify(r);before=(r/'dmesg.before.log').read_text();after=(r/'dmesg.after.log').read_text()
assert (r/'exit.txt').read_text().strip()=='1' and 'STOP: poll device failure' in (r/'stderr.log').read_text()
assert 'page allocation failure: order:7, mode:0x10dc0' in after[len(before):] and 'mvx_mmu_alloc_contiguous_pages' in after[len(before):]
assert '"event":"Engine_created"' not in (r/'results/lifecycle.jsonl').read_text() and not (r/'results/inference.jsonl').read_bytes()
snapshot=directory/'memory-failure-snapshot';old.verify(snapshot)
report=dict(status='guarded_passed_TCP_three_passed_TCP27_unresolved',guarded=dict(program_sha256=guarded[0]['binary_sha256'],Host_cases=107,full_correct_forwards=sum(x['full_correct_forwards'] for x in guarded[1:]),encoded_frames=sum(x['encoded_frames'] for x in guarded[1:]),network_frames=sum(x['network_frames'] for x in guarded[1:]),all_sources_PTS_pixels_verified=True),TCP_three=dict(program_sha256=three['binary_sha256'],complete_windows=4,encoded_frames=three['encoded_frames'],network_frames=three['network_frames'],all_outputs_PTS_pixels_verified=True),TCP27=dict(status='failed',received_windows=6,complete_correct_forwards=5,failed_case='S12_48_349',actual_rejected_output_missing=True,root_cause='unproven'),diagnostic=dict(program_sha256=host['binary_sha256'],manifest_sha256=host['package_manifest_sha256'],Host_cases=107,CPU_output_FP32=59600,Native_ARM_failure_capture_contracts=True,hardware_result='VPU_first_start_order7_allocation_failure',returned_hashed_files=count,model_forwards=0,SDK_Engine_initialized=False),ordinary_high_order_failure=dict(order=7,bytes=524288,GFP='GFP_KERNEL|__GFP_NORETRY|__GFP_ZERO',kernel_snapshot_CmaFree_kB=130604,at_failure_512KiB_and_larger_blocks_CMA_only=True,post_cleanup_order7_Unmovable_blocks=5,post_cleanup_not_a_retry_gate=True),whole_system_5Hz_verified=False,long_run_verified=False,HDMI_verified=False,compaction_cache_clear_reboot_BOOT_CMA_changes=False,services_running=False,SSH_SFTP_closed=True)
target=directory/'progress-review.json';assert not target.exists();target.write_bytes((json.dumps(report,indent=2)+'\n').encode())
checkpoint=dict(status='hardware_testing_stopped_at_VPU_allocation_failure_TCP_output_diagnostic_pending',user_paused=False,active_test=False,services_running=False,SSH_SFTP_closed=True,build='.local/pose-v1-build/mixed-20261008-tcp-evidence-r1',package='.local/pose-v1-tcp-evidence/package-20261008-r1',board='/tmp/pose-v1-tcp-evidence-20261008-r1',program_sha256=host['binary_sha256'],last_accepted_stage='host-check',last_hardware_stage='live-three exit1 before Engine',report_sha256=sha(target),next='Read TCP-INTEGRATION-RESULTS-20261008.md and TCP-RECOVERY-NEXT-20261008.md. Restore first-start conditions only with explicit user choice; new directory three source regression before27 failure-only capture. Do not rerun existing failure directories or start performance.',no_automatic_retry_compaction_cache_clear_reboot_or_BOOT_CMA_change=True)
(directory/'next-checkpoint.json').write_bytes((json.dumps(checkpoint,indent=2)+'\n').encode());print(json.dumps(report,indent=2))
