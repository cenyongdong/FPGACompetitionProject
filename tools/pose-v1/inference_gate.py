"""User-run packaging, ONNX reference and comparison; never installs or opens devices."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import time

CASES = ('S11_01_308', 'S11_01_309', 'S11_01_310')
PINNED = {
    'piw24_ZG.json': '75ffdc37b93dcb4913678991d6e7cf5cd0ab09c59653224d07c7434345acb8a0',
    'piw24_ZG.raw': '3991a679282a4c6b014aece59b717910bc53fd14e67c0fac5fb9f93d4ae054d3',
    'piw24_optimized.json': '3c95b99f35032f001643abb981193eb5558ad3e545a61cb3261388da6246e296',
    'piw24_optimized.raw': '9b74e369a477bafced2a6664d447fd769f1c539aa1177b5e66ccd45aa900c780',
    'person_in_wifi_2024_best_epoch442_full.onnx': '7b04090e374e31e016d5703bbcf1d0a561d0b98f268fde984b0bf0461598bd21',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def fresh(path):
    path.mkdir(parents=True, exist_ok=False)


def verify_package(package):
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    if tuple(item['case'] for item in manifest['cases']) != CASES:
        raise ValueError('Fixed three-case list changed')
    for item in manifest['files']:
        if digest(package / item['relative_path']) != item['sha256']:
            raise ValueError('Package file changed: ' + item['relative_path'])
    return manifest


def prepare(args):
    # Reuse the exact approved 300-case gate bytes; no new preprocessing algorithm.
    source = json.loads((args.fixtures / 'manifest.json').read_text(encoding='utf-8'))
    selected = []
    for name in CASES:
        found = [item for item in source['cases'] if item['case'] == name and item['kind'] == 'real']
        if len(found) != 1:
            raise ValueError('Missing/ambiguous approved real fixture: ' + name)
        item = found[0]
        for suffix, key in (('.csi', 'input_sha256'), ('.reference.f32', 'reference_sha256')):
            if digest(args.fixtures / (item['stem'] + suffix)) != item[key]:
                raise ValueError('Approved fixture changed: ' + name + suffix)
        data = (args.fixtures / (item['stem'] + '.csi')).read_bytes()
        magic, version, size, frame, stamp = struct.unpack('<8sIIQQ', data[:32])
        if (magic, version, size, len(data)) != (b'PIWCSI1\0', 1, 86400, 86432):
            raise ValueError('Invalid original fixture record')
        selected.append((name, item, frame, stamp))
    paths = {name: args.repo / 'result/icraft_2024' / name for name in PINNED}
    onnx = 'person_in_wifi_2024_best_epoch442_full.onnx'
    paths[onnx] = args.repo / 'result/code_faithful' / onnx
    for name, path in paths.items():
        if digest(path) != PINNED[name]:
            raise ValueError('Pinned model changed: ' + str(path))
    fresh(args.output)
    for folder in ('inputs', 'reference', 'models'):
        (args.output / folder).mkdir()
    cases, files = [], []

    def copy(src, relative):
        dst = args.output / relative
        shutil.copyfile(src, dst)
        if digest(src) != digest(dst):
            raise ValueError('Copy mismatch')
        files.append({'relative_path': relative, 'source': str(src.resolve()),
                      'bytes': dst.stat().st_size, 'sha256': digest(dst)})

    for name, item, frame, stamp in selected:
        copy(args.fixtures / (item['stem'] + '.csi'), 'inputs/' + name + '.csi')
        copy(args.fixtures / (item['stem'] + '.reference.f32'), 'reference/' + name + '.input.f32')
        cases.append({'case': name, 'frame_id': frame, 'source_time_ns': stamp,
                      'original_fixture_stem': item['stem']})
    for name, path in paths.items():
        copy(path, 'models/' + name)
    save(args.output / 'manifest.json', {'schema_version': 1, 'model': '2024 epoch442',
         'source_fixture_manifest_sha256': digest(args.fixtures / 'manifest.json'),
         'cases': cases, 'files': files, 'numerical_acceptance': 'pending_execution'})
    (args.output / 'files.sha256').write_text(''.join(f"{f['sha256']}  {f['relative_path']}\n" for f in files), encoding='ascii')
    print('Prepared and hashed; no inference: ' + str(args.output))


def array(np, path, count):
    if path.stat().st_size != count * 4:
        raise ValueError('Unexpected tensor byte count: ' + str(path))
    data = np.fromfile(path, dtype='<f4')
    if not np.isfinite(data).all():
        raise ValueError('NaN/Inf: ' + str(path))
    return data


def onnx_reference(args):
    # Dependency presence must be reviewed before installing anything.
    import numpy as np
    import onnxruntime as ort
    manifest = verify_package(args.package)
    session = ort.InferenceSession(str(args.package / 'models/person_in_wifi_2024_best_epoch442_full.onnx'),
                                  providers=['CPUExecutionProvider'])
    inputs, outputs = session.get_inputs(), session.get_outputs()
    if len(inputs) != 1 or inputs[0].shape != [1, 180, 60] or inputs[0].type != 'tensor(float)':
        raise ValueError('Unexpected ONNX input signature')
    if len(outputs) != 2:
        raise ValueError('Unexpected ONNX output count')
    score = [o for o in outputs if o.shape == [1, 100] and o.type == 'tensor(float)']
    pose = [o for o in outputs if o.shape == [1, 100, 14, 3] and o.type == 'tensor(float)']
    if len(score) != 1 or len(pose) != 1:
        raise ValueError('Unexpected ONNX outputs; stop rather than reshape speculatively')
    fresh(args.output)
    results = []
    for item in manifest['cases']:
        name = item['case']
        src = args.package / 'reference' / (name + '.input.f32')
        tokens = array(np, src, 10800).reshape(1, 180, 60)
        begin = time.perf_counter()
        scores, poses = session.run([score[0].name, pose[0].name], {inputs[0].name: tokens})
        ms = (time.perf_counter() - begin) * 1000
        if scores.shape != (1,100) or poses.shape != (1,100,14,3) or not np.isfinite(scores).all() or not np.isfinite(poses).all():
            raise ValueError('Invalid ONNX output')
        shutil.copyfile(src, args.output / (name + '.input.f32'))
        scores.astype('<f4').tofile(args.output / (name + '.scores.f32'))
        poses.astype('<f4').tofile(args.output / (name + '.poses.f32'))
        results.append(dict(item, mode='onnx_cpu_reference', top_index=int(np.argmax(scores)),
                            top_score=float(scores.max()), forward_ms=ms))
    (args.output / 'results.jsonl').write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in results), encoding='utf-8')
    save(args.output / 'environment.json', {'numpy': np.__version__, 'onnxruntime': ort.__version__,
         'providers': session.get_providers(), 'model_sha256': PINNED['person_in_wifi_2024_best_epoch442_full.onnx'],
         'purpose': 'reference only; does not satisfy NPU acceptance'})


def metrics(np, left, right):
    delta = right.astype(np.float64) - left.astype(np.float64)
    absolute = np.abs(delta)
    return {'bitwise_equal': bool(np.array_equal(left.view('u4'), right.view('u4'))),
            'max_abs': float(absolute.max()), 'mean_abs': float(absolute.mean()),
            'rms': float(np.sqrt(np.mean(delta * delta))), 'p95_abs': float(np.percentile(absolute, 95))}


def compare(args):
    import numpy as np
    manifest = verify_package(args.package)
    def rows(folder):
        records = [json.loads(line) for line in (folder / 'results.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        mapped = {r['case']: r for r in records}
        if len(records) != 3 or set(mapped) != set(CASES):
            raise ValueError('Missing/duplicate/mislabelled results')
        for item in manifest['cases']:
            row = mapped[item['case']]
            if row['frame_id'] != item['frame_id'] or row['source_time_ns'] != item['source_time_ns']:
                raise ValueError('Frame identity differs')
        return mapped
    left_rows, right_rows = rows(args.left), rows(args.right)
    report = {'left': str(args.left), 'right': str(args.right), 'cases': [],
              'numerical_acceptance': 'pending_user_discussion', 'coordinate_units': 'model_raw_unconfirmed',
              'candidate_comparison': 'same candidate index; index/rank switches reported separately'}
    valid = True
    signatures = []
    for item in manifest['cases']:
        name = item['case']
        reference = array(np, args.package / 'reference' / (name + '.input.f32'), 10800).reshape(180,60)
        gate = []
        for folder in (args.left, args.right):
            tokens = array(np, folder / (name + '.input.f32'), 10800).reshape(180,60)
            phase_delta = tokens[:,30:].astype('f8') - reference[:,30:].astype('f8')
            amp = np.allclose(tokens[:,:30], reference[:,:30], atol=1e-6, rtol=1e-6)
            scalar = float(np.abs(phase_delta).max())
            circular = float(np.abs(np.arctan2(np.sin(phase_delta),np.cos(phase_delta))).max())
            passed = bool(amp and scalar <= 1e-5 and circular <= 1e-5)
            valid = valid and passed
            gate.append(dict(path=str(folder), passed=passed, amplitude=metrics(np,reference[:,:30],tokens[:,:30]),
                             phase_scalar_max=scalar, phase_circular_max=circular,
                             input_bitwise_equal=bool(np.array_equal(reference.view('u4'), tokens.view('u4')))))
        ls, rs = [array(np, p / (name + '.scores.f32'), 100) for p in (args.left,args.right)]
        lp, rp = [array(np, p / (name + '.poses.f32'), 4200).reshape(100,14,3) for p in (args.left,args.right)]
        li, ri = int(np.argmax(ls)), int(np.argmax(rs))
        l2 = np.linalg.norm(rp.astype('f8') - lp.astype('f8'),axis=-1)
        signatures.append((rs.tobytes(),rp.tobytes()))
        report['cases'].append(dict(case=name, frame_id=item['frame_id'], preprocessing=gate,
             scores=metrics(np,ls,rs), poses=metrics(np,lp,rp), same_index_joint_distance_mean_raw=float(l2.mean()),
             same_index_joint_distance_max_raw=float(l2.max()), top_index_left=li, top_index_right=ri,
             top_index_changed=li!=ri, top_score_left=float(ls[li]), top_score_right=float(rs[ri]),
             selected_pose_delta_raw=metrics(np,lp[li],rp[ri]),
             left_execution=left_rows[name],right_execution=right_rows[name]))
    report['right_outputs_change_across_inputs'] = len(set(signatures)) > 1
    report['preprocessing_gate_passed'] = valid
    report['outputs_finite'] = True
    fresh(args.output)
    save(args.output / 'comparison.json', report)
    if not valid or not report['right_outputs_change_across_inputs']:
        raise ValueError('Stop: preprocessing changed or all three outputs identical; inspect saved report')
    print('Comparison saved; score/coordinate acceptance remains pending discussion')


def verify_return(args):
    records = args.checksums.read_text(encoding='ascii').splitlines()
    seen = set()
    for line in records:
        checksum, name = line.split('  ', 1)
        # sha256sum runs from the parent, so accept exactly mixed/<simple filename>.
        parts = name.split('/')
        if len(parts) != 2 or parts[0] != 'mixed' or parts[1] in ('', '.', '..') or '\\' in parts[1]:
            raise ValueError('Unexpected checksum path')
        if parts[1] in seen or digest(args.directory / parts[1]) != checksum:
            raise ValueError('Duplicate or changed returned file: ' + name)
        seen.add(parts[1])
    actual = {p.name for p in args.directory.iterdir() if p.is_file()}
    if not seen or seen != actual:
        raise ValueError('Returned file list differs from board checksums')
    print('Returned file hashes match board: ' + str(len(seen)))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    prepare_p = sub.add_parser('prepare')
    prepare_p.add_argument('--repo', required=True, type=Path)
    prepare_p.add_argument('--fixtures', required=True, type=Path)
    prepare_p.add_argument('--output', required=True, type=Path)
    prepare_p.set_defaults(func=prepare)
    probe = sub.add_parser('dependencies')
    probe.set_defaults(func=lambda _: print(json.dumps({name: importlib.util.find_spec(name) is not None
                       for name in ('numpy', 'onnxruntime')}, indent=2)))
    onnx = sub.add_parser('onnx')
    onnx.add_argument('--package', required=True, type=Path)
    onnx.add_argument('--output', required=True, type=Path)
    onnx.set_defaults(func=onnx_reference)
    cmp = sub.add_parser('compare')
    for name in ('package','left','right','output'):
        cmp.add_argument('--'+name, required=True, type=Path)
    cmp.set_defaults(func=compare)
    returned = sub.add_parser('verify-return')
    returned.add_argument('--directory', required=True, type=Path)
    returned.add_argument('--checksums', required=True, type=Path)
    returned.set_defaults(func=verify_return)
    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
