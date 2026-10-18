"""Fresh bounded ARM build; run only under root's FPAI container ownership.

Does not start Docker Desktop, install anything, deploy, or access the board.
Each process has full stdout/stderr/exit evidence. On failure/timeout the owned
container is stopped and inspected, while cleanup cannot replace the original
error. A running FPAI container is never taken over.
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3/build-read-probe-r2'
WORK = ROOT / '.local/hdmi-live-20261017-r3/read-probe-source-r2'
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
DEST = '/tmp/hdmi-live-read-probe-20261017-r3-r2'
EXPECTED_FILE_SHA = '19b3a995678023c34244e02ca8c92e400e07520442debc73ee786743a49f2f10'
EXPECTED = {
    'libicraft_hostbackend.so': 'd0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130',
    'libicraft_zg330backend.so': '592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57',
    'libicraft_xrt.so': 'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96',
    'libicraft_xir.so': '377a2cac1a8834836503d9805451449d42d99a888b8f96b38d4c2ba8c585af3e',
    'libicraft_utils.so': '99679371aa20e7955e14c39938225df24cdc763d75f26301970fba114f650109',
    'libaxizg330aiu.so': 'd55e48873da61314da712c584e62f8257f63794ecca481e64868361ee5fc7178',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=False)
    steps = []
    cleanup_errors = []
    start_attempted = False
    compiled = False
    stopped = None
    original_error = None
    began = time.monotonic()
    shutil.copyfile(__file__, EVIDENCE / 'actual-builder.py')

    def run(label, args, budget=90, check=True):
        started = time.monotonic()
        timed_out = False
        with (EVIDENCE / (label + '.stdout.txt')).open('xb') as stdout, \
                (EVIDENCE / (label + '.stderr.txt')).open('xb') as stderr:
            proc = subprocess.Popen([DOCKER, *args], cwd=ROOT, stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            try:
                proc.wait(timeout=budget)
            except subprocess.TimeoutExpired:
                timed_out = True
                # Killing the CLI does not prove docker-exec's container process
                # ended. Finally below separately stops and inspects our container.
                try:
                    if os.name == 'nt':
                        kill = subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                                              capture_output=True, timeout=15)
                        (EVIDENCE / (label + '.client-cleanup.txt')).write_bytes(kill.stdout + kill.stderr)
                    else:
                        proc.kill()
                    proc.wait(timeout=15)
                except Exception as error:
                    (EVIDENCE / (label + '.client-cleanup-error.txt')).write_text(str(error))
                    try:
                        proc.kill(); proc.wait(timeout=10)
                    except Exception as secondary:
                        cleanup_errors.append(label + ' CLI still unconfirmed: ' + str(secondary))
        row = {'label': label, 'argv': [DOCKER, *args], 'cwd': str(ROOT), 'pid': proc.pid,
               'exit_code': proc.poll(), 'seconds': time.monotonic() - started,
               'budget_seconds': budget, 'outer_timeout': timed_out}
        steps.append(row)
        dump(EVIDENCE / 'execution.json', steps)
        if check and (timed_out or proc.poll() != 0):
            raise RuntimeError(label + (' outer timeout' if timed_out else ' failed')
                               + '; original stdout/stderr/process status retained')
        return (EVIDENCE / (label + '.stdout.txt')).read_bytes(), row

    state_format = '{"id":{{json .Id}},"image":{{json .Image}},"state":{{json .State}}}'
    try:
        WORK.mkdir(parents=True, exist_ok=False)
        expected_path = ROOT / 'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json'
        if sha(expected_path) != EXPECTED_FILE_SHA or json.loads(expected_path.read_text())['libraries'] != EXPECTED:
            raise RuntimeError('Frozen six-SDK expected identity changed; no container start')
        names = ['ai_read_dma_probe.cpp', 'ai_read_monitor_sdk.hpp', 'ai_monitor_sdk.hpp']
        sources = []
        for name in names:
            source = ROOT / 'FPGA/hdmi_candidate/software' / name
            if name == 'ai_monitor_sdk.hpp' and sha(source) != '77b3ef8341ad791518e64861daafbb74df330ac399bd00f6f3c1ffec3c8c4f53':
                raise RuntimeError('Protected old monitor header changed')
            shutil.copyfile(source, WORK / name)
            sources.append({'path': str(source), 'sha256': sha(source), 'bytes': source.stat().st_size})
        (WORK / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.24)
project(ai_read_dma_probe LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(icraft-zg330backend 3.39.0.0 EXACT REQUIRED)
add_executable(ai_read_dma_probe ai_read_dma_probe.cpp)
target_compile_options(ai_read_dma_probe PRIVATE -Wall -Wextra -Werror)
target_link_options(ai_read_dma_probe PRIVATE -Wl,--no-as-needed)
target_link_libraries(ai_read_dma_probe PRIVATE Icraft::ZG330Backend)
''', encoding='utf-8')
        shutil.copytree(WORK, EVIDENCE / 'source')
        dump(EVIDENCE / 'source-identities.json', {'sources': sources, 'expected_sdk_file_sha256': EXPECTED_FILE_SHA})
        raw, _ = run('initial-state', ['inspect', '--format', state_format, 'FPAI'], 30)
        initial = json.loads(raw)
        if initial['state']['Status'] != 'exited' or initial['state']['Running']:
            raise RuntimeError('FPAI is not stopped; do not interrupt another container owner')
        start_attempted = True
        run('start', ['start', 'FPAI'], 30)
        actual, _ = run('SDK', ['exec', 'FPAI', 'sha256sum',
                               *['/usr/lib/aarch64-linux-gnu/' + name for name in EXPECTED]], 30)
        actual_map = {Path(line.split()[1]).name: line.split()[0] for line in actual.decode().splitlines()}
        if actual_map != EXPECTED:
            raise RuntimeError('Actual six-SDK SHA mismatch; no compilation')
        run('fresh', ['exec', 'FPAI', 'test', '!', '-e', DEST], 30)
        run('copy', ['cp', str(WORK), 'FPAI:' + DEST], 60)
        run('configure', ['exec', 'FPAI', 'cmake', '-S', DEST, '-B', DEST + '/build',
                          '-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
                          '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++', '-DCMAKE_PREFIX_PATH=/usr/cmake'], 90)
        run('build', ['exec', 'FPAI', 'cmake', '--build', DEST + '/build', '--parallel', '2'], 180)
        run('binary-copy', ['cp', 'FPAI:' + DEST + '/build/ai_read_dma_probe', str(EVIDENCE / 'ai_read_dma_probe')], 60)
        elf, _ = run('ELF', ['exec', 'FPAI', 'aarch64-linux-gnu-readelf', '-h', '-d', DEST + '/build/ai_read_dma_probe'], 30)
        binary = EVIDENCE / 'ai_read_dma_probe'
        header = binary.read_bytes()[:20]
        if (len(header) < 20 or header[:7] != b'\x7fELF\x02\x01\x01'
                or int.from_bytes(header[18:20], 'little') != 183
                or b'AArch64' not in elf or b'libicraft_zg330backend.so' not in elf):
            raise RuntimeError('ELF64 little-endian AArch64/backend dependency check failed')
        compiled = True
    except Exception as error:
        original_error = {'error': str(error), 'traceback': traceback.format_exc()}
        dump(EVIDENCE / 'failure.json', original_error)
        print(traceback.format_exc(), file=sys.stderr)
    finally:
        if start_attempted:
            for label, args, budget in [
                ('pre-stop-processes', ['top', 'FPAI', '-eo', 'pid,ppid,args'], 20),
                ('stop', ['stop', '--time', '10', 'FPAI'], 35),
                ('final-state', ['inspect', '--format', state_format, 'FPAI'], 30),
            ]:
                try:
                    raw, row = run(label, args, budget, check=False)
                    if row['outer_timeout'] or row['exit_code'] != 0:
                        cleanup_errors.append(label + ' failed; see full logs')
                    elif label == 'final-state':
                        final = json.loads(raw)
                        stopped = final['state']['Status'] == 'exited' and not final['state']['Running']
                        if not stopped: cleanup_errors.append('Owned FPAI container not confirmed stopped')
                except Exception as error:
                    cleanup_errors.append(label + ': ' + str(error))
            if not compiled:
                try:
                    run('failed-build-tree', ['cp', 'FPAI:' + DEST + '/build', str(EVIDENCE / 'failed-build-tree')],
                        45, check=False)
                except Exception as error:
                    cleanup_errors.append('Failed-build archive: ' + str(error))
        result = {'compiled': compiled, 'board_executed': False, 'Docker_Desktop_started': False,
                  'SDK': EXPECTED, 'container_start_attempted': start_attempted,
                  'container_confirmed_stopped': stopped, 'cleanup_errors': cleanup_errors,
                  'original_error': original_error, 'seconds': time.monotonic() - began,
                  'time': datetime.now(timezone(timedelta(hours=8))).isoformat(),
                  'complete': compiled and stopped is True and not cleanup_errors and original_error is None}
        if compiled: result['binary_sha256'] = sha(EVIDENCE / 'ai_read_dma_probe')
        dump(EVIDENCE / 'result.json', result)
        files = [{'path': path.relative_to(EVIDENCE).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)}
                 for path in sorted(EVIDENCE.rglob('*')) if path.is_file() and path.name != 'manifest.json']
        dump(EVIDENCE / 'manifest.json', {'files': files})
        print(json.dumps(result), flush=True)
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
