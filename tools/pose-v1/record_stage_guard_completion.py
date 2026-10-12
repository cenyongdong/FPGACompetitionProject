"""Bind independently reviewed stage-guard outcomes; never starts devices."""
import json,hashlib,shutil
from pathlib import Path
import mixed_validation_gate as g
def main():
    e=g.ROOT/'tools/pose-v1/evidence/stage-guard-20261009-r1'
    def load(name):return json.loads((e/name).read_text(encoding='utf-8-sig'))
    for name in ('load-103.acceptance.json','completion-review.json','next-checkpoint.json'):assert not (e/name).exists()
    host=load('host-check.acceptance.json');three=load('process-three.acceptance.json');load103=load('load-103.numeric-review.json')
    assert host['Host_cases']==107 and host['CPU_FP32']==59600 and host['registry_records']==12
    assert three['consumed']==4 and load103['consumed']==103 and load103['measured_consumed']==100 and load103['overwritten']==0 and load103['full_numeric_bitwise']
    observations=load('load-shadow-review.json');assert observations['snapshot_rows']==824 and observations['fresh_sync_rows']==103 and observations['sync_actual_waited']==0
    for suffix,encoded,network in [('three',494,464),('103',592,562)]:
        assert load('video-'+suffix+'/review.json')['decoded_frames']==encoded
        assert load('network-'+suffix+'/review.json')['network_frames']==network and load('network-'+suffix+'/review.json')['all_sources_present']
    assert load('resource-review.json')['kernel_unchanged'] and load('resource-review.json')['compactions']==0
    report=dict(status='stage_guard_Host_three_103_complete_regression_passed_root_unproven',
        program_sha256=host['binary_sha256'],package_manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=71,
        Host_cases=107,registry_records=12,CPU_FP32=59600,Native_ARM_refusals_each=11,Host_probe_shadow_bytes=47040,Host_source_read_bytes=94080,
        three_forwards=4,three_FP32=60400,three_encoded=494,three_network=464,
        load_forwards=103,load_FP32=1555300,all_correct_forwards=107,all_correct_FP32=1615700,
        load_measured_calls=100,load_received_consumed_returned=103,overwritten=0,
        load_encoded=592,load_network=562,load_inference_sources=103,load_joint_checks=4158,
        Native_references=103,ARM_sparse_references=29,
        all_new_sync_checks=107,all_first_counter=638,all_final_counter=638,actual_extra_waits=0,
        load_snapshot_rows=824,load_metadata_rows=927,all_alignment_capacity_checks_passed=True,
        normal_shadow_bytes_persisted=False,exception_Host_snapshot_two_source_reads_retained=True,actual_device_error_reads_triggered=False,
        first_sample_repeat_and_27_sources_bitwise=True,
        bounded_pose_completion_Hz=load103['new_pose_completion_interval_Hz'],bounded_picture_P95_ms=load103['metrics']['arrival_to_picture_ms']['P95'],
        bounded_5Hz_existing_threshold_met=load103['whole_5Hz_threshold_met'],permanent_5Hz_reliability_accepted=False,long_term_tested=False,
        root_cause_proven=False,root_cause_fixed=False,premature_read_hypothesis_proven=False,DMA_cache_fence_proven=False,zero_copy=False,
        compactions=0,drop_caches=False,reboot=False,BOOT_CMA_SDK_model_RAW_math_frame_protocol_unchanged=True,
        child_reaped=True,VPU_LAST_and_buffers_returned=True,network_sources_live=0,Engine_destroyed_after_workers=True,
        kernel_unchanged=True,ports_released=True,all_agent_sessions_closed=True,
        final_MemAvailable_KiB=load('resource-review.json')['MemAvailable'],final_CmaFree_KiB=load('resource-review.json')['CmaFree'])
    names=['build.acceptance.json','build-contract-identities.json','source-policy-review.json','SDK-sync-interface-review.json','native-stage-review.json','host-check.acceptance.json','Host-shadow-review.json','process-three.acceptance.json','three-shadow-review.json','reference-three-review.json','video-three/review.json','network-three/review.json','load-103.numeric-review.json','load-shadow-review.json','observed-sync-and-shadow-review.json','reference-103-review.json','video-103/review.json','network-103/review.json','resource-review.json']
    report['review_sha256']={name:g.sha(e/name) for name in names}
    shutil.copyfile(e/'load-103.numeric-review.json',e/'load-103.acceptance.json')
    (e/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,
        package='.local/pose-v1-stage-guard/package-20261009-r1',build='.local/pose-v1-build/mixed-20261009-stage-guard-r1',board='/tmp/pose-stage-guard-20261009-r1',
        completion_sha256=g.sha(e/'completion-review.json'),program_sha256=host['binary_sha256'],
        next='Read STAGE-GUARD-RESULTS-20261009.md and ADR_19/17. Host, complete three and new103 passed. All107 new counter checks initially638, no actual additional wait. Keep post-copy shadow/metadata and old error staging/two late source reads. Do not infer permanent repair or DMA fence. Bounded 100-call5.000193Hz only, tiny margin, HDMI/long-term/zero-copy pending. Next separate first-start/longer regression design from SDK copy-coherence/validated mapping audit; no failed-run retry/cache/BOOT/CMA change.')
    (e/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    active=load('active-checkpoint.json');active.update(status=report['status'],active_stage=None,active_tests=False,services_running=False,completion_sha256=checkpoint['completion_sha256']);(e/'active-checkpoint.json').write_text(json.dumps(active,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','all_correct_forwards','all_correct_FP32','actual_extra_waits','root_cause_fixed','bounded_pose_completion_Hz','all_agent_sessions_closed']},indent=2))
if __name__=='__main__':main()
