"""Archive separate-process feasibility without rounding the strict5Hz threshold."""
import hashlib,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as old

root=old.ROOT;directory=root/'tools/pose-v1/evidence/display-process-20261008-r1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=('process-three','measure-2hz','measure-5hz');host=load(directory/'host-check.acceptance.json');stages=[load(directory/(name+'.acceptance.json')) for name in names]
video=[load(directory/(name+'-video-review/review.json')) for name in names];network=[load(directory/(name+'-network-review/review.json')) for name in names]
assert host['Host_cases']==107 and host['CPU_FP32']==59600
assert all(s['full_numeric_bitwise'] and s['display_subprocess'] and s['child_reaped'] and s['binary_sha256']==host['binary_sha256'] for s in stages)
assert all(n['all_sources_present'] and n['all_pixels_equal_current_capture'] and n['actual_RTP_capture_PTS'] for n in network)
assert [s['consumed'] for s in stages]==[4,33,33] and all(s['overwritten']==0 for s in stages)
comp=directory/'compaction-once';assert old.verify(comp)==13;action=load(comp/'action.json');assert action['requested_compactions']==1 and action['status']=='single_compaction_completed' and not action['drop_caches'] and not action['reboot']
def ordinary(phase):
    total=0
    for line in (comp/(phase+'.pagetypeinfo.txt')).read_text().splitlines():
        if 'DMA32, type' not in line or any(x in line for x in ('CMA','Isolate')):continue
        values=[int(x) for x in line.split()[-11:]];total+=sum(values[i]*(1<<(i-7)) for i in range(7,11))
    return total
final=directory/'final-state';assert old.verify(final)==8
ports=(final/'ports.txt').read_text();assert all(':'+str(p)+' ' not in ports for p in (8554,39001))
processes=(final/'processes.txt').read_text();assert not any('pose_display_worker' in x or 'pose_live_pipeline_check' in x for x in processes.splitlines())
assert (final/'dmesg.log').read_bytes()==(directory/'measure-5hz/dmesg.after.log').read_bytes()
b=load(root/'.local/pose-v1-build/mixed-20261008-display-process-r1/build-result.json');oldload=load(root/'tools/pose-v1/evidence/system-timing-20261008-r2/measure-5hz.acceptance.json');load5=stages[-1]
timing=rows(directory/'measure-5hz/results/timing.jsonl');display=rows(directory/'measure-5hz/results/display-timing.jsonl');used=timing[3:]
published=[(t['published_ns']-t['arrived_ns'])/1e6 for t in used];slow=max(timing,key=lambda x:x['forward_ms'])
report=dict(status='independent_display_process_feasibility_passed_strict5Hz_pending',program_sha256=host['binary_sha256'],display_worker_sha256=b['display_worker_sha256'],manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=57,Host_cases=107,CPU_FP32=59600,IPC_selftest_bytes=6912000,IPC_rejections=9,forwards=sum(s['consumed'] for s in stages),input_scores_poses_FP32=sum(s['consumed']*15100 for s in stages),all_numeric_bitwise=True,encoded=sum(s['encoded'] for s in stages),network_frames=sum(n['network_frames'] for n in network),joint_checks=sum(v['joint_visibility_checks'] for v in video),sources_actual_PTS_pixels_verified=True,display_in_separate_executable=True,child_SDK_VPU_descriptors=False,normal_children_reaped=3,main_Engine_owner_preserved=True,load5_sent=33,load5_consumed=33,load5_overwritten=0,load5_measurements=30,actual_update_Hz=load5['new_pose_completion_interval_Hz'],old_update_Hz=oldload['new_pose_completion_interval_Hz'],update_change_percent=(load5['new_pose_completion_interval_Hz']/oldload['new_pose_completion_interval_Hz']-1)*100,picture_P95_ms=load5['metrics']['arrival_to_picture_ms']['P95'],parent_owned_picture_P95_ms=float(np.percentile(published,95)),old_picture_P95_ms=oldload['metrics']['arrival_to_picture_ms']['P95'],IPC_reply_mean_ms=load5['metrics']['IPC_reply_ms']['mean'],parent_forward_display_overlap=load5['parent_forward_display_overlap'],forward_outlier={k:slow[k] for k in ('invocation','sequence','case','process_ms','forward_ms')},outlier_cause='unproven; intra-forward trace disabled in low-log baseline',strict5Hz_verified=False,nominal5Hz_input_all_results_correct=True,HDMI_verified=False,long_run_verified=False,compactions_this_batch=1,compaction_ms=action['elapsed_ns']/1e6,ordinary512KiB_units_before=ordinary('before'),ordinary512KiB_units_after=ordinary('after'),CMA_BOOT_model_RAW_SDK_math_frame_cookie_unchanged=True,new_dependencies=False,services_running=False,SSH_SCP_closed=True,review_adapter_sha256=sha(root/'tools/pose-v1/review_display_stage.py'),acceptance_sha256={name:sha(directory/(name+'.acceptance.json')) for name in ('build','host-check')+names})
assert report['actual_update_Hz']<5 and report['parent_forward_display_overlap']==32
p=directory/'completion-review.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n')
checkpoint=dict(status='separate_display_process_feasibility_done_strict5Hz_jitter_and_reliability_pending',user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,build='.local/pose-v1-build/mixed-20261008-display-process-r1',package='.local/pose-v1-display-process/package-20261008-r1',board='/tmp/pose-display-process-20261008-r1',program_sha256=host['binary_sha256'],display_worker_sha256=b['display_worker_sha256'],completion_sha256=sha(p),this_batch_compaction_authorization_consumed=True,strict5Hz_verified=False,next='Read DISPLAY-PROCESS-RESULTS-20261008.md and DISPLAY-PROCESS-NEXT-20261008.md. Preserve separate executable and main-owned Engine. Investigate forward invocation28 spike with bounded single-clock trace before claiming strict5Hz; longer finite/load then overload/stream outage/cleanup. Match VPU allocation path for startup reliability; no automatic compaction/reboot/cache/BOOT/CMA/math/sync changes. HDMI and30min remain pending.')
(directory/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n');print(json.dumps(report,indent=2))
