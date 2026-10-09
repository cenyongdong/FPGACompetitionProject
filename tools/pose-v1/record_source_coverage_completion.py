"""Bind bounded coverage evidence; keep fault and performance conclusions separate."""
import hashlib
import json
from pathlib import Path
import mixed_validation_gate as gate


def main():
    evidence = gate.ROOT / 'tools/pose-v1/evidence/source-coverage-20261009-r4'
    load = lambda name: json.loads((evidence / name).read_text())
    reports = []
    reviews = ['resource-review.json', 'pure-trace-review.json', 'forward-trace-analysis.json',
               'callback-gap-review.json', 'finite-rate-review.json', 'process-three.acceptance.json']
    for stage, media in [('measure-2hz', '2hz'), ('trace-5hz', 'trace')]:
        run = evidence / ('run-' + stage)
        returned = gate.verify(run)
        numeric = load(stage + '.numeric-review.json')
        video = load('video-' + media + '/review.json')
        network = load('network-' + media + '/review.json')
        assert numeric['status'] == 'live_stage_passed' and numeric['full_numeric_bitwise']
        assert numeric['sent'] == numeric['consumed'] == 33 and numeric['overwritten'] == 0
        assert video['status'] == 'resident_video_sources_and_IDs_verified'
        assert network['status'] == 'real_capture_RTSP_bytes_PTS_sources_pixels_verified'
        assert video['inference_sources'] == network['new_inference_sources'] == 33
        assert video['decoded_frames'] == numeric['encoded'] and network['all_sources_present']
        assert not (run / 'results/failed-host-inputs').exists()
        calls = [json.loads(line) for line in (run / 'results/inference.jsonl').read_text().splitlines()]
        assert len(set(call['case'] for call in calls)) == 27
        for i in range(6):
            assert calls[i]['case'] == calls[i + 27]['case']
            for suffix in ('input', 'scores', 'poses'):
                assert (run / f'results/result{i}.{suffix}.f32').read_bytes() == (run / f'results/result{i+27}.{suffix}.f32').read_bytes()
        sender = load('client-' + ('2hz' if stage == 'measure-2hz' else 'trace-5hz') + '/sender.json')
        assert sender['session_count'] == 1 and sender['status'] == 'sent_no_receiver_ack' and len(sender['sent']) == 33
        reports.append(dict(stage=stage, returned_files=returned, model_forwards=33,
            full_model_FP32_bitwise=498300, unique_cases=27, repeated_cases_bitwise=6,
            encoded=video['decoded_frames'], network_frames=network['network_frames'],
            joint_checks=video['joint_visibility_checks'], no_error_capture_triggered=True))
        reviews.extend([stage + '.numeric-review.json', 'video-' + media + '/review.json', 'network-' + media + '/review.json'])
    pure = load('pure-trace-review.json')
    trace = load('forward-trace-analysis.json')
    assert pure['invocations'] == 32 and pure['records'] == 1856
    assert pure['readiness_rows'] == pure['operator_log_rows'] == pure['observation_spans'] == 0
    assert not pure['performance_acceptance'] and not trace['old_spike_threshold_reached']
    assert load('resource-review.json')['status'] == 'identity_kernel_ports_own_processes_released_verified'
    resources = evidence / 'resource-bytes'
    assert (resources / 'final-audit/dmesg').read_bytes() == (evidence / 'run-trace-5hz/dmesg.after.log').read_bytes()
    assert ':8554' not in (resources / 'final-audit/ports').read_text() and ':39001' not in (resources / 'final-audit/ports').read_text()
    assert not any('pose_live_pipeline_check' in line or 'pose_display_worker' in line
                   for line in (resources / 'final-audit/processes').read_text().splitlines())
    report = dict(status='bounded_2Hz_and_pure_trace_full_chain_verified_fault_and_old_spike_not_reproduced',
        program_sha256=load('measure-2hz.numeric-review.json')['binary_sha256'],
        package_manifest_sha256=load('measure-2hz.numeric-review.json')['package_manifest_sha256'],
        payloads=403, build_sources=63, source_readback_retained=True, source_math_sync_changed=False,
        fresh_compilation=False, Host107_reused_from_reviewed_r4=True,
        stages=reports, model_forwards=66, full_model_FP32_bitwise=996600,
        encoded=997, network_frames=937, joint_checks=5446,
        pure_timing_records=1856, pure_timing_invocations=32,
        actual_model_error_source_reads=0, data_fault_reproduced=False, root_cause_fixed=False,
        old_221ms_spike_reproduced=False, performance_5Hz_accepted=False, long_103_executed=False,
        compactions=0, no_cache_clear_reboot_BOOT_CMA_SDK_changes=True,
        final_resources_released=True, all_agent_sessions_closed=True,
        MemAvailable_KiB=749848, CmaFree_KiB=0, permanent_startup_or_leak_proven=False,
        review_sha256={name: gate.sha(evidence / name) for name in reviews})
    (evidence / 'completion-review.json').write_text(json.dumps(report, indent=2)+'\n')
    checkpoint = dict(status=report['status'], user_paused=False, active_tests=False,
        services_running=False, SSH_SCP_closed=True,
        package='.local/pose-v1-source-readback/package-20261009-r4',
        build='.local/pose-v1-build/mixed-20261009-source-readback-r4',
        board='/tmp/pose-source-coverage-20261009-r4',
        program_sha256=report['program_sha256'],
        completion_sha256=gate.sha(evidence / 'completion-review.json'),
        next='Read SOURCE-COVERAGE-RESULTS-20261009.md and ADR_16/17. Keep Host staging + two SDK error reads in any next candidate. 66 exact forwards and 32 pure traces passed; neither old bad blocks nor old221ms spike recurred. Actual device error read branch remains untested. Next prepare coordinated103 low-log bounds and independent input-paced/capacity metrics, retain all data/error stops. No repeat failed runs, cache/reset/BOOT/CMA/SDK changes. HDMI/30min remain pending.')
    (evidence / 'next-checkpoint.json').write_text(json.dumps(checkpoint, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
