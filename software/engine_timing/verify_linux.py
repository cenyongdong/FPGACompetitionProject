"""在既有FPAI的Linux主机编译器运行SDK无关计时合同，验证线程CPU/rusage。"""
from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'software/demo'))
from build_support import Docker


def verify(output, tag):
    if not re.fullmatch(r'engine-timing-native-[A-Za-z0-9_-]+', tag):
        raise ValueError('Invalid isolated native tag')
    output.mkdir(parents=True)
    docker = Docker(output)
    remote = '/tmp/' + tag
    docker.run('exec', 'FPAI', 'test', '!', '-e', remote)
    docker.run('exec', 'FPAI', 'mkdir', remote)
    for name in ('application_clock.hpp', 'clock_selftest.cpp'):
        docker.run('cp', str(HERE / name), 'FPAI:' + remote + '/' + name)
    docker.run('exec', 'FPAI', 'g++', '-std=gnu++17', '-O2', '-pthread', '-Wall', '-Wextra', '-Werror',
               '-I' + remote, remote + '/clock_selftest.cpp', '-o', remote + '/clock_selftest')
    for name in ('basic', 'thread', 'capacity'):
        docker.run('exec', 'FPAI', remote + '/clock_selftest', name, remote + '/' + name)
    docker.run('cp', 'FPAI:' + remote + '/basic', str(output / 'basic'))
    docker.run('cp', 'FPAI:' + remote + '/capacity', str(output / 'capacity'))
    rows = [json.loads(line) for line in (output / 'basic/trace.jsonl').read_text().splitlines()]
    if len(rows) != 3 or not all(row['thread_cpu_ns'] is not None and row['voluntary_switches'] is not None for row in rows):
        raise ValueError('Linux CPU/rusage coverage differs')
    (output / 'result.json').write_text(json.dumps({'status': 'Linux_thread_CPU_rusage_contracts_passed',
        'synthetic_rows': rows, 'SDK_linked': False, 'NPU_Device_or_Session': False, 'board_connected': False}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    verify(args.output.resolve(), args.tag)
    print('Linux clock contracts passed; no SDK/device execution')
