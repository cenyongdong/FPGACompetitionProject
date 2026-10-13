"""Authorized memory-only SSH, new package, bounded demo plus host display."""
from pathlib import Path
import argparse, getpass, hashlib, json, shutil, subprocess, sys, tarfile, time
ROOT = Path(__file__).resolve().parents[2]
DEMO = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/pose-v1'))
import ssh_transport as transport
from archive_bytes import extract_bytes


# 核验传输包、源码及实际产物身份，不将新哈希回填旧证据。
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


# 按新目录部署和有界阶段运行；失败先取消本批播放器，再完整回传归档。
def main():
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['install', 'cpu', 'short', 'demo'])
    p.add_argument('--build', type=Path, default=ROOT / '.local/pose-v1-build/demo-refactor-20261013-r1')
    p.add_argument('--evidence', type=Path, default=ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1/board')
    p.add_argument('--remote', default='/tmp/wifi-pose-demo-refactor-20261013-r1')
    p.add_argument('--headless', action='store_true')
    p.add_argument('--model-dir', type=Path, default=Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo\result\icraft_2024'))
    p.add_argument('--cpu-package', type=Path, default=ROOT / '.local/core-refactor/cpu-package')
    p.add_argument('--credential-dialog', action='store_true')
    p.add_argument('--replay-python', type=Path, default=Path(sys.executable))
    a = p.parse_args()
    assert a.remote == '/tmp/wifi-pose-demo-refactor-20261013-r1' or a.remote in ('/tmp/wifi-pose-demo-20261011-r4',
        '/tmp/wifi-pose-demo-20261011-r5')
    E = a.evidence
    mode = 'host' if a.stage == 'install' else a.stage
    if a.stage == 'install':
        assert not E.exists()
        E.mkdir()
        t = E / 'transfer'
        t.mkdir()
        m = json.loads((a.build / 'build-result.json').read_text(encoding='utf-8'))
        for rel, digest in m['baseline_sources'].items():
            assert sha(ROOT / rel) == digest
        for rel, digest in m.get('core_python_sources', {}).items():
            assert sha(ROOT / rel) == digest
        for rel, digest in m['demo_sources'].items():
            if Path(rel).suffix in ('.cpp', '.hpp') or Path(rel).name in ('CMakeLists.txt', 'baseline-lock.json'):
                assert sha(ROOT / rel) == digest
        for name in [*m['programs'], 'build-result.json']:
            shutil.copyfile(a.build / name, t / name)
        shutil.copyfile(DEMO / 'board/runner.py', t / 'runner.py')
        shutil.copyfile(DEMO / 'board/cpu_runner.py', t / 'cpu_runner.py')
        shutil.copyfile(a.build / 'pose_core_cpu_check', t / 'pose_core_cpu_check')
        assert sha(a.build / 'pose_core_cpu_check') == m['regression_programs']['pose_core_cpu_check']
        shutil.copytree(a.cpu_package, t / 'cpu-package')
        shutil.copyfile(ROOT / 'tools/pose-v1/board_application_preflight.py', t / 'board_application_preflight.py')
        model = a.model_dir
        assert sha(model / 'piw24_ZG.json') == m['graph_sha256']
        assert sha(model / 'piw24_ZG.raw') == m['raw_sha256']
        (t / 'models').mkdir()
        for n in ('piw24_ZG.json', 'piw24_ZG.raw'):
            shutil.copyfile(model / n, t / 'models' / n)
        (t / 'files.sha256').write_text(''.join((sha(p) + '  ' + p.relative_to(t).as_posix() + '\n' for p in sorted(t.rglob('*')) if p.is_file())),
            encoding='utf-8', newline='\n')
        with tarfile.open(E / 'transfer.tar', 'w') as archive:
            for item in sorted(t.rglob('*')):
                if item.is_file():
                    info = archive.gettarinfo(str(item), item.relative_to(t).as_posix())
                    info.mtime = 0
                    with item.open('rb') as f:
                        archive.addfile(info, f)
        (E / 'delivery.json').write_text(json.dumps({'transfer_sha256': sha(E / 'transfer.tar'),
            'build_sha256': sha(a.build / 'build-result.json'), 'demo_sources': {p.relative_to(ROOT).as_posix(): sha(p) for p in DEMO.rglob('*') if p.is_file() and '__pycache__' not in p.parts},
            'input_contract_unchanged': True, 'sources_explicitly_refactored': True, 'core_python_sources': m.get('core_python_sources', {})}, indent=2) + '\n', encoding='utf-8')
    else:
        assert json.loads((E / 'host.review.json').read_text())['exit'] == 0
        if a.stage == 'short' and a.remote == '/tmp/wifi-pose-demo-refactor-20261013-r1':
            assert json.loads((E / 'cpu.acceptance.json').read_text())['status'] == 'cpu107_current_core_passed'
        if a.stage == 'demo':
            assert json.loads((E / 'short.review.json').read_text())['status'] == 'end_to_end_demo_passed'
            assert json.loads((E / 'short.video-review.json').read_text())['status'] == 'original_VPU_video_real_pose_geometry_verified'
    secret = transport.credential_dialog() if a.credential_dialog else getpass.getpass('Authorized Lite password (memory only): ')
    original = transport.getpass.getpass
    transport.getpass.getpass = lambda _: secret
    serial = 0
    started = False
    finished = False
    peer = None

    def call(*args):
        nonlocal serial
        serial += 1
        sys.argv = ['transport', *map(str, args), '--log', str(E / (mode + '-transport-' + str(serial) + '.txt'))]
        if mode == 'cpu':
            sys.argv += ['--timeout', '360']
        try:
            transport.main()
        except SystemExit as e:
            return e.code or 0
        return 0
    try:
        if a.stage == 'install':
            assert call('ssh', 'set -eu; test ! -e ' + a.remote + '; mkdir ' + a.remote) == 0
            assert call('put', E / 'transfer.tar', a.remote + '/transfer.tar') == 0
            command = 'set -eu; cd ' + a.remote + '; echo "' + sha(E / 'transfer.tar') + '  transfer.tar" | sha256sum -c -; tar -xf transfer.tar; chmod u+x pose_demo pose_display_worker pose_demo_transport_test pose_core_cpu_check; python3 runner.py host'
            assert call('ssh', command) == 0
            finished = True
        elif a.stage == 'cpu':
            call('ssh', 'cd ' + a.remote + ' && python3 cpu_runner.py')
            finished = True
        else:
            assert call('ssh', 'cd ' + a.remote + ' && python3 -c "import subprocess; from pathlib import Path; assert not Path(\'run-' + mode + "').exists(); p=subprocess.Popen(['python3','runner.py','" + mode + "'],stdin=subprocess.DEVNULL,stdout=open('" + mode + "-manager.stdout','wb'),stderr=open('" + mode + "-manager.stderr','wb'),start_new_session=True); Path('" + mode + '-manager.pid\').write_text(str(p.pid))"') == 0
            started = True
            output = E / (mode + '-host')
            args = [str(a.replay_python), str(DEMO / 'host/run.py'),
                '--frames', str(3 if mode == 'short' else 60), '--hz', '2', '--output', str(output)]
            if a.headless:
                args.append('--headless')
            peer = subprocess.Popen(args, stdout=(E / (mode + '-peer.stdout')).open('wb'),
                stderr=(E / (mode + '-peer.stderr')).open('wb'))
            begin = time.monotonic()
            while time.monotonic() - begin < 195:
                status = E / (mode + '-status-' + str(serial) + '.json')
                assert call('ssh', 'cd ' + a.remote + ' && python3 -c "import json; from pathlib import Path; Path(\'status-' + mode + ".json').write_text(json.dumps({'finished':Path('finished-" + mode + '.json\').exists()}))"') == 0
                assert call('get', a.remote + '/status-' + mode + '.json', status) == 0
                if json.loads(status.read_text())['finished']:
                    finished = True
                    break
                if peer.poll() is not None and peer.returncode != 0:
                    call('ssh', 'touch ' + a.remote + '/abort-' + mode)
                time.sleep(3)
            else:
                raise TimeoutError('Finite demo controller deadline')
            status = E / (mode + '-finished.json')
            assert call('get', a.remote + '/finished-' + mode + '.json', status) == 0
            if json.loads(status.read_text())['exit'] != 0 and output.is_dir():
                (output / 'stop.request').write_text('board-exited-error\n')
            try:
                peer.wait(timeout=15)
            except subprocess.TimeoutExpired:
                if output.is_dir():
                    (output / 'stop.request').write_text('peer-finite-wait-exceeded\n')
                try:
                    peer.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    peer.terminate()
                    peer.wait(timeout=5)
                (E / (mode + '-peer-timeout.txt')).write_text('Host peer finite wait exceeded; board archive still collected\n')
        assert call('get', a.remote + '/return-' + mode + '.tar', E / ('return-' + mode + '.tar')) == 0
        extract_bytes(E / ('return-' + mode + '.tar'), E / (mode + '-return'))
        d = E / (mode + '-return/run-' + mode)
        for line in (d / 'files.sha256').read_text().splitlines():
            h, n = line.split('  ', 1)
            assert sha(d / n) == h
        code = int((d / 'exit.txt').read_text())
        kernel = (d / 'before.dmesg.txt').read_bytes() == (d / 'after.dmesg.txt').read_bytes()
        if mode in ('host', 'cpu'):
            (E / (mode + '.review.json')).write_text(json.dumps({'exit': code, 'kernel_unchanged': kernel,
                'archive_sha256': sha(E / 'return-host.tar')}) + '\n')
        print('Returned demo', mode, 'exit', code, 'kernel unchanged', kernel, 'peer',
            peer.returncode if peer else None)
        assert code == 0 and kernel and (not peer or peer.returncode == 0), 'Preserve error and stop; no retry'
    finally:
        if started and (not finished):
            call('ssh', 'touch ' + a.remote + '/abort-' + mode)
        if peer and peer.poll() is None:
            peer.terminate()
            peer.wait(timeout=5)
        secret = ''
        transport.getpass.getpass = original


if __name__ == '__main__':
    main()
