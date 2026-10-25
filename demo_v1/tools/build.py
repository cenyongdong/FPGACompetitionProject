"""使用现有FPAI/SDK编译；保留原生日志与实际退出码，不运行板端负载。"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, tarfile

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'demo_v1'
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
ORIGIN = ROOT / '.local/shared-stability-delivery-20261015-r2'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--read-diagnostic', action='store_true')
    parser.add_argument('--d47-isolation', action='store_true')
    a = parser.parse_args()
    if a.d47_isolation and not a.read_diagnostic: raise ValueError('Isolation requires diagnostic overlay')
    if not a.tag.replace('-', '').isalnum():
        raise ValueError('Invalid build tag')
    out = D / 'build' / a.tag
    out.mkdir(parents=True, exist_ok=False)
    steps = []
    def run(*args):
        r = subprocess.run([DOCKER, *args], capture_output=True)
        stem = str(len(steps)).zfill(2)
        (out / (stem + '.stdout')).write_bytes(r.stdout)
        (out / (stem + '.stderr')).write_bytes(r.stderr)
        steps.append({'argv': list(args), 'exit': r.returncode})
        (out / 'steps.json').write_text(json.dumps(steps, indent=2))
        if r.returncode:
            raise RuntimeError(r.stderr.decode(errors='replace') + r.stdout.decode(errors='replace')[-4000:])
        return r.stdout
    expected = json.loads((ORIGIN / 'package.json').read_text())
    actual = run('exec', 'FPAI', 'sha256sum', *['/usr/lib/aarch64-linux-gnu/' + n for n in expected['libraries']]).decode()
    if {Path(line.split()[1]).name: line.split()[0] for line in actual.splitlines()} != expected['libraries']:
        raise ValueError('Build SDK library identity differs')
    manifest = json.loads((D / 'shared-source.json').read_text())
    for name, digest in manifest['files'].items():
        if sha(D / 'shared_fp16' / name) != digest:
            raise ValueError('Shared source changed: ' + name)
    remote = '/tmp/demo-v1-build-' + a.tag
    run('exec', 'FPAI', 'test', '!', '-e', remote)
    run('exec', 'FPAI', 'mkdir', remote)
    for name in ['CMakeLists.txt', 'board', 'shared_fp16', 'output']:
        run('cp', str(D / name), 'FPAI:' + remote + '/')
    if a.read_diagnostic:
        run('cp', str(D / 'diagnostics'), 'FPAI:' + remote + '/')
    run('exec', 'FPAI', 'cmake', '-S', remote, '-B', remote + '/build',
        '-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
        '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++', '-DCMAKE_PREFIX_PATH=/usr/cmake', '-DCMAKE_BUILD_TYPE=Release',
        '-DDEMO_READ_DIAGNOSTIC=' + ('ON' if a.read_diagnostic else 'OFF'),
        '-DDEMO_D47_ISOLATION=' + ('ON' if a.d47_isolation else 'OFF'))
    run('exec', 'FPAI', 'cmake', '--build', remote + '/build', '--parallel', '2')
    run('cp', 'FPAI:' + remote + '/build/pose_demo_v1', str(out / 'pose_demo_v1'))
    package = out / 'package'; package.mkdir()
    shutil.copyfile(out / 'pose_demo_v1', package / 'pose_demo_v1')
    if a.d47_isolation:
        run('cp', 'FPAI:' + remote + '/build/pose_static_read', str(package / 'pose_static_read'))
    for name in ['fixtures', 'models']:
        shutil.copytree(ORIGIN / name, package / name)
    for name in ['board_guard.py', 'preflight.py']:
        shutil.copyfile(D / 'tools' / name, package / name)
    identity = {k: expected[k] for k in ['expected_boot_files', 'libraries', 'expected_linux_version']}
    identity['files'] = {p.relative_to(package).as_posix(): sha(p) for p in package.rglob('*') if p.is_file()}
    policy = json.loads((ORIGIN / 'policy.json').read_text())
    for name, key in [('piw24_shared_ZG.json', 'graph_json_sha256'), ('piw24_shared_ZG.raw', 'graph_raw_sha256')]:
        if identity['files']['models/' + name] != policy[key]:
            raise ValueError('Protected shared model identity changed: ' + name)
    identity['source'] = sha(D / 'shared-source.json')
    (package / 'identity.json').write_text(json.dumps(identity, indent=2))
    with tarfile.open(out / 'package.tar', 'w') as archive:
        for p in package.rglob('*'):
            if p.is_file():
                info = archive.gettarinfo(str(p), arcname=p.relative_to(package).as_posix())
                if p.name in ['pose_demo_v1', 'pose_static_read']: info.mode = 0o755
                with p.open('rb') as source: archive.addfile(info, source)
    print(json.dumps({'compiled': True, 'board_executed': False, 'package': str(out / 'package.tar'), 'sha256': sha(out / 'package.tar')}))

if __name__ == '__main__': main()
