"""本轮已批准的CPU107及三窗口回归；各门检成功后才执行下一阶段。"""
from pathlib import Path
import argparse
import getpass
import hashlib
import json
import subprocess
import sys

import numpy as np
import deploy
import ssh_transport

ROOT = Path(__file__).resolve().parents[2]
DEMO = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/pose-v1'))
from cpu_adapter_gate import verify_checksums


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def reviewCpu(evidence, build, package):
    run = evidence / 'cpu-return/run-cpu'
    assert verify_checksums(run) > 0 and verify_checksums(package) > 0
    assert (run / 'exit.txt').read_text().strip() == '0'
    assert (run / 'run.stderr.log').stat().st_size == 0
    assert (run / 'before.dmesg.txt').read_bytes() == (run / 'after.dmesg.txt').read_bytes()
    manifest = load(package / 'manifest.json')
    compiled = load(build / 'build-result.json')
    identities = load(run / 'input-identities.json')
    assert identities['binary'] == compiled['regression_programs']['pose_core_cpu_check']
    assert identities['graph'] == compiled['graph_sha256'] == manifest['graph_sha256']
    assert identities['package_manifest'] == sha(package / 'manifest.json')
    assert identities['build_result'] == sha(build / 'build-result.json')
    audit = load(run / 'sdk-audit.json')
    assert audit['headers_normalized_sha256'] == manifest['sdk_headers_normalized_sha256']
    assert audit['host_sha256'] == compiled['libraries']['libicraft_hostbackend.so']
    assert all(value == '3.39.0' for value in audit['versions'].values())
    for relative, digest in audit['headers_normalized_sha256'].items():
        normalized = (build / 'sdk' / relative).read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(normalized).hexdigest() == digest
    summary = load(run / 'results/summary.json')
    assert summary['case_count'] == len(manifest['cases']) == 107
    assert not summary['device_opened'] and not summary['full_model_executed'] and not summary['mixed_verified']
    records = [json.loads(line) for line in (run / 'results/cases.jsonl').read_text().splitlines()]
    assert len(records) == 107
    numeric = []
    for expected, actual in zip(manifest['cases'], records):
        assert actual['case_id'] == expected['case_id'] and actual['op_id'] == expected['op_id']
        assert actual['expected'] == expected['expected'] and actual['passed']
        assert actual['rejection'] == ('' if expected['expected'] == 'PASS' else expected['expected'])
        for index in range(expected['outputs']):
            path = run / 'results' / expected['case_id'] / f'output{index}.f32'
            reference = package / 'fixtures' / expected['case_id'] / f'expected{index}.f32'
            assert path.read_bytes() == reference.read_bytes()
            values = np.frombuffer(path.read_bytes(), dtype='<f4')
            assert np.isfinite(values).all()
            numeric.append({'case': expected['case_id'], 'output': index,
                            'elements': int(values.size), 'sha256': sha(path), 'bitwise': True})
    registry = [json.loads(line) for line in (run / 'results/registry.jsonl').read_text().splitlines()]
    expected_registry = [(phase, op) for phase in ('before', 'after') for op in (188, 192, 437, 442, 582, 649)]
    assert len(registry) == len(expected_registry) == 12
    for row, (phase, op) in zip(registry, expected_registry):
        present = phase == 'after' or op == 442
        assert row['phase'] == phase and row['op_id'] == op
        assert all(row[key] == present for key in ('supported', 'init', 'forward'))
    assert len(numeric) == 22 and sum(row['elements'] for row in numeric) == 59600
    report = {'status': 'cpu107_current_core_passed', 'cases': 107, 'registry_records': 12,
              'outputs': numeric, 'FP32_elements': 59600, 'NPU_Device_or_Session': False,
              'compiled_current_core': 'software/core/inference/host_cpu_adapter.cpp',
              'kernel_unchanged': True, 'package_manifest_sha256': sha(package / 'manifest.json')}
    destination = evidence / 'cpu.acceptance.json'
    assert not destination.exists()
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('CPU107: 12 registrations, 22 outputs, 59600 FP32 bitwise passed', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', type=Path, default=ROOT / '.local/pose-v1-build/demo-refactor-20261013-r1')
    parser.add_argument('--evidence', type=Path, default=ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1/board')
    parser.add_argument('--cpu-package', type=Path, default=ROOT / '.local/core-refactor/cpu-package')
    parser.add_argument('--reference', type=Path, default=ROOT / '.local/core-refactor/reference')
    parser.add_argument('--model-dir', type=Path, default=Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo\result\icraft_2024'))
    parser.add_argument('--viewer-python', type=Path, default=Path.home() / 'miniconda3/envs/WIFI-densepose/python.exe')
    args = parser.parse_args()
    assert np.__version__ == '2.2.5' and not args.evidence.exists()
    assert load(args.build / 'build-result.json')['status'] == 'compiled_not_board_executed'
    secret = ssh_transport.credential_dialog()
    original = getpass.getpass
    getpass.getpass = lambda message: secret

    def stage(name):
        sys.argv = ['deploy', name, '--build', str(args.build), '--evidence', str(args.evidence),
                    '--cpu-package', str(args.cpu_package), '--model-dir', str(args.model_dir),
                    '--replay-python', sys.executable]
        print('Board stage:', name, flush=True)
        deploy.main()

    def run(python, script, *arguments):
        # Child review processes never receive the SSH password.
        command = [str(python), str(DEMO / script), *map(str, arguments)]
        index = len(list(args.evidence.glob('review-command-*.json')))
        stem = 'review-command-' + str(index)
        process = subprocess.run(command, capture_output=True)
        (args.evidence / (stem + '.stdout.txt')).write_bytes(process.stdout)
        (args.evidence / (stem + '.stderr.txt')).write_bytes(process.stderr)
        (args.evidence / (stem + '.json')).write_text(json.dumps({'args': command, 'exit': process.returncode}) + '\n')
        print(process.stdout.decode(errors='replace'), flush=True)
        assert process.returncode == 0, process.stderr.decode(errors='replace')

    try:
        stage('install')
        stage('cpu')
        reviewCpu(args.evidence, args.build, args.cpu_package)
        stage('short')
        run(sys.executable, 'review.py', 'short', '--evidence', args.evidence, '--reference', args.reference)
        assert len(load(args.evidence / 'short.review.json')['fixed_reference_bitwise_cases']) == 3
        run(sys.executable, 'native_render.py', 'short', '--evidence', args.evidence, '--build', args.build)
        run(args.viewer_python, 'review_video.py', 'short', '--evidence', args.evidence)

        # 所有检查成功后再次只读核验身份、进程和端口，随后关闭认证连接。
        remote = '/tmp/wifi-pose-demo-core-check-20261014-r1'
        sys.argv = ['transport', 'ssh', 'cd ' + remote + ' && python3 board_application_preflight.py final-preflight.json && ss -ltnp',
                    '--log', str(args.evidence / 'final-preflight.stdout.txt')]
        try:
            ssh_transport.main()
        except SystemExit as error:
            assert (error.code or 0) == 0
        sys.argv = ['transport', 'get', remote + '/final-preflight.json', str(args.evidence / 'final-preflight.json'),
                    '--log', str(args.evidence / 'final-preflight-transfer.txt')]
        try:
            ssh_transport.main()
        except SystemExit as error:
            assert (error.code or 0) == 0
        final = load(args.evidence / 'final-preflight.json')
        assert final['fpga_state'] == 'operating'
        assert not any(line.split()[1].startswith('pose_') for line in final['processes'].splitlines()[1:] if len(line.split()) > 1)
        ports = (args.evidence / 'final-preflight.stdout.txt').read_text()
        assert ':39001 ' not in ports and ':8554 ' not in ports
        initial = load(args.evidence / 'host-return/run-host/preflight.json')
        assert final['boot_files'] == initial['boot_files'] and final['libraries'] == initial['libraries']
        print('Board CPU107 and three-window validation completed; no 60-window run', flush=True)
    finally:
        secret = ''
        getpass.getpass = original


if __name__ == '__main__':
    main()
