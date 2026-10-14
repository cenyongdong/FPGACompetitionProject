"""记录离线分析器和SDK无关计时合同的实际结果；不连接设备。"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def verify(output):
    output.mkdir(parents=True)
    records = []
    def run(name, argv):
        p = subprocess.run(argv, cwd=ROOT, capture_output=True)
        (output / (name + '.stdout.txt')).write_bytes(p.stdout)
        (output / (name + '.stderr.txt')).write_bytes(p.stderr)
        records.append({'name': name, 'argv': argv, 'exit': p.returncode})
        (output / 'checks.json').write_text(json.dumps(records, indent=2) + '\n')
        if p.returncode:
            raise RuntimeError('Offline check failed: ' + name)
    run('analysis-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_analyze.py', '-v'])
    binary = output / 'clock_selftest.exe'
    run('clock-native-compile', ['g++', '-std=c++17', '-O2', '-pthread', '-Wall', '-Wextra', '-Werror',
                                '-I' + str(HERE), str(HERE / 'clock_selftest.cpp'), '-o', str(binary)])
    for name in ('basic', 'thread', 'capacity'):
        run('clock-' + name, [str(binary), name, str(output / name)])
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*') if p.is_file()}
    (output / 'result.json').write_text(json.dumps({'status': 'offline_contracts_passed',
        'checks': records, 'source_sha256': files, 'NPU_or_board_executed': False,
        'Windows_thread_CPU_supported': False}, indent=2) + '\n')
    return records


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    verify(a.output.resolve())
    print('Offline contracts passed; no device inference')
