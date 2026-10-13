"""在新目录导出锁定源码，核验既有SDK和厂商库，再进行FPAI构建。"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEMO = Path(__file__).resolve().parent
VENDOR = Path(r'D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现\单路PLIM+VPU\fpai_demo_package_26040702\fpai_demo_package_26040702\deps\thirdparty')
DOCKER = r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
PROGRAMS = ('pose_demo', 'pose_display_worker', 'pose_demo_transport_test')
REGRESSIONS = ('pose_core_cpu_check', 'pose_core_preprocess_check', 'pose_core_render_check',
               'pose_core_access_unit_selftest', 'pose_core_display_selftest', 'pose_core_failure_selftest',
               'pose_core_stage_selftest', 'pose_core_invocation_selftest', 'pose_core_producer_selftest',
               'pose_core_identity_selftest', 'pose_core_read_selftest')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Docker:
    """每条命令独立记录退出码及完整stdout/stderr；失败即返回原错误。"""
    def __init__(self, output):
        self.output = output
        self.steps = []

    def run(self, *args):
        process = subprocess.run([DOCKER, *args], capture_output=True)
        index = len(self.steps)
        stem = f'build-step-{index:03d}'
        (self.output / (stem + '.stdout.txt')).write_bytes(process.stdout)
        (self.output / (stem + '.stderr.txt')).write_bytes(process.stderr)
        self.steps.append({'args': list(args), 'exit': process.returncode, 'stem': stem})
        (self.output / 'build-steps.json').write_text(json.dumps(self.steps, indent=2) + '\n', encoding='utf-8')
        with (self.output / 'build.log').open('ab') as log:
            log.write((repr(args) + '\n').encode() + process.stdout + process.stderr)
        if process.returncode:
            raise RuntimeError(f'Build step {index} exited {process.returncode}: ' +
                               process.stderr[-4000:].decode(errors='replace'))
        return process.stdout


def exportBaseline(lock, output):
    # 先核验所有输入，身份变化时不导出替代源码。
    aliases = set()
    for relative, item in lock['build_files'].items():
        assert sha(ROOT / relative) == item['sha256'], relative
        name = item['destination']
        assert Path(name).name == name and name not in aliases
        aliases.add(name)
    for relative, digest in lock['vendor_files'].items():
        assert sha(VENDOR / relative) == digest, relative

    baseline = output / 'baseline'
    baseline.mkdir()
    for relative, item in lock['build_files'].items():
        shutil.copyfile(ROOT / relative, baseline / item['destination'])
    return baseline


def auditSdk(lock, docker, output):
    # 对ARM实际头文件及动态库进行快照，不用Windows版本号替代ARM身份。
    snapshot = output / 'sdk'
    snapshot.mkdir()
    for relative, digest in lock['sdk_headers_normalized_sha256'].items():
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        docker.run('cp', '-L', 'FPAI:/usr/include/' + relative, str(destination))
        normalized = destination.read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(normalized).hexdigest() == digest, relative
    for package in ('icraft:arm64', 'customop:arm64'):
        version = docker.run('exec', 'FPAI', 'dpkg-query', '-W', '-f=${Version}', package)
        assert version.strip() == b'3.39.0', package

    libraries = {}
    names = ('libicraft_hostbackend.so', 'libicraft_zg330backend.so', 'libicraft_xrt.so',
             'libicraft_xir.so', 'libicraft_utils.so', 'libaxizg330aiu.so')
    for name in names:
        docker.run('cp', '-L', 'FPAI:/usr/lib/aarch64-linux-gnu/' + name, str(snapshot / name))
        libraries[name] = sha(snapshot / name)
    assert libraries['libicraft_hostbackend.so'] == lock['host_library_sha256']
    assert libraries['libicraft_zg330backend.so'] == lock['zg_library_sha256']
    return libraries


def stageVendor(lock, docker, remote):
    docker.run('exec', 'FPAI', 'mkdir', '-p', remote + '/vendor/libs')
    for relative in ('include/live', 'include/openssl'):
        docker.run('cp', str(VENDOR / relative), 'FPAI:' + remote + '/vendor/' + Path(relative).name)
    for relative in lock['vendor_files']:
        if relative.startswith('a/'):
            docker.run('cp', str(VENDOR / relative), 'FPAI:' + remote + '/vendor/libs/' + Path(relative).name)


def compilePrograms(docker, remote, output):
    # SDK无关TCP检查先运行；ARM构建通过不表示已执行板端测试。
    flags = ['-std=gnu++17', '-O2', '-DNDEBUG', '-pthread', '-I' + remote + '/baseline']
    docker.run('exec', 'FPAI', 'g++', *flags, remote + '/baseline/tcp_receiver.cpp',
               remote + '/baseline/tcp_transport_check.cpp', '-o', remote + '/transport-native')
    result = docker.run('exec', 'FPAI', remote + '/transport-native', '--self-test')
    (output / 'transport-native.txt').write_bytes(result)

    docker.run('exec', 'FPAI', 'cmake', '-S', remote + '/demo', '-B', remote + '/build',
               '-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
               '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++', '-DCMAKE_BUILD_TYPE=Release',
               '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG', '-DCMAKE_PREFIX_PATH=/usr/cmake',
               '-DBASELINE_DIR=' + remote + '/baseline', '-DVENDOR_DIR=' + remote + '/vendor')
    docker.run('exec', 'FPAI', 'cmake', '--build', remote + '/build', '--parallel', '2')

    binaries = {}
    for name in (*PROGRAMS, *REGRESSIONS):
        docker.run('cp', 'FPAI:' + remote + '/build/' + name, str(output / name))
        binaries[name] = sha(output / name)
    needed = docker.run('exec', 'FPAI', 'aarch64-linux-gnu-readelf', '-d', remote + '/build/pose_demo')
    (output / 'needed.txt').write_bytes(needed)
    cpu_needed = docker.run('exec', 'FPAI', 'aarch64-linux-gnu-readelf', '-d', remote + '/build/pose_core_cpu_check')
    assert b'zg330backend' not in cpu_needed and b'axizg330' not in cpu_needed
    (output / 'cpu-needed.txt').write_bytes(cpu_needed)
    return binaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', default='demo-refactor-20261013-r1')
    args = parser.parse_args()
    assert re.fullmatch(r'demo-[a-zA-Z0-9_-]+', args.tag)
    output = ROOT / '.local/pose-v1-build' / args.tag
    assert not output.exists(), 'Preserve previous build'
    output.mkdir(parents=True)
    lock = json.loads((DEMO / 'baseline-lock.json').read_text(encoding='utf-8'))

    baseline = exportBaseline(lock, output)
    source = output / 'demo'
    shutil.copytree(DEMO, source, ignore=shutil.ignore_patterns('__pycache__'))
    docker = Docker(output)
    remote = '/tmp/pose-' + args.tag + '-build'
    docker.run('exec', 'FPAI', 'test', '!', '-e', remote)
    docker.run('exec', 'FPAI', 'mkdir', remote)
    docker.run('cp', str(baseline), 'FPAI:' + remote + '/baseline')
    docker.run('cp', str(source), 'FPAI:' + remote + '/demo')
    libraries = auditSdk(lock, docker, output)
    stageVendor(lock, docker, remote)
    binaries = compilePrograms(docker, remote, output)

    report = {
        'status': 'compiled_not_board_executed',
        'programs': {name: binaries[name] for name in PROGRAMS},
        'regression_programs': {name: binaries[name] for name in REGRESSIONS},
        'libraries': libraries,
        'baseline_manifest_sha256': sha(DEMO / 'baseline-lock.json'),
        'baseline_sources': {relative: item['sha256'] for relative, item in lock['build_files'].items()},
        'demo_sources': {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(DEMO.rglob('*'))
                         if path.is_file() and '__pycache__' not in path.parts},
        'core_python_sources': {'software/core/input/csi_io.py': sha(ROOT / 'software/core/input/csi_io.py')},
        'vendor_files': lock['vendor_files'],
        'sdk_headers_normalized_sha256': lock['sdk_headers_normalized_sha256'],
        'graph_sha256': lock['graph_sha256'],
        'raw_sha256': lock['raw_sha256'],
        'source_migration': lock['source_migration'],
        'HDMI': False,
        'prior_Host107_reused': True,
        'new_Host107_executed': False,
    }
    (output / 'build-result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Demo built', output, binaries['pose_demo'])


if __name__ == '__main__':
    main()
