"""Compare C++ against the actual training methods, without mmdet/GPU imports.

Reports errors rather than inventing an acceptance tolerance. Uses FPAI only
for the Linux host executable; arm64 device checks remain a separate gate.
"""
import argparse
import ast
import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import pywt
from csi_io import encode_window, load_mat
from numeric_metrics import POLICY, compare_tokens, gate_result


def training_processor(source):
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    wanted = {'CSI_sanitization', 'phase_deno', 'dwt_amp'}
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'WifiPoseDataset']
    if len(classes) != 1:
        raise ValueError('Training dataset class missing/ambiguous')
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    if {m.name for m in methods} != wanted:
        raise ValueError('Training methods changed/missing')
    isolated = ast.ClassDef(name='TrainingProcessor', bases=[], keywords=[], body=methods, decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[isolated], type_ignores=[]))
    scope = {'np': np, 'pywt': pywt}
    exec(compile(module, str(source), 'exec'), scope)
    return scope['TrainingProcessor']()


def reference(csi, processor):
    amp = processor.dwt_amp(csi)
    phase = np.angle(processor.phase_deno(csi))
    return np.concatenate((amp, phase), axis=2).astype(np.float32).transpose(0, 1, 3, 2).reshape(1, 180, 60)


def run(docker, *args, require_success=True):
    result = subprocess.run([docker, *args], capture_output=True, text=True, timeout=60)
    if require_success and result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_real_sources(data):
    """300 fixed windows, stratified by filename group, retaining old regressions."""
    listed = (data.parent / 'test_data_list.txt').read_text(encoding='utf-8-sig').splitlines()
    listed = [name.strip() for name in listed if name.strip()]
    if len(set(listed)) != len(listed):
        raise ValueError('Duplicate entries in test data list')
    groups = {}
    for name in listed:
        groups.setdefault(name.split('_')[0], []).append(name)
    if len(groups) != 9:
        raise ValueError('Approved sampling expects nine groups; discuss changed data')
    selected, counts = [], {}
    mandatory = {'S11_01_308', 'S11_01_309', 'S11_01_310'}
    if not mandatory.issubset(listed):
        raise ValueError('Original regression windows missing')
    for index, group in enumerate(sorted(groups)):
        quota = 34 if index < 3 else 33
        members = groups[group]
        retained = [name for name in members if name in mandatory]
        remaining = [name for name in members if name not in mandatory]
        wanted = quota - len(retained)
        if len(remaining) < wanted or wanted < 2:
            raise ValueError('Insufficient group data')
        # Even spacing with floor, including the first and last remaining record.
        retained += [remaining[i * (len(remaining)-1) // (wanted-1)] for i in range(wanted)]
        chosen = set(retained)
        selected.extend(data / (name + '.mat') for name in members if name in chosen)
        counts[group] = {'available': len(members), 'selected': quota}
    if len(selected) != 300 or len(set(selected)) != 300:
        raise ValueError('Sampling count mismatch')
    return selected, counts, data.parent / 'test_data_list.txt'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--docker', default=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe')
    parser.add_argument('--container', default='FPAI')
    parser.add_argument('--executable', default='/tmp/pose-v1-preprocess-host')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixtures = args.output / 'fixtures'
    fixtures.mkdir()
    source = args.repo / 'opera/datasets/wifi_pose.py'
    processor = training_processor(source)
    rng = np.random.default_rng(20261004)
    cases = {'constant': np.ones((3,3,30,20), dtype=np.complex128),
             'zero': np.zeros((3,3,30,20), dtype=np.complex128),
             'random': rng.normal(size=(3,3,30,20)) + 1j*rng.normal(size=(3,3,30,20))}
    n = np.arange(30)[None,None,:,None]
    a = np.arange(3)[None,:,None,None]
    t = np.arange(20)[None,None,None,:]
    for slope in (0.75, 3.141592653589793, -3.141592653589793):
        phase = np.broadcast_to(slope*n + 0.7*a + 0.1*t, (3,3,30,20))
        cases['ramp_' + str(slope)] = (1 + rng.random((3,3,30,20))) * np.exp(1j*phase)
    data = args.repo / 'data/wifipose/test_data/csi'
    paths, group_counts, data_list = select_real_sources(data)
    for path in paths:
        cases[path.stem] = load_mat(path)
    references = {}
    manifest = {'schema_version': 1, 'policy': POLICY, 'group_counts': group_counts,
                'list_sha256': digest(data_list), 'cases': []}
    names = {}
    for index, (name, csi) in enumerate(cases.items()):
        stem = f'case_{index:03d}'
        names[stem] = name
        (fixtures / (stem + '.csi')).write_bytes(encode_window(csi, index))
        expected = reference(csi, processor)
        if not np.isfinite(expected).all():
            raise ValueError('Non-finite training reference')
        references[stem] = expected
        (fixtures / (stem + '.reference.f32')).write_bytes(expected.astype('<f4').tobytes())
        kind = ('real' if index >= 6 else 'artificial_pi_boundary' if index in (4,5) else 'synthetic_regression')
        manifest['cases'].append({'stem': stem, 'case': name, 'kind': kind,
            'input_sha256': digest(fixtures / (stem + '.csi')),
            'reference_sha256': digest(fixtures / (stem + '.reference.f32'))})
    first = (fixtures / 'case_000.csi').read_bytes()
    (fixtures / 'invalid_truncated.csi').write_bytes(first[:-1])
    (fixtures / 'invalid_trailing.csi').write_bytes(first + b'X')
    (fixtures / 'invalid_magic.csi').write_bytes(b'BADMAGIC' + first[8:])
    corrupt = bytearray(first)
    import struct
    corrupt[32:40] = struct.pack('<d', float('nan'))
    (fixtures / 'invalid_nan.csi').write_bytes(corrupt)
    (fixtures / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    remote = '/tmp/pose-v1-fixtures-' + datetime.now().strftime('%Y%m%d%H%M%S')
    run(args.docker, 'cp', str(fixtures), args.container + ':' + remote)
    batch = ('for raw in "$1"/case_*.csi; do '
             '"$2" "$raw" "${raw%.csi}.host.f32" > "${raw%.csi}.execution.json" || exit; done')
    run(args.docker, 'exec', args.container, 'sh', '-c', batch, 'pose-preprocess', remote, args.executable)
    run(args.docker, 'cp', args.container + ':' + remote + '/.', str(fixtures))
    results = []
    for item in manifest['cases']:
        stem = item['stem']
        expected = references[stem]
        output = fixtures / (stem + '.host.f32')
        actual = np.fromfile(output, dtype='<f4').reshape(1,180,60)
        metrics = compare_tokens(actual.reshape(-1), expected.reshape(-1),
                                 np.array_equal(actual.view(np.uint32), expected.view(np.uint32)))
        item['host_sha256'] = digest(output)
        results.append({'case': names[stem], 'stem': stem, 'kind': item['kind'], **metrics,
                        'gate': gate_result(item['kind'], metrics),
                        'input_sha256': digest(fixtures / (stem + '.csi')),
                        'reference_sha256': digest(fixtures / (stem + '.reference.f32')),
                        'actual_sha256': digest(output),
                        'execution': json.loads((fixtures / (stem + '.execution.json')).read_text())})
    invalids = []
    for path in sorted(fixtures.glob('invalid_*.csi')):
        result = run(args.docker, 'exec', args.container, args.executable,
                     remote + '/' + path.name, remote + '/invalid.f32', require_success=False)
        invalids.append({'case': path.name, 'rejected': result.returncode != 0,
                         'returncode': result.returncode, 'message': result.stderr.strip()})
    report = {'stage': 'host_preprocess_comparison', 'board_tested': False,
              'training_source_sha256': digest(source),
              'raw_sources': [{'path': str(p), 'sha256': digest(p)} for p in paths],
              'sampling': {'count': len(paths), 'groups': group_counts, 'list_sha256': digest(data_list)},
              'policy': POLICY,
              'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                              'h5py': h5py.__version__, 'pywavelets': pywt.__version__},
              'wavelet_max_level': pywt.dwt_max_level(20, pywt.Wavelet('db11').dec_len),
              'results': results, 'invalid_inputs': invalids,
              'acceptance': ('passed_real_replay_gate' if all(r['gate']['status'] == 'passed'
                              for r in results if r['gate']['blocking']) and all(r['rejected'] for r in invalids)
                              else 'blocked'),
              'remote_fixtures': remote}
    (fixtures / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (args.output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if not all(r['finite'] for r in results) or not all(r['rejected'] for r in invalids):
        raise RuntimeError('Finite output or malformed-input rejection failed')
    print(json.dumps({'cases': len(results), 'max_abs': max(r['max_abs'] for r in results),
                      'invalid_rejected': len(invalids), 'report': str(args.output / 'report.json')}))
    if report['acceptance'] != 'passed_real_replay_gate':
        raise RuntimeError('Real/synthetic regression gate blocked; preserve report and discuss before inference')


if __name__ == '__main__':
    main()
