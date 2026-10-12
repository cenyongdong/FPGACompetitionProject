"""Archive reviewed invocation integration outcomes; no device operations."""
import json,hashlib
from pathlib import Path
import mixed_validation_gate as g
def main():
    e=g.ROOT/'tools/pose-v1/evidence/invocation-guard-20261009-r1'
    def load(name):return g.load(e/name)
    def write(name,obj):
        p=e/name;assert not p.exists();p.write_text(json.dumps(obj,indent=2)+'\n')
    host=load('host-check.acceptance.json');three=load('process-three.acceptance.json');full=load('load-103.numeric-review.json')
    assert host['Host_cases']==107 and host['registry_records']==12 and host['CPU_FP32']==59600
    assert three['consumed']==4 and full['consumed']==103 and full['measured_consumed']==100 and not full['overwritten'] and full['full_numeric_bitwise']
    assert load('host.integration.json')['status']=='Host_lifetime_and_independent_persistence_passed'
    assert load('load.integration.json')['calls']==103 and load('load.shadow.json')['snapshot_rows']==824
    media={}
    for label in ('three','103'):
        v=load('video-'+label+'/review.json');n=load('network-'+label+'/review.json');assert n['all_sources_present']
        media[label]=dict(encoded=v['decoded_frames'],network=n['network_frames'],sources=n['new_inference_sources'],joint_checks=v['joint_visibility_checks'])
    assert load('resource-review.json')['kernel_unchanged'] and load('resource-review.json')['compactions']==0
    refs=['build.acceptance.json','build.integration.json','host-check.acceptance.json','host.integration.json','process-three.acceptance.json','three.integration.json','three.shadow.json','reference-three-review.json','video-three/review.json','network-three/review.json','load-103.numeric-review.json','load.integration.json','load.shadow.json','reference-103-review.json','video-103/review.json','network-103/review.json','resource-review.json']
    report=dict(status='invocation_retention_and_independent_persistence_complete_bounded_regression_passed',program_sha256=host['binary_sha256'],manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=74,Host_cases=107,registry_records=12,Host_FP32=59600,SDK_free_refusals_Native_ARM_each=12,finite_Host_probe_bytes=47040,old_Host_source_read_bytes=94080,normal_frame_inputs=8,normal_frame_bytes=115360,all_correct_forwards=107,all_correct_FP32=1615700,load_forwards=103,load_full_FP32=1555300,media=media,normal_device_reads_added=0,hardware_failure_capture_triggered=False,all_tasks_independent=True,root_cause_fixed=False,compactions=0,cache_clear=False,BOOT_SDK_model_math_changed=False,pose_completion_Hz=full['new_pose_completion_interval_Hz'],picture_P95_ms=full['metrics']['arrival_to_picture_ms']['P95'],strict_short_term_5Hz=full['whole_5Hz_threshold_met'],long_term_passed=False,HDMI_passed=False,zero_copy=False,all_agent_sessions_closed=True,evidence_sha256={name:g.sha(e/name) for name in refs})
    write('completion-review.json',report)
    gate=dict(full);gate['integration_and_media_reviewed']=True;write('load-103.acceptance.json',gate)
    checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,package='.local/pose-v1-invocation-guard/package-20261009-r1',build='.local/pose-v1-build/mixed-20261009-invocation-guard-r1',board='/tmp/pose-invocation-guard-20261009-r1',completion_sha256=g.sha(e/'completion-review.json'),next='Read INVOCATION-GUARD-RESULTS and ADR_20. Keep original CPU exception staging/two late source reads and frame-owned postcopy evidence until complete output gate. New107 hardware calls passed but old finite mismatch root remains unproven; no hardware failure shadow triggered. Next plan independent finite starts with same frozen retention candidate, stop first error, compare preserved8 inputs to same-CSI N1. If inputs equal but final result differs, design public Engine-owned output read evidence separately; no private access, map/cache/ready guesses or failed-run retry. Long-term/HDMI/zero-copy pending.')
    write('next-checkpoint.json',checkpoint)
    active=load('active-checkpoint.json');active.update(status=report['status'],active_stage=None,active_tests=False,services_running=False,SSH_SCP_closed=True,completion_sha256=checkpoint['completion_sha256'])
    (e/'active-checkpoint.json').write_text(json.dumps(active,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','all_correct_forwards','all_correct_FP32','pose_completion_Hz','strict_short_term_5Hz','root_cause_fixed')}))
if __name__=='__main__':main()
