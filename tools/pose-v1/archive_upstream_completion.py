"""Bind already reviewed upstream evidence; local files only, no new test/device run."""
import hashlib
import json
from pathlib import Path
from review_upstream_boundary_r4_stage import identities

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / 'tools/pose-v1/evidence/upstream-boundary-20261011-r4'

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    assert not p.exists(), p
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def main():
    package = ROOT / '.local/pose-v1-upstream-boundary/package-20261011-r4'
    build = ROOT / '.local/pose-v1-build/mixed-20261011-upstream-boundary-r4'
    m, b, n = identities(package, build)
    assert n == 403 and len(m['build_files']) == 146
    host, three, bad = [load(E / f) for f in ('host-check.acceptance.json', 'process-three.acceptance.json', 'failure-review.json')]
    assert host['Host_cases'] == 107 and host['CPU_FP32'] == 59600
    assert load(E/'host.contracts.json')['original_Gather_NumPy_bitwise']
    assert three['FP32_compared'] == 60400 and three['normal_drain_and_reaping']
    assert bad['complete_correct'] == 55 and bad['FP32_correct'] == 830500
    assert bad['failed_invocation'] == 55 and bad['failed_frame'] == 100056
    index = bad['Host_and_late'][2]
    assert index['Host_vs_gold']['changed_FP32'] == 1584
    assert index['Host_vs_gold']['noninteger_actual'] == 1582
    assert all(x['vs_gold']['bitwise_equal'] for x in index['late'])
    assert bad['kernel_unchanged'] and bad['all_project_services_closed']
    partial = load(E/'diagnostic.partial-boundary.json')
    assert partial['rows'] == 440 and partial['invocations'] == 55 and partial['complete_owned_frames'] == 4
    expected = {
        'host.tar': '540c9e86ec8676ef80455b7b2440381822ed85c48629ed48e1da6d6ef4ad42f5',
        'three.tar': 'f2ea76c4ba0b0f0120a56f80b930686b9315589aeb00e635e7437d6467c94b8e',
        'diagnostic.tar': 'fe70f208857da7d61196231512ba16efb4ad7ad32fedefb592d9bb652c5f5206',
    }
    for name, digest in expected.items():
        assert sha(E/name) == digest
    files = [
        'build.acceptance.json', 'host-check.acceptance.json', 'host.numeric.json',
        'host.Gather-boundary.json', 'host.contracts.json',
        'process-three.acceptance.json', 'process-three.numeric.json', 'process-three.boundary.json',
        'three-video/review.json', 'three-network-prefix/review.json',
        'client-three/sender.json', 'client-diagnostic/sender.json',
        'failure-review.json', 'diagnostic.partial-boundary.json', 'objects.json', 'counts.json',
        'static-lineage.json', 'diagnostic-video-prefix/review.json', 'diagnostic-network-prefix/review.json',
        'resource-three.log', 'resource-diagnostic.log',
    ]
    completed = dict(
        status='approved_diagnostic_completed_failure_preserved_root_unresolved',
        date='2026-10-11', binary_sha256=b['binary_sha256'],
        package_manifest_sha256=b['package_manifest_sha256'], payloads=n, build_sources=len(m['build_files']),
        frozen_ELFs_bitwise=36, Host_cases=107, Host_FP32=59600, registry_records=12,
        normal_four_window_FP32=60400, normal_encoded=495, normal_network=465,
        high_load_correct_returns=55, high_load_FP32=830500,
        failed_invocation=55, actual_transport_frame=100056, case='S11_32_349', failed_op=192,
        first_Host_indices_changed=1584, first_Host_indices_noninteger=1582,
        two_late_reads_bitwise_gold=True, boundary_metadata_rows=440,
        complete_owned_boundary_frames=4, failed_current_frame_not_reached_Gather442=True,
        original_eight_plus_independent_one_tasks_saved=True,
        high_load_video_prefix=407, high_load_network_prefix=377, visible_sources=52,
        completed_sources_not_captured=[52,53,54], normal_drain_in_failed_batch=False,
        compactions_this_approved_scope=2, compaction_ms=[148.45488,225.37927],
        diagnostic_compaction=False, kernel_unchanged=True,
        root_cause_proven=False, high_load103_passed=False, strict_5Hz_passed=False,
        next_plan_executed=False, all_test_processes_and_connections_closed=True,
        management_estimate=83, estimate_is_not_acceptance_rate=True,
        archive_SHA256=expected, evidence_SHA256={name:sha(E/name) for name in files},
        build_result_SHA256=sha(build/'build-result.json'),
        frozen_reuse_SHA256=sha(build/'frozen-build-reuse.json'),
        report_SHA256=sha(ROOT/'tools/pose-v1/UPSTREAM-BOUNDARY-RESULTS-20261011.md'),
        next_plan_SHA256=sha(ROOT/'tools/pose-v1/UPSTREAM-BOUNDARY-NEXT-20261011.md'),
    )
    write(E/'completion-review.json', completed)
    checkpoint = dict(
        status='batch_completed_at_failure_safe_stop', date='2026-10-11',
        paused_by_user=False, active_processes=False, active_connections=False,
        hardware_retry_pending=False, root_cause_fixed=False,
        completion_SHA256=sha(E/'completion-review.json'),
        read_first=['tools/pose-v1/UPSTREAM-BOUNDARY-RESULTS-20261011.md','ADR/ADR_34.md',
                    'tools/pose-v1/UPSTREAM-BOUNDARY-NEXT-20261011.md'],
        next='Review actual SDK read completion and capture first-read/Host-staging boundaries in a new isolated identity.',
        no_retry_old_failed_run=True, no_frequency_adjustment=True,
        no_reboot_cache_clear_CMA_BOOT_model_SDK_change=True,
    )
    write(E/'next-checkpoint.json', checkpoint)
    # This is the mutable progress entry, not an original test result.
    (E/'in-progress-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Completion identities, reviewed reports and archive hashes bound; no hardware operations.')

if __name__ == '__main__':
    main()
