"""Freeze scoped recovery success; preserve the unreproduced earlier failure."""
import hashlib,json
from pathlib import Path
import mixed_validation_gate as old
root=old.ROOT;directory=root/'tools/pose-v1/evidence/tcp-presaved-20261008-r1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
host=load(directory/'host-check.acceptance.json');assert host['Host_cases']==107
stages=[load(directory/(name+'.acceptance.json')) for name in ('live-three','live-27')]
assert all(s['complete_online_stage_verified'] and s['TCP_input_independent_mapping_verified'] and s['binary_sha256']==host['binary_sha256'] for s in stages)
numeric=[load(directory/(name+'.numeric-analysis.json')) for name in ('live-three','live-27')]
assert all(n['all_bitwise_reference'] and n['input_all_bitwise_reference'] for n in numeric) and sum(n['frames'] for n in numeric)==32
old.verify(directory/'compaction-once');action=load(directory/'compaction-once/action.json')
assert action['status']=='single_compaction_completed' and action['requested_compactions']==1 and not action['drop_caches'] and not action['reboot']
def ordinary_units(phase):
    total=0
    for line in (directory/'compaction-once'/(phase+'.pagetypeinfo.txt')).read_text().splitlines():
        if 'DMA32, type' not in line or any(t in line for t in ('CMA','Isolate')):continue
        values=[int(x) for x in line.split()[-11:]]
        total+=sum(values[order]*(1<<(order-7)) for order in range(7,11))
    return total
report=dict(status='save_before_gate_and_single_compaction_finite_pipeline_passed',program_sha256=host['binary_sha256'],manifest_sha256=host['package_manifest_sha256'],package_files=403,build_sources=44,Host_cases=107,CPU_FP32=59600,forward_calls=32,input_scores_poses_FP32=483200,all_presaved_before_gate=True,all_outputs_bitwise_old_board=True,previous_failing_case_now_bitwise=True,old_failure_reproduced=False,fixed_point_truncation_cause_proven=False,old_failure_root_cause_resolved=False,encoded_frames=sum(s['encoded_frames'] for s in stages),network_frames=sum(s['network_frames'] for s in stages),joint_checks=sum(s['video_joint_visibility_checks'] for s in stages),actual_PTS_sources_pixels_verified=True,compactions=1,compaction_ms=action['elapsed_ns']/1e6,ordinary_512KiB_units_before=ordinary_units('before'),ordinary_512KiB_units_after=ordinary_units('after'),independent_VPU_process_starts_passed=2,model_SDK_BOOT_CMA_unchanged=True,whole_system_5Hz_verified=False,long_run_verified=False,permanent_CMA_driver_solution=False,HDMI_verified=False,local_review_started_before_transfer_complete=True,local_review_corrected_no_hardware_retry=True,services_running=False,SSH_SFTP_closed=True,acceptance_sha256={name:sha(directory/(name+'.acceptance.json')) for name in ('host-check','live-three','live-27')})
p=directory/'completion-review.json';assert not p.exists();p.write_bytes((json.dumps(report,indent=2)+'\n').encode())
checkpoint=dict(status='finite_TCP_guarded_pipeline_passed_ready_for_bounded_system_timing',user_paused=False,active_tests=False,services_running=False,SSH_SFTP_closed=True,program_sha256=host['binary_sha256'],build='.local/pose-v1-build/mixed-20261008-tcp-presaved-r1',package='.local/pose-v1-tcp-presaved/package-20261008-r1',board='/tmp/pose-v1-tcp-presaved-20261008-r1',report_sha256=sha(p),compaction_once_already_consumed=True,old_mismatch_cause_unproven=True,next='Read PRESAVED-RESULTS-20261008.md and WHOLE-SYSTEM-NEXT-20261008.md. Separate bounded low-log timing from save-first diagnostic oracle; retain all model/SDK/frame/encoder protocols. CMA driver solution requires matched allocation/MMU/DMA design, not larger reservation alone. No automatic repeated compaction/reboot or performance acceptance.')
(directory/'next-checkpoint.json').write_bytes((json.dumps(checkpoint,indent=2)+'\n').encode());print(json.dumps(report,indent=2))
