"""在新目录执行原107例Host检查器，核验实际ARM身份并完整归档。"""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import tarfile
import time
import traceback

ROOT = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def snapshot(run, prefix):
    for name in ('buddyinfo', 'pagetypeinfo', 'meminfo', 'vmstat'):
        (run / (prefix + '.' + name)).write_bytes(Path('/proc/' + name).read_bytes())
    (run / (prefix + '.dmesg.txt')).write_bytes(subprocess.check_output(['dmesg']))


def main():
    os.chdir(ROOT)
    run = ROOT / 'run-cpu'
    assert not run.exists(), 'Preserve prior CPU run'
    run.mkdir()
    child = None
    code = 1
    try:
        snapshot(run, 'before')
        build = json.loads((ROOT / 'build-result.json').read_text())
        package = ROOT / 'cpu-package'
        manifest = json.loads((package / 'manifest.json').read_text())
        for line in (ROOT / 'files.sha256').read_text().splitlines():
            digest, name = line.split('  ', 1)
            assert sha(ROOT / name) == digest, name
        for line in (package / 'files.sha256').read_text().splitlines():
            digest, name = line.split('  ', 1)
            assert sha(package / name) == digest, name
        binary = ROOT / 'pose_core_cpu_check'
        assert sha(binary) == build['regression_programs']['pose_core_cpu_check']
        assert sha(package / 'piw24_ZG.json') == build['graph_sha256'] == manifest['graph_sha256']
        headers = {}
        for relative, expected in manifest['sdk_headers_normalized_sha256'].items():
            raw = (Path('/usr/include') / relative).read_bytes().replace(b'\r\n', b'\n')
            headers[relative] = hashlib.sha256(raw).hexdigest()
            assert headers[relative] == expected, relative
        versions = {name: subprocess.check_output(['dpkg-query', '-W', '-f=${Version}', name], text=True)
                    for name in ('icraft:arm64', 'customop:arm64')}
        assert all(value == '3.39.0' for value in versions.values())
        host = sha('/usr/lib/aarch64-linux-gnu/libicraft_hostbackend.so')
        assert host == manifest['host_library_sha256'] == build['libraries']['libicraft_hostbackend.so']
        (run / 'sdk-audit.json').write_text(json.dumps({'versions': versions,
            'headers_normalized_sha256': headers, 'host_sha256': host}, indent=2) + '\n')
        subprocess.run(['python3', 'board_application_preflight.py', str(run / 'preflight.json')],
                       check=True, stdout=(run / 'preflight.stdout.txt').open('wb'))
        preflight = json.loads((run / 'preflight.json').read_text())
        assert preflight['fpga_state'] == 'operating'
        assert next(item['sha256'] for item in preflight['boot_files'] if item['name'] == 'BOOT.BIN') == 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
        assert not any(line.split()[1].startswith('pose_') for line in preflight['processes'].splitlines()[1:] if len(line.split()) > 1)
        dynamic = subprocess.run(['ldd', str(binary)], capture_output=True, check=True)
        (run / 'ldd.txt').write_bytes(dynamic.stdout + dynamic.stderr)
        assert b'not found' not in dynamic.stdout and b'zg330backend' not in dynamic.stdout and b'axizg330' not in dynamic.stdout
        (run / 'input-identities.json').write_text(json.dumps({'binary': sha(binary),
            'graph': sha(package / 'piw24_ZG.json'), 'package_manifest': sha(package / 'manifest.json'),
            'build_result': sha(ROOT / 'build-result.json')}, indent=2) + '\n')

        # 单个Host检查器生命周期，保留原300秒预算，不创建NPU Device或Session。
        began = time.monotonic()
        with (run / 'run.stdout.log').open('wb') as stdout, (run / 'run.stderr.log').open('wb') as stderr:
            command = [str(binary), '--graph', str(package / 'piw24_ZG.json'),
                       '--fixtures', str(package / 'fixtures'), '--output', str(run / 'results')]
            child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                code = child.wait(timeout=300)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
                code = 124
        (run / 'budget.json').write_text(json.dumps({'exit': code, 'seconds': time.monotonic() - began,
            'CPU_budget_seconds': 300, 'NPU_forward': False, 'compaction': False}) + '\n')
    except Exception:
        (run / 'manager.failure.txt').write_text(traceback.format_exc())
    finally:
        if child and child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)
        snapshot(run, 'after')
        (run / 'exit.txt').write_text(str(code) + '\n')
        (run / 'processes.txt').write_bytes(subprocess.check_output(['ps', '-eo', 'pid,comm,args']))
        (run / 'ports.txt').write_bytes(subprocess.check_output(['ss', '-ltnp']))
        with (run / 'files.sha256').open('w') as stream:
            for path in sorted(run.rglob('*')):
                if path.is_file() and path.name != 'files.sha256':
                    stream.write(sha(path) + '  ' + path.relative_to(run).as_posix() + '\n')
        with tarfile.open(ROOT / 'return-cpu.tar', 'w') as archive:
            archive.add(run, arcname=run.name)
        (ROOT / 'finished-cpu.json').write_text(json.dumps({'exit': code,
            'archive_sha256': sha(ROOT / 'return-cpu.tar')}) + '\n')
        print('CPU107 finished', code, flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
