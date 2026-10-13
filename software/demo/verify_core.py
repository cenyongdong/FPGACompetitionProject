"""复用冻结检查器核验正式核心；不修改测试源码，也不在本机模拟NPU成功。"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'tools/pose-v1/evidence/core-refactor-20261013-r1'
sys.path.insert(0, str(ROOT / 'tools'))
from core_refactor_format import tokens

DOCKER = r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
LOCK = ROOT / 'software/demo/baseline-lock.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def refresh():
    # 当前修订哈希与原修订分开，原冻结清单绝不回写。
    manifest = load(LOCK)
    for relative, item in manifest['build_files'].items():
        if relative.startswith('software/core/'):
            item['sha256'] = sha(ROOT / relative)
    save(LOCK, manifest)
    migration_path = EVIDENCE / 'source-migration.json'
    migration = load(migration_path)
    for row in migration['files']:
        row['new_sha256'] = sha(ROOT / row['destination'])
    save(migration_path, migration)


def static():
    frozen = load(EVIDENCE / 'frozen-sources.before.json')
    for relative, digest in frozen.items():
        assert sha(ROOT / relative) == digest, 'Frozen source changed: ' + relative
    old_lock = load(EVIDENCE / 'baseline-lock.before.json')
    for relative, item in old_lock['build_files'].items():
        assert sha(ROOT / relative) == item['sha256'], relative
    manifest = load(LOCK)
    aliases = {}
    for relative, item in manifest['build_files'].items():
        assert sha(ROOT / relative) == item['sha256'], relative
        assert item['destination'] not in aliases
        aliases[item['destination']] = relative
    migration = load(EVIDENCE / 'source-migration.json')
    cpp_files = []
    for row in migration['files']:
        if row['destination'].endswith(('.cpp', '.hpp')):
            original = (ROOT / row['original']).read_text(encoding='utf-8')
            current = (ROOT / row['destination']).read_text(encoding='utf-8')
            assert tokens(original) == tokens(current), row['destination']
            cpp_files.append(row['destination'])
    cmake = (ROOT / 'software/demo/CMakeLists.txt').read_text(encoding='utf-8')
    production = re.findall(r'\$\{BASELINE_DIR\}/([\w.]+)', cmake)
    for alias in production:
        if alias != 'tcp_transport_check.cpp':
            assert aliases[alias].startswith('software/core/'), alias
    result = {'status': 'static_passed', 'original_lock_files_unchanged': len(old_lock['build_files']),
              'frozen_files_unchanged': len(frozen), 'core_cpp_token_equivalent': len(cpp_files),
              'production_uses_formal_core': True, 'original_tests_unchanged': True}
    save(EVIDENCE / 'static-review.json', result)
    print(json.dumps(result), flush=True)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def native(tag):
    static()
    output = ROOT / '.local/core-refactor' / ('native-' + tag)
    assert not output.exists(), 'Preserve previous regression'
    output.mkdir(parents=True)
    source = output / 'source'
    source.mkdir()
    manifest = load(LOCK)
    for relative, item in manifest['build_files'].items():
        shutil.copyfile(ROOT / relative, source / item['destination'])
    old = output / 'original'
    old.mkdir()
    for relative, item in load(EVIDENCE / 'baseline-lock.before.json')['build_files'].items():
        shutil.copyfile(ROOT / relative, old / item['destination'])
    for name in ('preprocess_check.cpp', 'skeleton_render_check.cpp'):
        shutil.copyfile(ROOT / 'software/pose_v1/src' / name, old / name)

    inputs = output / 'inputs'
    inputs.mkdir()
    original_codec = module(ROOT / 'tools/pose-v1/csi_io.py', 'original_codec')
    current_codec = module(ROOT / 'software/core/input/csi_io.py', 'current_codec')
    data = Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo\data\wifipose\test_data\csi')
    csi_sources = []
    for index, number in enumerate((308, 309, 310)):
        name = f'S11_01_{number}'
        raw = original_codec.load_mat(data / (name + '.mat'))
        first = original_codec.encode_window(raw, 1000000 + index, 0)
        second = current_codec.encode_window(current_codec.load_mat(data / (name + '.mat')), 1000000 + index, 0)
        assert first == second and len(second) == 86432
        (inputs / (name + '.csi')).write_bytes(second)
        csi_sources.append({'source': name, 'MAT_sha256': sha(data / (name + '.mat')),
                            'record_sha256': sha(inputs / (name + '.csi')), 'codec_bitwise': True})
    remote = '/tmp/pose-core-refactor-native-' + tag
    steps = []

    def run(*args):
        process = subprocess.run([DOCKER, *args], capture_output=True)
        index = len(steps)
        stem = f'step-{index:03d}'
        (output / (stem + '.stdout.txt')).write_bytes(process.stdout)
        (output / (stem + '.stderr.txt')).write_bytes(process.stderr)
        steps.append({'args': list(args), 'exit': process.returncode, 'stem': stem})
        save(output / 'steps.json', steps)
        if process.returncode:
            raise RuntimeError(f'Native step {index} failed: ' + process.stderr.decode(errors='replace'))
        return process.stdout

    run('exec', 'FPAI', 'test', '!', '-e', remote)
    run('exec', 'FPAI', 'mkdir', remote)
    for name in ('source', 'original', 'inputs'):
        run('cp', str(output / name), 'FPAI:' + remote + '/' + name)
    run('exec', 'FPAI', 'mkdir', remote + '/results')
    flags = ('-std=gnu++17', '-O2', '-DNDEBUG', '-pthread', '-Wall', '-Wextra', '-Wpedantic', '-ffp-contract=off')
    suites = {
        'tcp': ('tcp_transport_check.cpp', 'tcp_receiver.cpp'),
        'access_unit': ('access_unit_selftest.cpp', 'h264_access_unit.cpp', 'access_unit_channel.cpp'),
        'failure': ('host_failure_evidence_selftest.cpp', 'host_failure_evidence.cpp'),
        'stage': ('host_stage_observation_selftest.cpp', 'host_stage_observation.cpp'),
        'invocation': ('invocation_evidence_selftest.cpp', 'invocation_evidence.cpp'),
        'producer': ('producer_count_observation_selftest.cpp', 'producer_count_observation.cpp'),
        'identity': ('tensor_identity_selftest.cpp', 'tensor_identity_observation.cpp'),
        'read': ('input_read_selftest.cpp', 'input_read_contract.cpp'),
        'display_worker': ('display_worker.cpp', 'display_protocol.cpp', 'skeleton_render.cpp'),
        'display': ('display_process_selftest.cpp', 'display_process.cpp', 'display_protocol.cpp',
            'skeleton_render.cpp'),
        'preprocess': ('preprocess_check.cpp', 'preprocess.cpp'),
        'render': ('skeleton_render_check.cpp', 'skeleton_render.cpp'),
    }
    for name, files in suites.items():
        run('exec', 'FPAI', 'g++', *flags, '-I' + remote + '/source',
            *(remote + '/source/' + file for file in files), '-o', remote + '/' + name)
        if name == 'display_worker':
            continue
        args = ('--self-test',) if name in ('tcp', 'preprocess') else ()
        if name in ('failure', 'stage', 'invocation', 'producer', 'identity'):
            args = (remote + '/results/' + name,)
        elif name == 'display':
            args = (remote + '/display_worker', remote + '/results/display')
        elif name == 'render':
            args = ('--self-test', remote + '/results/render')
        text = run('exec', 'FPAI', remote + '/' + name, *args)
        print(name, text.decode(errors='replace').strip()[:180], flush=True)

    # 对照原实现，保持同一编译器、选项和测试输入；不比较计时值。
    for name in ('preprocess', 'render'):
        files = suites[name]
        run('exec', 'FPAI', 'g++', *flags, '-I' + remote + '/original',
            *(remote + '/original/' + file for file in files), '-o', remote + '/' + name + '-original')
    run('exec', 'FPAI', remote + '/render-original', '--self-test', remote + '/results/render-original')
    for row in csi_sources:
        name = row['source']
        for binary in ('preprocess', 'preprocess-original'):
            run('exec', 'FPAI', remote + '/' + binary, remote + '/inputs/' + name + '.csi',
                remote + '/results/' + name + '.' + binary + '.f32')
    run('cp', 'FPAI:' + remote + '/results', str(output / 'results'))
    result = output / 'results'
    for row in csi_sources:
        name = row['source']
        original = result / (name + '.preprocess-original.f32')
        actual = result / (name + '.preprocess.f32')
        reference = ROOT / '.local/core-refactor/reference/reference' / (name + '.input.f32')
        assert actual.read_bytes() == original.read_bytes() == reference.read_bytes(), name
        row['preprocess_fixed_reference_bitwise'] = True
    compared = []
    for path in (result / 'render').iterdir():
        if path.suffix in ('.ppm', '.nv12', '.nv21', '.rgb565le', '.rgb24'):
            assert path.read_bytes() == (result / 'render-original' / path.name).read_bytes()
            compared.append({'file': path.name, 'sha256': sha(path), 'bytes': path.stat().st_size})
    report = {'status': 'native_regressions_passed', 'test_suites': 11, 'inputs': csi_sources,
              'renderer_bitwise_files': compared, 'full_output_directory': str(output),
              'steps_sha256': sha(output / 'steps.json'), 'NPU_or_VPU_executed': False}
    save(EVIDENCE / ('native-' + tag + '.review.json'), report)
    print('All native suites and fixed byte comparisons passed', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('refresh', 'static', 'native'))
    parser.add_argument('--tag', default='20261013-r1')
    args = parser.parse_args()
    assert re.fullmatch(r'[a-zA-Z0-9_-]+', args.tag)
    if args.stage == 'native':
        native(args.tag)
    else:
        globals()[args.stage]()


if __name__ == '__main__':
    main()
