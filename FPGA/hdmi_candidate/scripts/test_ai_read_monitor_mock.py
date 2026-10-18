"""Compile/run isolated local mocks only. No real SDK, Docker, network or board."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3/mock-ai-read-monitor-r1/source'
DEFAULT = FIXTURES.parent / 'run-r2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / 'actual-runner.py')
    steps = []
    start = time.monotonic()
    compiler = shutil.which('g++')
    env = os.environ.copy()
    if compiler:
        env['PATH'] = str(Path(compiler).parent) + os.pathsep + env.get('PATH', '')

    def run(label, argv, budget=30, selected_env=None):
        stdout_path, stderr_path = out / (label + '.stdout.txt'), out / (label + '.stderr.txt')
        began = time.monotonic()
        timed_out = False
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            proc = subprocess.Popen([str(x) for x in argv], cwd=out,
                                    env=selected_env or env, stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            try:
                proc.wait(timeout=budget)
            except subprocess.TimeoutExpired:
                timed_out = True
                if os.name == 'nt':
                    kill = subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                                          capture_output=True, timeout=15)
                    (out / (label + '.cleanup.txt')).write_bytes(kill.stdout + kill.stderr)
                else:
                    proc.kill()
                proc.wait(timeout=15)
        row = {'label': label, 'argv': [str(x) for x in argv], 'pid': proc.pid,
               'exit_code': proc.returncode, 'seconds': time.monotonic() - began,
               'budget_seconds': budget, 'timed_out': timed_out}
        steps.append(row)
        (out / 'execution.json').write_text(json.dumps(steps, indent=2) + '\n')
        if timed_out:
            raise RuntimeError(label + ' timeout; complete logs/process exit retained, no retry')
        return row, stdout_path.read_text(encoding='utf-8', errors='replace'), stderr_path.read_text(encoding='utf-8', errors='replace')

    try:
        if not compiler:
            result = {'executed': False, 'reason': 'No existing local g++ found; fixtures prepared only',
                      'real_SDK': False, 'board': False, 'Docker': False}
            (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps(result))
            return 0
        row, _, _ = run('compiler-version', [compiler, '--version'], 10)
        if row['exit_code']:
            raise RuntimeError('Existing compiler version command failed')
        production = out / 'production-source'
        production.mkdir()
        origin = ROOT / 'FPGA/hdmi_candidate/software'
        inputs = []
        for name in ['ai_read_monitor_sdk.hpp', 'ai_read_dma_probe.cpp', 'ai_monitor_sdk.hpp', 'dma_probe_evidence.hpp']:
            path = origin / name
            shutil.copyfile(path, production / name)
            inputs.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)})
        shutil.copytree(FIXTURES, out / 'fixtures')
        fixtures = out / 'fixtures'
        for path in sorted(FIXTURES.rglob('*')):
            if path.is_file():
                inputs.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)})
        inputs.append({'path': compiler, 'bytes': Path(compiler).stat().st_size, 'sha256': sha(Path(compiler))})
        (out / 'inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
        flags = ['-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread',
                 '-I' + str(fixtures / 'mock'), '-I' + str(production)]
        helper, probe = out / 'helper_cases.exe', out / 'probe_mock.exe'
        row, _, _ = run('compile-helper', [compiler, *flags, fixtures / 'helper_cases.cpp', '-o', helper], 45)
        if row['exit_code']:
            raise RuntimeError('Mock helper compilation failed; original logs retained')
        row, _, _ = run('compile-probe', [compiler, *flags, '-include', fixtures / 'windows_io_compat.hpp',
                                         production / 'ai_read_dma_probe.cpp', '-o', probe], 45)
        if row['exit_code']:
            raise RuntimeError('Mock probe compilation failed; original logs retained')
        row, stdout, _ = run('helper-cases', [helper], 10)
        if row['exit_code'] or 'MOCK_HELPER_PASS 48' not in stdout:
            raise RuntimeError('Local helper cases failed')
        cases = []
        expected_codes = {'normal': 0, 'write_fault_4096': 71, 'read_fault_4096': 71,
                          'write_fault_freeze_timeout': 71, 'mismatch_4096': 72,
                          'late_file_collision': 74, 'identity_changed': 1,
                          'initial_sequence': 1, 'initial_busy': 1, 'arm_clock_stopped': 1, 'after_probe': 1}
        for mode, expected_code in expected_codes.items():
            case = out / mode
            case.mkdir()
            trace = case / 'trace.jsonl'
            events_path = case / 'mock-events.txt'
            selected_env = env.copy()
            selected_env.update(AI_READ_MOCK_CASE=mode, AI_READ_MOCK_EVENTS=str(events_path),
                                AI_READ_MOCK_COLLISION_PATH=str(trace) + '.4096.actual.bin')
            row, stdout, stderr = run('case-' + mode, [probe, trace], 10, selected_env)
            if row['exit_code'] != expected_code:
                raise RuntimeError(mode + ': unexpected exit ' + str(row['exit_code']))
            events = events_path.read_text().splitlines() if events_path.exists() else []
            log = [json.loads(line) for line in trace.read_text().splitlines()]
            if events.count('OPEN') != 1:
                raise RuntimeError(mode + ': opened more than one mock Device')
            if mode in ('identity_changed', 'initial_sequence', 'initial_busy', 'arm_clock_stopped', 'after_probe'):
                if any(e.startswith(('MALLOC', 'WRITE', 'READ')) for e in events):
                    raise RuntimeError(mode + ': pretransfer rejection started a load')
            else:
                if events.count('ARM') != 1 or events.count('FREEZE') != 1 or events.count('MIG_CAPTURE') != 1:
                    raise RuntimeError(mode + ': diagnostic lifecycle repeated or missing')
                if mode == 'normal':
                    if events.count('FREE') != 1 or 'AI_READ_DMA_ROUNDTRIP_PASS' not in stdout:
                        raise RuntimeError('normal mock missing release/PASS')
                    if not events.index('READ 1048576') < events.index('FREEZE') < events.index('MIG_CAPTURE') < events.index('FREE'):
                        raise RuntimeError('normal capture/free ordering')
                else:
                    if 'FREE' in events or 'WRITE 65536' in events or 'AI_READ_DMA_ROUNDTRIP_PASS' in stdout:
                        raise RuntimeError(mode + ': affected load continued/freed/claimed pass')
                sizes = [64, 4096, 65536, 1048576] if mode == 'normal' else [64]
                if mode == 'mismatch_4096':
                    sizes.append(4096)
                for size in sizes:
                    source = Path(str(trace) + f'.{size}.source.bin').read_bytes()
                    actual = Path(str(trace) + f'.{size}.actual.bin').read_bytes()
                    expected = bytes(((i * 37) ^ (i >> 9) ^ size) & 255 for i in range(size))
                    if source != expected or len(actual) != size:
                        raise RuntimeError(mode + ': complete byte evidence does not match independent pattern')
                    if mode == 'mismatch_4096' and size == 4096:
                        if actual == source or actual[13] == source[13]:
                            raise RuntimeError('mismatch mock did not exercise actual data difference')
                    elif actual != source:
                        raise RuntimeError(mode + ': unexpected complete byte difference')
                if mode in ('write_fault_4096', 'read_fault_4096', 'write_fault_freeze_timeout'):
                    if Path(str(trace) + '.4096.actual.bin').exists():
                        raise RuntimeError(mode + ': fabricated actual after failed/unreturned read')
                    if events.index('original_exception_what') > events.index('FREEZE'):
                        raise RuntimeError(mode + ': diagnostic preceded original exception serialization')
                if mode == 'late_file_collision':
                    if Path(str(trace) + '.4096.actual.bin').read_bytes() != b'KEEP':
                        raise RuntimeError('late evidence file overwritten')
                    if any(x.get('event') in ('mismatch_stop_allocation_retained', 'roundtrip_pass') and x.get('bytes') == 4096 for x in log):
                        raise RuntimeError('data compared before complete evidence save')
                if mode == 'mismatch_4096':
                    tags = [(x.get('event'), x.get('bytes')) for x in log]
                    if tags.index(('read_returned_and_complete_bytes_saved', 4096)) > tags.index(('mismatch_stop_allocation_retained', 4096)):
                        raise RuntimeError('comparison preceded complete byte save')
            cases.append({'mode': mode, 'exit_code': expected_code, 'mock_events': events,
                          'trace_rows': len(log), 'stderr_original_preserved': 'ORIGINAL_' in stderr})
        for collision in ['trace', 'binary']:
            case = out / ('preexisting-' + collision)
            case.mkdir()
            trace = case / 'trace.jsonl'
            target = trace if collision == 'trace' else Path(str(trace) + '.64.actual.bin')
            target.write_bytes(b'KEEP')
            events = case / 'mock-events.txt'
            selected_env = env.copy()
            selected_env.update(AI_READ_MOCK_CASE='normal', AI_READ_MOCK_EVENTS=str(events))
            row, _, _ = run('collision-' + collision, [probe, trace], 10, selected_env)
            if row['exit_code'] != 1 or target.read_bytes() != b'KEEP' or events.exists():
                raise RuntimeError('Preexisting evidence was overwritten or Device opened')
            cases.append({'mode': 'preexisting-' + collision, 'exit_code': 1, 'no_Device_Open': True})
        result = {'passed': True, 'helper_cases': 48, 'probe_cases': cases,
                  'real_SDK': False, 'board': False, 'Docker': False, 'seconds': time.monotonic() - start,
                  'limits': ['Mock register/memory behavior is not real SDK or hardware validation',
                             'Windows shim maps fsync to _commit; O_NOFOLLOW/O_CLOEXEC are not validated',
                             'No physical timing, throughput, DMA drainage or numerical model validation']}
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: result[k] for k in ['passed', 'helper_cases', 'real_SDK', 'board', 'Docker', 'seconds']}))
        return 0
    except Exception as error:
        (out / 'failure.json').write_text(json.dumps({'error': str(error), 'traceback': traceback.format_exc()}, indent=2) + '\n')
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        files = [{'path': path.relative_to(out).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)}
                 for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'manifest.json']
        (out / 'manifest.json').write_text(json.dumps({'files': files}, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
