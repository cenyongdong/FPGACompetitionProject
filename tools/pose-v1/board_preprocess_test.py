"""Run the cross-compiled pure-math checker from a verified temporary bundle.
No hardware registers, model runtime, video node, or boot configuration access.
"""
import array
import base64
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import textwrap
from pathlib import Path


def main():
    archive, expected = Path(sys.argv[1]), sys.argv[2]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError('Board bundle SHA256 mismatch')
    destination = Path('/tmp') / ('pose-v1-test-' + expected[:16])
    destination.mkdir(exist_ok=False)
    with tarfile.open(archive, 'r:gz') as bundle:
        for member in bundle.getmembers():
            if not member.isfile() or '/' in member.name or '\\' in member.name or member.name in ('.','..'):
                raise ValueError('Unexpected bundle member')
            if member.size > 1024 * 1024:
                raise ValueError('Unexpected bundle member size')
            (destination / member.name).write_bytes(bundle.extractfile(member).read())
    executable = destination / 'pose_preprocess_check.arm64'
    sys.path.insert(0, str(destination))
    from numeric_metrics import POLICY, compare_tokens, gate_result
    manifest = json.loads((destination / 'manifest.json').read_text())
    if manifest['policy'] != POLICY or len(manifest['cases']) != 306:
        raise ValueError('Approved policy/case manifest mismatch')
    executable.chmod(0o700)
    basic = subprocess.run([str(executable),'--self-test'], capture_output=True, text=True, timeout=10)
    if basic.returncode:
        raise RuntimeError(basic.stderr)
    results, invalids = [], []
    for item in manifest['cases']:
        raw = destination / (item['stem'] + '.csi')
        if hashlib.sha256(raw.read_bytes()).hexdigest() != item['input_sha256']:
            raise ValueError('Input hash mismatch')
        output = raw.with_suffix('.arm64.f32')
        run = subprocess.run([str(executable),str(raw),str(output)], capture_output=True, text=True, timeout=10)
        if run.returncode:
            raise RuntimeError(run.stderr)
        actual_bytes = output.read_bytes()
        reference_bytes = raw.with_suffix('.reference.f32').read_bytes()
        if hashlib.sha256(reference_bytes).hexdigest() != item['reference_sha256']:
            raise ValueError('Reference hash mismatch')
        if len(actual_bytes) != 43200 or len(reference_bytes) != 43200:
            raise ValueError('Model tensor byte count mismatch')
        actual, reference = array.array('f'), array.array('f')
        actual.frombytes(actual_bytes)
        reference.frombytes(reference_bytes)
        if sys.byteorder != 'little':
            actual.byteswap(); reference.byteswap()
        metrics = compare_tokens(actual, reference, actual_bytes == reference_bytes)
        results.append({'stem':raw.stem, 'case':item['case'], 'kind':item['kind'], **metrics,
                        'gate':gate_result(item['kind'], metrics),
                        'input_sha256':item['input_sha256'],
                        'matches_host':hashlib.sha256(actual_bytes).hexdigest() == item['host_sha256'],
                        'actual_sha256':hashlib.sha256(actual_bytes).hexdigest(),
                        'reference_sha256':hashlib.sha256(reference_bytes).hexdigest(),
                        'execution':json.loads(run.stdout)})
    for raw in sorted(destination.glob('invalid_*.csi')):
        run = subprocess.run([str(executable),str(raw),str(destination/'invalid.f32')],
                             capture_output=True,text=True,timeout=10)
        invalids.append({'case':raw.name,'rejected':run.returncode!=0,'message':run.stderr.strip()})
    report = {'scope':'arm64 pure-math preprocess only; no NPU/HDMI/VPU',
              'uname':list(os.uname()),'bundle_sha256':expected,'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
              'temporary_directory':str(destination),'self_test':basic.stdout.strip(),
              'sampling':{'count':300,'groups':manifest['group_counts'], 'list_sha256':manifest['list_sha256']},
              'policy':POLICY,
              'results':results,'invalid_inputs':invalids,
              'acceptance':('passed_real_replay_gate' if all(r['gate']['status']=='passed'
                           for r in results if r['gate']['blocking']) and all(r['rejected'] for r in invalids)
                           else 'blocked')}
    print('POSE_TEST_BEGIN')
    print(textwrap.fill(base64.b64encode(json.dumps(report).encode()).decode(),64))
    print('POSE_TEST_END')


if __name__=='__main__':
    main()
