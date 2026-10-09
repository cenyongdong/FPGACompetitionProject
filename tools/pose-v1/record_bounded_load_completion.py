"""Report the executed failed bounded load without creating a passing load gate."""
from pathlib import Path
import json
import mixed_validation_gate as g

def main():
    p=g.ROOT/'tools/pose-v1/evidence/bounded-load-20261009-r2'
    load=lambda name:g.load(p/name)
    host=load('host-check.acceptance.json');three=load('process-three.acceptance.json');failed=load('failed-load.numeric-review.json')
    assert host['Host_cases']==107 and host['CPU_FP32']==59600 and host['registry_records']==12
    assert three['consumed']==4 and three['full_numeric_bitwise'] and failed['consumed']==60 and failed['FP32_verified']==906000
    assert not failed['successful_103_acceptance'] and failed['failed_invocation']==60 and failed['failed_op']==582
    source=load('device-source-readback-analysis.json');gold=load('same-case-source-golden-comparison.json')
    assert source['source_hardware_read'] and source['additional_source_read_bytes']==67200
    assert source['comparisons'][0]['staging_to_round0_changed_FP32']==2096 and source['comparisons'][0]['round0_to_round1_changed_FP32']==0
    assert source['comparisons'][1]['staging_to_round0_changed_FP32']==source['comparisons'][1]['round0_to_round1_changed_FP32']==0
    assert all(x['source_round0_matches_same_case_gold'] and x['source_round1_matches_same_case_gold'] for x in gold['comparisons'])
    video=load('video-failed-prefix/review.json');network=load('network-failed-prefix-r2/review.json')
    assert video['decoded_frames']==419 and network['network_frames']==389
    assert video['missing_completed_sources']==network['missing_completed_sources']==[58,59]
    assert video['uncaptured_sample_tail']==3 and not network['all_sources_present']
    resources=load('resource-review.json');assert resources['status']=='failure_cleanup_identity_kernel_ports_own_processes_checked'
    assert load('ARM-budget-review.json')['status']=='103_budget_104_refusal_and_reaping_verified'
    refs=['build.acceptance.json','build-contract-identities.json','source-policy-review.json','native-budget-review.json','ARM-budget-review.json','Host-source-readback-review.json','native-reference-baseline-review.json','host-check.acceptance.json','process-three.acceptance.json','reference-three-review.json','video-three/review.json','network-three/review.json','failed-load.numeric-review.json','device-source-readback-analysis.json','failed-Scatter582-analysis.json','same-case-source-golden-comparison.json','stale-buffer-pattern-ranking.json','reference-failed-prefix-review.json','video-failed-prefix/review.json','network-failed-prefix-r2/review.json','resource-review.json','sdk-copy-read-mechanism-review.json']
    report=dict(status='bounded103_implemented_Host_three_passed_device_error_capture_triggered_load_failed',
        program_sha256=host['binary_sha256'],package_manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=68,
        Host_cases=107,registry_records=12,CPU_FP32=59600,budget_Native_and_ARM_renders_each=206,
        budget_104_refusal_and_reaping=True,Native_original_33_reference_bitwise=True,
        successful_three_forwards=4,successful_three_FP32=60400,successful_three_encoded=491,successful_three_network_frames=461,
        failed_load_completed_forwards=60,failed_load_FP32_bitwise=906000,all_current_correct_forwards=64,all_current_correct_FP32=966400,
        failed_op=582,failed_invocation=60,failed_frame_id=100060,failed_case='S13_07_304',failed_copy_slot=0,
        staging_NaN_indices=[8,9,10,11],staging_NaN_bits='0xffffffff',staging_changed_FP32=2096,
        original_staging_bytes=33600,actual_error_device_source_read_bytes=67200,source_rounds_bitwise_same=True,
        both_sources_match_same_case_old_gold=True,reads_occur_after_exception=True,root_cause_proven=False,root_cause_fixed=False,
        failed_prefix_video=419,failed_prefix_network=389,failed_prefix_sources=58,missing_completed_video_sources=[58,59],
        failed_prefix_not_acceptance=True,sparse_ARM_references=29,Native_reconstruction_actual_correct_prefix=60,
        source_capture_retained=True,operator_trace_and_extra_query_rows=0,SDK_profiling=False,
        original_103_plan_passed=False,performance_100_measurements_passed=False,strict_5Hz_accepted=False,
        no_automatic_retry=True,compactions=0,BOOT_CMA_SDK_math_frame_protocol_unchanged=True,
        final_kernel_unchanged=True,VPU_abort_streamoffs_success=True,normal_LAST_not_claimed_for_failed_run=True,
        child_reaped=True,network_sources_live=0,Engine_destroyed_after_workers=True,ports_released=True,all_agent_sessions_closed=True,
        MemAvailable_KiB=681088,CmaFree_KiB=26012,
        r1_Native_build_failure_preserved=True,local_failed_network_summary_reader_corrected_without_board_rerun=True,
        review_sha256={name:g.sha(p/name) for name in refs})
    (p/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n')
    checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,
        package='.local/pose-v1-bounded-load/package-20261009-r2',build='.local/pose-v1-build/mixed-20261009-bounded-load-r2',
        board='/tmp/pose-bounded-load-20261009-r2',program_sha256=host['binary_sha256'],completion_sha256=g.sha(p/'completion-review.json'),
        next='Read BOUNDED-LOAD-RESULTS-20261009.md, ADR_18/17 and HOST-STAGING-FAULT-NEXT-20261009.md. Keep failed load and source reads.60 good calls then Scatter582 bad Host slot0; both later device reads exact old same-case gold. No load acceptance/retry. Prepare post-copy owned shadow + Host destination alignment/region metadata and receiver failure accounting; normal copy/waits/math remain. SDK default cross-copy uses temporary/source.read/dest.write; direct Tensor.read alone not proven repair. No cache/BOOT/CMA changes. Await next agreed diagnostic execution; HDMI/30min pending.')
    (p/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
    # Retain the running snapshot as historical, close it explicitly.
    active=load('active-checkpoint.json');active.update(status='completed_with_preserved_load_failure',active_tests=False,services_running=False,completion_sha256=checkpoint['completion_sha256'])
    (p/'active-checkpoint.json').write_text(json.dumps(active,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','all_current_correct_forwards','all_current_correct_FP32','actual_error_device_source_read_bytes','both_sources_match_same_case_old_gold','root_cause_fixed','original_103_plan_passed','all_agent_sessions_closed']},indent=2))

if __name__=='__main__':main()
