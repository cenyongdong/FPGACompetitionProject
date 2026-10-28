"""Assemble a relocatable Top1/no-cutoff release with a verified model pair.

All operations are local. Does not deploy, install autostart or consume a board test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[3]
RESIDENT = ROOT/'software/pose180_pipeline/resident'
RUNTIME = ('startup.py', 'startup_network.py', 'boot_audit.py', 'service.py', 'process_guard.py',
           'run_hdmi_trial.py', 'bounded_log.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def model_selection(directory, original):
    if directory is None:
        folder = ROOT/'model/piw24_pose180_shared-20261024-r1'
        names = {name: expected for name, expected in original['files'].items() if name.startswith('models/')}
        for name, expected in names.items():
            if sha(folder/Path(name).name) != expected:
                raise ValueError('Original epoch99 model differs: '+name)
        return folder, original['model'], names, None
    folder = directory.resolve()
    candidate = json.loads((folder/'candidate.json').read_text(encoding='utf-8'))
    graph = json.loads((folder/'piw24_pose180_ZG.json').read_text())
    raw = (folder/'piw24_pose180_ZG.raw').read_bytes()
    if (graph.get('ai_target') != '@zhuget(330)' or graph.get('icraft_version') != 'v3.39.0'
            or graph.get('swap_mode') or graph.get('params_bytes') != len(raw)
            or graph.get('params_md5') != hashlib.md5(raw).hexdigest()):
        raise ValueError('Candidate target, version or JSON/RAW pairing differs')
    if any(op['_type_key'] not in {'icraft::xir::Input','icraft::xir::Output','icraft::xir::HardOp'}
           for op in graph['ops']):
        raise ValueError('Candidate contains unsupported Host operations')
    inputs = [op for op in graph['ops'] if op['_type_key'] == 'icraft::xir::Input']
    outputs = [op for op in graph['ops'] if op['_type_key'] == 'icraft::xir::Output']
    if len(inputs) != 1 or len(outputs) != 1:
        raise ValueError('Candidate port count differs')
    ports = inputs[0]['outputs'] + outputs[0]['inputs']
    if ([p['dtype']['shape'] for p in ports] != [[1,180,60],[1,180],[1,180,14,3]]
            or any(p['dtype']['element_dtype'] != '@fp(32)' for p in ports)):
        raise ValueError('Candidate public ports differ')
    names = {}
    for name in ('piw24_pose180_ZG.json','piw24_pose180_ZG.raw'):
        actual = sha(folder/name)
        if candidate['model_files'][name]['sha256'] != actual:
            raise ValueError('Candidate identity differs: '+name)
        names['models/'+name] = actual
    return folder, candidate['candidate'], names, candidate


def archive(folder, output, prefix=''):
    with tarfile.open(output, 'x:gz') as result:
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            name = path.relative_to(folder).as_posix()
            info = result.gettarinfo(str(path), arcname=prefix+name)
            info.mode = 0o755 if path.name == 'pose180_demo' or path.suffix == '.sh' else 0o644
            with path.open('rb') as stream:
                result.addfile(info, stream)


def source_snapshot(work, destination):
    files = set()
    # CMake source targets plus the actual project header dependency closure.
    for folder in ('software/core/pose', 'software/core/input', 'software/pose180_pipeline/board', 'software/pose180_pipeline/resident',
                   'tools/nexmon/board', 'tools/pose180', 'demo_v1/shared_fp16'):
        files.update(p for p in (ROOT/folder).rglob('*') if p.suffix in ('.h', '.hpp', '.cpp'))
    files.add(ROOT/'software/pose180_pipeline/CMakeLists.txt')
    files.add(ROOT/'software/core/README.md')
    for dependency in work.glob('*/CMakeFiles/**/*.o.d'):
        for path in re.findall(r'/workspace/[^\s\\]+', dependency.read_text()):
            source = (ROOT/path[len('/workspace/'):]).resolve()
            if source.is_file() and not source.is_relative_to(ROOT/'.local'):
                files.add(source)
    # Configure also needs these sources even when their targets are unbuilt.
    for folder in ('FPGA/hdmi_candidate/diagnostics/native_rgb565_r53/display',
                   'FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/joint'):
        files.update(p for p in (ROOT/folder).iterdir() if p.suffix in ('.h', '.hpp', '.cpp'))
    for name in RUNTIME + ('test_no_threshold.py', 'test_startup.py', 'test_exit_cleanup.py', 'test_startup_robustness.py', 'test_resident.py',
                          'test_adaptive_csi.py', 'test_csi_recovery.py', 'test_native_safety.py'):
        files.add(RESIDENT/name)
    files.add(RESIDENT/'startup-csi.conf')
    files.add(RESIDENT/'STARTUP-PACKAGE.md')
    if (RESIDENT/'KINECT-BOARD-TEST-20261028.md').is_file():
        files.add(RESIDENT/'KINECT-BOARD-TEST-20261028.md')
    files.add(Path(__file__))
    files.add(Path(__file__).with_name('build_startup.py'))
    with tarfile.open(destination, 'x:gz') as result:
        for path in sorted(files):
            result.add(path, arcname=path.relative_to(ROOT).as_posix())
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--build-work', type=Path, help='Reuse an existing verified build without rebuilding or modifying it')
    parser.add_argument('--model-dir', type=Path, help='Independent converted candidate with candidate.json; default is original epoch99')
    parser.add_argument('--default-seconds', type=int, default=0, help='Default manual run duration; 0 runs until manual stop')
    parser.add_argument('--output', type=Path, default=ROOT/'Deliverables')
    args = parser.parse_args()
    work = args.work.resolve()
    build = args.build_work.resolve() if args.build_work else work
    safety_verified = (build/'native-safety-final/result.json').is_file()
    if args.default_seconds < 0:
        parser.error('--default-seconds must be nonnegative')
    original = json.loads((ROOT/'software/pose180_pipeline/evidence/20261025/original-boot/software-identity.json').read_text())
    model_dir, model_name, model_files, candidate = model_selection(args.model_dir, original)
    work.mkdir(parents=True, exist_ok=True)
    release = work/'release'
    release.mkdir()
    board = release/'board'
    board.mkdir()
    deployed = json.loads((ROOT/'FPGA/hdmi_candidate/default_boot.json').read_text())
    if deployed['hardware_profile'] != 'probe-free-drain-filter-v1':
        raise ValueError('Release launcher requires the currently qualified hardware profile')
    copy(build/'arm64/pose180_demo', board/'pose180_demo')
    with (board/'pose180_demo').open('rb') as stream:
        header = stream.read(20)
    if header[:6] != b'\x7fELF\x02\x01' or int.from_bytes(header[18:20], 'little') != 183:
        raise ValueError('Expected a little-endian ARM64 ELF executable')
    for name in RUNTIME:
        copy(RESIDENT/name, board/name)
    copy(RESIDENT/'startup-csi.conf', board/'csi.conf')
    for name in model_files:
        copy(model_dir/Path(name).name, board/name)
    if candidate:
        copy(model_dir/'candidate.json', release/'validation/model-candidate.json')
        copy(model_dir/'host-comparison.json', release/'validation/model-host-comparison.json')
    boot_files = {entry['name']: entry['sha256'] for entry in original['protected_original_boot_files']
                  if entry['name'] in ('BOOT.BIN', 'IMAGE', 'FMQLMP~1.DTB', 'UENV.TXT')}
    boot_files['BOOT.BIN'] = deployed['BOOT_sha256']
    boot = ROOT/deployed['BOOT_path']
    if sha(boot) != deployed['BOOT_sha256']:
        raise ValueError('Qualified BOOT differs')
    copy(boot, release/'boot/BOOT.BIN')
    for name in ('qualification.json', 'package-review.json'):
        copy(ROOT/deployed['hardware_work']/'reports'/name, release/'boot'/name)
    identity = dict(package=work.name, selection=dict(top_k=1, strict_score_threshold=None, single_person_stability=True),
                    model=model_name, input_source='live_csi', csi_alignment='adaptive',
                    phase_preprocessing='original', hardware_profile=deployed['hardware_profile'],
                    BOOT_sha256=deployed['BOOT_sha256'], boot_files=boot_files,
                    verified_boot_ids=[deployed['runtime_boot_id']], libraries=original['SDK_libraries'],
                    SDK_autostart=False, automatic_retry=False,
                    runtime_safety='release-blocked-v1' if safety_verified else 'see-build-record',
                    presentation_filter='single-person-continuity-v1: centre/relative smoothing, 4-hit relocation, bounded steps',
                    files={p.relative_to(board).as_posix():sha(p) for p in board.rglob('*') if p.is_file()})
    write(board/'identity.json', identity)
    for script, action in [('start', 'start'), ('stop', 'stop'), ('status', 'status'), ('check', 'check'), ('recover', 'recover')]:
        defaults = ' --seconds '+str(args.default_seconds) if action == 'start' else ''
        (release/(script+'.sh')).write_text('#!/bin/sh\nset -eu\nroot=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec python3 "$root/board/startup.py" '+action+defaults+' "$@"\n', newline='\n')
    for name in ('resident.mjs', 'presentation.mjs', 'full_record.mjs', 'resident_archive.mjs'):
        copy(ROOT/'software/pose180_pipeline/host'/name, release/'pc/software/pose180_pipeline/host'/name)
    copy(ROOT/'demo_v1/web/scene.js', release/'pc/demo_v1/web/scene.js')
    three = ROOT/'software/pc_viewer/node_modules/three'
    for name in ('build/three.module.js', 'build/three.core.js', 'examples/jsm/controls/OrbitControls.js', 'LICENSE'):
        copy(three/name, release/'pc/software/pc_viewer/node_modules/three'/name)
    (release/'start-pc.ps1').write_text('param([string]$Board="192.168.50.49")\n$ErrorActionPreference="Stop"\n& node (Join-Path $PSScriptRoot "pc/software/pose180_pipeline/host/resident.mjs") --board $Board --mode view --http-port 39380\nexit $LASTEXITCODE\n', newline='\n')
    count = source_snapshot(build, release/'core-sources.tar.gz')
    copy(RESIDENT/'STARTUP-PACKAGE.md', release/'STARTUP-GUIDE.md')
    if candidate:
        copy(RESIDENT/'KINECT-BOARD-TEST-20261028.md', release/'KINECT-BOARD-TEST-20261028.md')
    (release/'README.md').write_text(
        '# '+work.name+'\n\n'
        '模型：`'+model_name+'`。TopK=1、无置信度阈值、CPU单人连续性滤波、实时自适应CSI。\n\n'
        '复用指定构建，安全验证范围见validation记录，未实板验证；保留原HDMI和PC性能指标栏。\n\n'
        '以root执行 `sh check.sh` 核对，`sh start.sh` 手动开始，`sh status.sh` 查看，`sh stop.sh` 请求正常停止。'
        '默认处理期为'+str(args.default_seconds)+'秒（0表示手动停止）；可用 `sh start.sh --seconds 300` 显式指定。\n\n'
        '比较时一次只运行一个包；上一包退出且SDK／HDMI安全关闭、独占与临时网络清理确认后才启动下一包。'
        '`release_blocked`表示完成未证明，必须保留资源与独占，不强杀、不自动重试或切换模型。\n\n'
        '未知boot_id按STARTUP-GUIDE.md处理，不跳过BOOT身份检查。包内BOOT仅为备份，不会自动安装或重启。'
        'PC运行 `start-pc.ps1`；停止PC不影响板端。\n\n'
        '完整操作与边界见 [启动说明](STARTUP-GUIDE.md)；实际构建、故障注入与模型身份在 `validation/`。\n',
        encoding='utf-8', newline='\n')
    for name in ('build.json', 'verification.json', 'no-threshold-test/result.json', 'startup-test/result.json'):
        copy(build/name, release/'validation'/name)
    for source, destination in [('comparison.json','comparison.json'),
            ('exit-cleanup-final/result.json','exit-cleanup.json'),
            ('robustness-verified/result.json','robustness.json'),
            ('native-safety-final/result.json','native-safety.json'),
            ('release-guard-final.log','release-guard.log'),('hdmi-resources-final.log','hdmi-resources.log'),
            ('source-final-arm64.log','source-final-arm64.log')]:
        if (build/source).is_file():
            copy(build/source, release/'validation'/destination)
    write(release/'validation/build-reuse.json', dict(build_work=str(build), native_sha256=identity['files']['pose180_demo']))
    manifest = dict(package=work.name, selection=identity['selection'], model=identity['model'],
                    runtime_safety=identity['runtime_safety'],
                    input='live_csi/adaptive; original preprocessing', outputs=['HDMI', 'PC:39385'],
                    runtime_seconds_default=args.default_seconds, SDK_autostart=False, automatic_retry=False,
                    board_tested=False, hardware_rebuilt=False, core_source_files=count,
                    validation='Local C++/mock/PC checks only; no new board or collection run',
                    files={p.relative_to(release).as_posix():dict(bytes=p.stat().st_size, sha256=sha(p))
                           for p in release.rglob('*') if p.is_file()})
    write(release/'manifest.json', manifest)
    args.output.mkdir(exist_ok=True, parents=True)
    output = args.output/(work.name+'.tar.gz')
    archive(release, output, work.name+'/')
    result = dict(archive=str(output), bytes=output.stat().st_size, sha256=sha(output),
                  native_sha256=identity['files']['pose180_demo'], model=identity['model'],
                  top_k=1, score_threshold=None, single_person_stability=True,
                  BOOT_sha256=identity['BOOT_sha256'], board_tested=False)
    write(work/'package.json', result)
    (output.with_suffix(output.suffix+'.sha256')).write_text(result['sha256']+'  '+output.name+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
