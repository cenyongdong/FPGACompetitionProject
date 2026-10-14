"""板端新目录的有限计时包装；阶段之间人工/代理审阅，失败不重跑。"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import traceback


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def snapshot(run, prefix):
    for name in ('buddyinfo', 'pagetypeinfo', 'meminfo', 'vmstat', 'version'):
        (run / (prefix + '.' + name)).write_bytes(Path('/proc/' + name).read_bytes())
    (run / (prefix + '.dmesg.txt')).write_bytes(subprocess.check_output(['dmesg']))
    (run / (prefix + '.processes.txt')).write_bytes(subprocess.check_output(['ps', '-eo', 'pid,comm,args']))


def stop_child(child):
    if child and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('baseline', 'wall', 'sdk'), required=True)
    parser.add_argument('--cycles', type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.cycles <= 8:
        parser.error('1..8 cycles, at most24 forwards; no automatic extension')
    root = Path(__file__).resolve().parent
    run = root / ('run-' + args.mode)
    run.mkdir()  # 已有目录直接拒绝，不能复用失败Session/现场。
    child = None
    code = 1
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Timing wrapper interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        snapshot(run, 'before')
        package = json.loads((root / 'package.json').read_text())
        for relative, expected in package['files'].items():
            if sha(root / relative) != expected:
                raise ValueError('Delivery identity changed: ' + relative)
        binary = root / 'pose_engine_timing'
        elf = binary.read_bytes()[:20]
        if elf[:6] != b'\x7fELF\x02\x01' or int.from_bytes(elf[18:20], 'little') != 183:
            raise ValueError('Expected ARM64 little-endian binary')
        if sha(binary) != package['binary_sha256']:
            raise ValueError('Binary identity differs')
        if Path('/proc/version').read_text().strip() != package['expected_linux_version']:
            raise ValueError('Kernel identity changed')
        for relative, expected in package['sdk_headers_normalized_sha256'].items():
            actual = hashlib.sha256((Path('/usr/include') / relative).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            if actual != expected:
                raise ValueError('SDK public header changed: ' + relative)
        for name, expected in package['libraries'].items():
            if sha(Path('/usr/lib/aarch64-linux-gnu') / name) != expected:
                raise ValueError('SDK library changed: ' + name)
        with (run / 'preflight.stdout.txt').open('wb') as out:
            subprocess.run([sys.executable, str(root / 'board_application_preflight.py'), str(run / 'preflight.json')],
                           stdout=out, stderr=subprocess.STDOUT, check=True, timeout=20)
        preflight = json.loads((run / 'preflight.json').read_text())
        if preflight['fpga_state'] != 'operating' or preflight['boot_files'] != package['expected_boot_files']:
            raise ValueError('FPGA/BOOT identity differs')
        if preflight['SDK_packages'] != ['customop arm64 3.39.0', 'icraft arm64 3.39.0']:
            raise ValueError('SDK package version differs')
        # 包装器自身python进程不占用NPU；拒绝已有项目推理/视频进程。
        if any(line.split()[1].startswith('pose_') for line in preflight['processes'].splitlines()[1:] if len(line.split()) > 1):
            raise ValueError('Existing pose process; do not interfere')
        identity = {'package_sha256': sha(root / 'package.json'), 'binary_sha256': sha(binary),
                    'cycles': args.cycles, 'mode': args.mode,
                    'board_preflight_identity': {'boot_files': preflight['boot_files'], 'libraries': preflight['libraries'],
                                                 'kernel': package['expected_linux_version']}}
        save(run / 'run-identity.json', identity)
        previous = {'wall': 'baseline', 'sdk': 'wall'}.get(args.mode)
        if previous:
            prior = root / ('run-' + previous)
            if (prior / 'exit.txt').read_text().strip() != '0':
                raise ValueError('Previous timing mode failed')
            old = json.loads((prior / 'run-identity.json').read_text())
            if any(old[key] != identity[key] for key in ('package_sha256', 'binary_sha256', 'cycles', 'board_preflight_identity')):
                raise ValueError('Previous mode conditions differ')
            # 成功退出不能代替时间线审查；上阶段报告必须由analyze.py产出。
            report = json.loads((prior / 'analysis/report.json').read_text())
            if report['status'] != 'finite_numeric_timing_evidence':
                raise ValueError('Previous timing evidence not reviewed')
        dynamic = subprocess.run(['ldd', str(binary)], capture_output=True, check=True)
        (run / 'ldd.txt').write_bytes(dynamic.stdout + dynamic.stderr)
        if b'not found' in dynamic.stdout + dynamic.stderr:
            raise ValueError('Unresolved runtime library')
        command = [str(binary), '--package', str(root), '--output', str(run / 'results'),
                   '--mode', args.mode, '--cycles', str(args.cycles), '--allow-device-init']
        save(run / 'command.json', {'argv': command, 'timeout_seconds': 120, 'kill_grace_seconds': 5})
        with (run / 'stdout.txt').open('wb') as out, (run / 'stderr.txt').open('wb') as err:
            child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
            (run / 'child.pid').write_text(str(child.pid))
            try:
                code = child.wait(timeout=120)
            except subprocess.TimeoutExpired:
                stop_child(child)
                code = 124
                save(run / 'timeout.json', {'deadline_seconds': 120, 'stopped_no_retry': True,
                                          'graceful_device_cleanup_verified': False})
        snapshot(run, 'after')
        if code == 0 and (run / 'stderr.txt').stat().st_size:
            raise ValueError('Unexpected stderr; preserve and review')
        if (run / 'before.dmesg.txt').read_bytes() != (run / 'after.dmesg.txt').read_bytes():
            raise ValueError('Kernel log changed; preserve and stop')
    except BaseException as error:
        stop_child(child)
        code = code if code else 1
        save(run / 'wrapper-failure.json', {'error': str(error), 'traceback': traceback.format_exc(), 'retry': False})
    finally:
        stop_child(child)
        try:
            if not (run / 'after.meminfo').exists():
                snapshot(run, 'after')
        except Exception as error:
            save(run / 'snapshot-error.json', {'error': str(error)})
            code = code if code else 1
        (run / 'exit.txt').write_text(str(code) + '\n')
        hashes = {p.relative_to(run).as_posix(): sha(p) for p in sorted(run.rglob('*')) if p.is_file()}
        save(run / 'evidence-files.json', hashes)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
