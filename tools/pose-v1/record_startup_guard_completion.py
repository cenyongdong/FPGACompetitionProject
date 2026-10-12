"""Review resources, partial failure and independent evidence prototype; no devices."""
import json,re,hashlib
from pathlib import Path
import mixed_validation_gate as g
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def units(path):
    free=path.read_text().split('Number of blocks')[0];counts={}
    for name,values in re.findall(r'type\s+(\w+)\s+([0-9 ]+)',free):
        numbers=list(map(int,values.split()));assert len(numbers)==11
        counts[name]=sum(numbers[i]*(1<<(i-7)) for i in range(7,11))
    return sum(v for k,v in counts.items() if k not in ('CMA','Isolate'))
def main():
    e=g.ROOT/'tools/pose-v1/evidence/startup-guard-20261009-r1';assert not (e/'completion-review.json').exists()
    baseline=load(e/'baseline-identities.json');first=load(e/'start-1.numeric-review.json');failed=load(e/'start-2.failure-review.json')
    assert first['consumed']==103 and first['overwritten']==0 and first['full_numeric_bitwise'] and not first['whole_5Hz_threshold_met']
    assert failed['correct_prefix_calls']==37 and failed['poses_changed_FP32']==652 and not failed['all_actual_pose_rows_exist_in_reference'] and failed['best_pose_max_abs']==0
    assert load(e/'video-start-1/review.json')['decoded_frames']==593 and load(e/'network-start-1/review.json')['network_frames']==563
    assert load(e/'video-failed-2/review.json')['decoded_frames']==385 and load(e/'network-failed-2/review.json')['network_frames']==355
    firstRoot=e/'start-1';secondRoot=e/'start-2';final=e/'invocation-arm-r2/final-audit'
    basePre=load(firstRoot/'run-load-103/preflight.json');lastPre=load(final/'preflight.json')
    assert all(basePre[k]==lastPre[k] for k in ('boot_files','libraries','SDK_packages','fpga_state'))
    dmesg=(firstRoot/'resources-before/dmesg').read_bytes()
    assert dmesg==(firstRoot/'resources-after/dmesg').read_bytes()==(secondRoot/'resources-after-failure/dmesg').read_bytes()==(final/'dmesg').read_bytes()
    ports=(final/'ports').read_text();assert ':39001 ' not in ports and ':8554 ' not in ports
    assert not re.search(r'^\s*\d+\s+pose_', (final/'processes').read_text(),re.M)
    action=load(secondRoot/'compaction-before-start/action.json');assert action['requested_compactions']==1 and action['status']=='single_compaction_completed' and not action['drop_caches'] and not action['reboot']
    before=units(secondRoot/'compaction-before-start/before.pagetypeinfo.txt');after=units(secondRoot/'compaction-before-start/after.pagetypeinfo.txt')
    proto=load(e/'invocation-evidence-review.json');assert proto['refusals_each']==12 and not proto['main_inference_integrated'] and not proto['new_NPU_tests']
    resources=dict(status='failure_cleanup_and_SDK_free_probe_final_identity_kernel_ports_verified',BOOT_SDK_unchanged=True,kernel_unchanged=True,ports_released=True,own_processes_released=True,
        compactions=1,compaction_ns=action['elapsed_ns'],non_CMA_512KiB_units_before=before,non_CMA_512KiB_units_after=after,
        final_memory={k:int(v) for k,v in re.findall(r'^(MemAvailable|CmaFree):\s+(\d+)',(final/'meminfo').read_text(),re.M)},
        files_sha256={str(p.relative_to(e)):g.sha(p) for folder in (firstRoot/'resources-before',firstRoot/'resources-after',secondRoot/'resources-predecision',secondRoot/'compaction-before-start',secondRoot/'resources-before',secondRoot/'resources-after-failure',final) for p in folder.rglob('*') if p.is_file()})
    (e/'resource-review.json').write_text(json.dumps(resources,indent=2)+'\n',encoding='utf-8')
    reviews=['baseline-identities.json','start-1.numeric-review.json','start-1.shadow-review.json','video-start-1/review.json','network-start-1/review.json','start-2.failure-review.json','video-failed-2/review.json','network-failed-2/review.json','invocation-evidence-review.json','Host-producer-dependency-review.json','resource-review.json']
    sdkFiles=[p for p in e.iterdir() if p.is_file() and p.suffix=='.txt']
    sdk=dict(status='matched_ARM_interfaces_and_function_ranges_read_only_audited',XRT_sha256='a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96',AXI_sha256='d55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178',CacheSyncHost_Linux_read_write_memcpy=True,UDMA_read_sync_attribute_path=True,PLDDR_public_CPTR_mapping_verified=False,GP_maps_are_register_evidence=True,agent_direct_register_or_dev_mem_access=False,zero_copy_executed=False,artifact_sha256={p.name:g.sha(p) for p in sdkFiles})
    (e/'SDK-mapping-review.json').write_text(json.dumps(sdk,indent=2)+'\n',encoding='utf-8');reviews.append('SDK-mapping-review.json')
    report=dict(status='independent_start1_passed_start2_finite_pose_mismatch_start3_stopped',program_sha256=baseline['program_sha256'],manifest_sha256=baseline['manifest_sha256'],starts_planned=3,starts_executed=2,start3_executed=False,Host_reused=True,new_main_build=False,
        correct_complete_forwards=140,correct_complete_FP32=2114000,returned_forwards=141,failed_returned_forwards=1,
        start1_forwards=103,start1_encoded=593,start1_network=563,start1_Hz=first['new_pose_completion_interval_Hz'],strict_5Hz_passed=False,
        failed_case='S21_19_319',failed_invocation=37,failed_frame=100037,failed_before_forward=0,failed_completed_layers=745,failed_input_and_scores_bitwise=True,failed_poses_finite=True,failed_pose_changed_FP32=652,failed_pose_max_abs=0.5078125,changed_candidate_rows=35,best_candidate_and_pose_bitwise=True,simple_candidate_row_permutation_proven=False,
        failed_received=39,failed_consumed=38,failed_returned=38,failed_unconsumed=1,sender_successful_calls=40,sender_not_ACK=True,
        failed_presaved_results=38,failed_correct_inference_rows=37,failed_timing_rows=38,
        failed_copy_metadata_saved=False,failed_ARM_references_saved=False,failed_error_only_source_reads=0,
        failed_capture_images=385,failed_network=355,failed_video_sources=35,missing_correct_sources=[35,36],uncaptured_sample_tail=4,failed_video_only_partial=True,
        compactions=1,compaction_ms=action['elapsed_ns']/1e6,non_CMA_512KiB_before=before,non_CMA_512KiB_after=after,compaction_not_numerical_repair=True,no_drop_caches_reboot_CMA_BOOT_SDK_changes=True,
        evidence_module_Native_ARM_refusals_each=12,evidence_module_integrated=False,hardware_after_failure='SDK-free selftest only; no NPU/VPU/third model start',
        root_cause_proven=False,root_cause_fixed=False,metadata_save_coupling_identified=True,
        kernel_unchanged=True,VPU_abort_streamoffs_success=True,normal_LAST_not_claimed_for_failed_run=True,child_reaped=True,network_sources_live=0,Engine_destroyed_after_workers=True,ports_released=True,all_agent_sessions_closed=True,
        final_memory=resources['final_memory'],review_sha256={name:g.sha(e/name) for name in reviews})
    (e/'completion-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    checkpoint=dict(status=report['status'],user_paused=False,active_tests=False,services_running=False,SSH_SCP_closed=True,
        baseline_package='.local/pose-v1-stage-guard/package-20261009-r1',baseline_build='.local/pose-v1-build/mixed-20261009-stage-guard-r1',board='/tmp/pose-startup-guard-20261009-r1',
        completion_sha256=g.sha(e/'completion-review.json'),third_run_forbidden_in_this_batch=True,
        next='Read STARTUP-GUARD-RESULTS, ADR_20/17 and INVOCATION-EVIDENCE-INTEGRATION-NEXT. Finite pose-only mismatch at inv37 despite same raw/input/scores as earlier inv10.37 correct prefix; full bad result saved, postcopy metadata skipped by repeated save gate. SDK-free Frame/independent flush Native/ARM12 tests passed but not integrated. Prepare isolated observer from original owned shadow and independent flush; Host107 plus synthetic final-output error first, then new three/103 identity only. Keep all old failures, no retry of start2/start3, no map/cache/BOOT/CMA guesses. Only582 has fresh638 wait; static other Host groups223/234/477/481/720 mapped, not root proof. Long-term/HDMI/zero-copy pending.')
    (e/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    (e/'returned-archive-identities.json').write_text(json.dumps({p.name:dict(sha256=g.sha(p),bytes=p.stat().st_size) for p in e.glob('*.tar')},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','correct_complete_FP32','failed_pose_changed_FP32','compaction_ms','non_CMA_512KiB_before','non_CMA_512KiB_after','final_memory','all_agent_sessions_closed']},indent=2))
if __name__=='__main__':main()
