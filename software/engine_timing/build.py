"""核验隔离包与ARM SDK后交叉编译；不SSH、不部署、不运行模型。"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'software/demo'))
from build_support import Docker, auditSdk


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(source, tag):
    if not re.fullmatch(r'engine-timing-[A-Za-z0-9_-]+', tag):
        raise ValueError('Invalid fresh build tag')
    manifest_path = source / 'source-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for relative, digest in manifest['files'].items():
        if sha(source / relative) != digest:
            raise ValueError('Prepared source changed: ' + relative)
    output = ROOT / '.local/pose-v1-build' / tag
    if output.exists():
        raise FileExistsError('Preserve previous build')
    output.mkdir(parents=True)
    docker = Docker(output)
    lock = json.loads((ROOT / 'software/demo/baseline-lock.json').read_text())
    if sha(ROOT / 'software/demo/baseline-lock.json') != manifest['baseline_lock_sha256']:
        raise ValueError('Current core lock changed since preparation')
    libraries = auditSdk(lock, docker, output)
    # 这两个公共接口用于本次新采样；核对真实ARM声明与本机阅读版本。
    for relative in ('icraft-xrt/core/session.h', 'icraft-xrt/dev/zg330_device.h'):
        destination = output / 'sdk' / relative
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            docker.run('cp', '-L', 'FPAI:/usr/include/' + relative, str(destination))
        windows = Path(r'C:\Icraft\CLI v3.39.0\include') / relative
        if destination.read_bytes().replace(b'\r\n', b'\n') != windows.read_bytes().replace(b'\r\n', b'\n'):
            raise ValueError('ARM/Windows public timing header differs: ' + relative)
    remote = '/tmp/' + tag
    docker.run('exec', 'FPAI', 'test', '!', '-e', remote)
    docker.run('cp', str(source), 'FPAI:' + remote)
    docker.run('exec', 'FPAI', 'cmake', '-S', remote, '-B', remote + '/build',
               '-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
               '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++', '-DCMAKE_BUILD_TYPE=Release',
               '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG', '-DCMAKE_PREFIX_PATH=/usr/cmake')
    docker.run('exec', 'FPAI', 'cmake', '--build', remote + '/build', '--parallel', '2')
    docker.run('cp', 'FPAI:' + remote + '/build/pose_engine_timing', str(output / 'pose_engine_timing'))
    needed = docker.run('exec', 'FPAI', 'aarch64-linux-gnu-readelf', '-d', remote + '/build/pose_engine_timing')
    (output / 'needed.txt').write_bytes(needed)
    result = {'status': 'compiled_not_board_executed', 'source_manifest_sha256': sha(manifest_path),
              'binary_sha256': sha(output / 'pose_engine_timing'), 'libraries': libraries,
              'source_directory': str(source), 'docker_directory': remote}
    (output / 'build-result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    result = build(args.source.resolve(), args.tag)
    print('Compiled, no board execution:', result['binary_sha256'])
