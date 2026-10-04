"""Cross-check fixed-window identities before summarizing the real-data gate."""
import hashlib
import json
import math
from pathlib import Path


def main():
    evidence = Path(__file__).with_name('evidence')
    host = json.loads((evidence / 'host-preprocess-300.json').read_text())
    board = json.loads((evidence / 'board-preprocess-300.json').read_text(encoding='utf-8-sig'))
    manifest = json.loads((evidence / 'replay-300-manifest.json').read_text())
    bundle = json.loads((evidence / 'board-300-bundle.json').read_text())
    if host['policy'] != board['policy'] or host['policy'] != manifest['policy']:
        raise ValueError('Policy mismatch')
    if hashlib.sha256((evidence / 'replay-300-manifest.json').read_bytes()).hexdigest() != bundle['manifest_sha256']:
        raise ValueError('Manifest identity mismatch')
    if board['bundle_sha256'] != bundle['sha256'] or board['executable_sha256'] != bundle['executable_sha256']:
        raise ValueError('Board binary/bundle identity mismatch')
    refs = {r['stem']: r for r in manifest['cases']}
    hosts = {r['stem']: r for r in host['results']}
    boards = {r['stem']: r for r in board['results']}
    if len(refs) != 306 or set(refs) != set(hosts) or set(refs) != set(boards):
        raise ValueError('Fixed case list mismatch')
    for stem, item in refs.items():
        for row in (hosts[stem], boards[stem]):
            if any(row[key] != item[key] for key in ('case','kind','input_sha256','reference_sha256')):
                raise ValueError('Window identity mismatch: ' + stem)
        if item['host_sha256'] != hosts[stem]['actual_sha256']:
            raise ValueError('Host output identity mismatch')
    for stage in (host, board):
        if len(stage['invalid_inputs']) != 4 or not all(r['rejected'] for r in stage['invalid_inputs']):
            raise ValueError('Malformed-input rejection not verified')
    real = [row for row in board['results'] if row['kind'] == 'real']
    if len(real) != 300 or len({r['case'] for r in real}) != 300:
        raise ValueError('Real-data coverage mismatch')
    passed = (host['acceptance'] == board['acceptance'] == 'passed_real_replay_gate')
    times = sorted(row['execution']['preprocess_ms'] for row in real)
    old_assets = json.loads((evidence / 'asset-manifest.json').read_text())
    preserved = [item for item in old_assets['files'] if not '/tools/' in item['path'].replace('\\','/')]
    if any(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256'] for item in preserved):
        raise ValueError('Production source/model/binary changed')
    summary = {
        'stage': 'passed_real_replay_preprocessing_only' if passed else 'blocked',
        'fixed_real_windows': 300, 'group_counts': manifest['group_counts'], 'policy': manifest['policy'],
        'host_bitwise_equal_real': sum(r['bitwise_equal'] for r in host['results'] if r['kind']=='real'),
        'board_bitwise_equal_real': sum(r['bitwise_equal'] for r in real),
        'board_matches_host_real': sum(r['matches_host'] for r in real),
        'real_amplitude_max_abs': max(r['amplitude_max_abs'] for r in real),
        'real_phase_scalar_max_abs_rad': max(r['phase_scalar_max_abs_rad'] for r in real),
        'real_phase_circular_max_rad': max(r['phase_circular_max_rad'] for r in real),
        'nonblocking_diagnostics': [{key: row[key] for key in
                                   ('case','gate','max_abs','phase_circular_max_rad','phase_circular_rms_rad')}
                                  for row in board['results'] if not row['gate']['blocking']],
        'preprocess_only_ms': {'min':times[0], 'median':(times[149]+times[150])/2,
                               'p95_nearest_rank':times[math.ceil(.95*len(times))-1], 'max':times[-1]},
        'timing_limit': 'sequential fixed-window tests only; excludes transport, inference, rendering and video',
        'reference_environment': host['environment'], 'arm64_executable_sha256':board['executable_sha256'],
        'linux_host_executable_sha256':'1d75b6e49488b738a34ab3830b302b117d2defa1b3f30d05ad92f54438d2d9e2',
        'compiler':'g++ 9.4.0, -O2 -ffp-contract=off; existing unchanged production binary',
        'production_source_model_binary_hashes_unchanged':True,
        'npu_executed':False, 'hdmi_executed':False, 'vpu_executed':False,
        'first_version_complete':False,
    }
    (evidence / 'replay-300-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
