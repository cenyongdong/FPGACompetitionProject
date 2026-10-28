"""Assemble a relocatable Top1/no-cutoff release from the shared core and original model.

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
RUNTIME = ('startup.py', 'startup_network.py', 'boot_audit.py', 'service.py',
           'run_hdmi_trial.py', 'bounded_log.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


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
    for folder in ('software/core', 'software/pose180_pipeline/board', 'software/pose180_pipeline/resident',
                   'tools/nexmon/board', 'tools/pose180', 'demo_v1/shared_fp16'):
        files.update(p for p in (ROOT/folder).rglob('*') if p.suffix in ('.h', '.hpp', '.cpp'))
    files.add(ROOT/'software/pose180_pipeline/CMakeLists.txt')
    for dependency in work.glob('*/CMakeFiles/**/*.o.d'):
        for path in re.findall(r'/workspace/[^\s\\]+', dependency.read_text()):
            source = (ROOT/path[len('/workspace/'):]).resolve()
            if source.is_file() and not source.is_relative_to(ROOT/'.local'):
                files.add(source)
    # Configure also needs these sources even when their targets are unbuilt.
    for folder in ('FPGA/hdmi_candidate/diagnostics/native_rgb565_r53/display',
                   'FPGA/hdmi_candidate/diagnostics/native_rgb565_r47/joint'):
        files.update(p for p in (ROOT/folder).iterdir() if p.suffix in ('.h', '.hpp', '.cpp'))
    for name in RUNTIME + ('test_no_threshold.py', 'test_startup.py', 'test_resident.py',
                          'test_adaptive_csi.py', 'test_csi_recovery.py'):
        files.add(RESIDENT/name)
    files.add(RESIDENT/'startup-csi.conf')
    files.add(RESIDENT/'STARTUP-PACKAGE.md')
    files.add(Path(__file__))
    files.add(Path(__file__).with_name('build_startup.py'))
    with tarfile.open(destination, 'x:gz') as result:
        for path in sorted(files):
            result.add(path, arcname=path.relative_to(ROOT).as_posix())
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'Deliverables')
    args = parser.parse_args()
    work = args.work.resolve()
    release = work/'release'
    release.mkdir()
    board = release/'board'
    board.mkdir()
    original = json.loads((ROOT/'software/pose180_pipeline/evidence/20261025/original-boot/software-identity.json').read_text())
    deployed = json.loads((ROOT/'FPGA/hdmi_candidate/default_boot.json').read_text())
    if deployed['hardware_profile'] != 'probe-free-drain-filter-v1':
        raise ValueError('Release launcher requires the currently qualified hardware profile')
    copy(work/'arm64/pose180_demo', board/'pose180_demo')
    with (board/'pose180_demo').open('rb') as stream:
        header = stream.read(20)
    if header[:6] != b'\x7fELF\x02\x01' or int.from_bytes(header[18:20], 'little') != 183:
        raise ValueError('Expected a little-endian ARM64 ELF executable')
    for name in RUNTIME:
        copy(RESIDENT/name, board/name)
    copy(RESIDENT/'startup-csi.conf', board/'csi.conf')
    for name, expected in original['files'].items():
        if name.startswith('models/'):
            source = ROOT/'model/piw24_pose180_shared-20261024-r1'/Path(name).name
            if sha(source) != expected:
                raise ValueError('Original epoch99 model differs: '+name)
            copy(source, board/name)
    boot_files = {entry['name']: entry['sha256'] for entry in original['protected_original_boot_files']
                  if entry['name'] in ('BOOT.BIN', 'IMAGE', 'FMQLMP~1.DTB', 'UENV.TXT')}
    boot_files['BOOT.BIN'] = deployed['BOOT_sha256']
    boot = ROOT/deployed['BOOT_path']
    if sha(boot) != deployed['BOOT_sha256']:
        raise ValueError('Qualified BOOT differs')
    copy(boot, release/'boot/BOOT.BIN')
    for name in ('qualification.json', 'package-review.json'):
        copy(ROOT/deployed['hardware_work']/'reports'/name, release/'boot'/name)
    identity = dict(package=work.name, selection=dict(top_k=1, strict_score_threshold=None),
                    model=original['model'], input_source='live_csi', csi_alignment='adaptive',
                    phase_preprocessing='original', hardware_profile=deployed['hardware_profile'],
                    BOOT_sha256=deployed['BOOT_sha256'], boot_files=boot_files,
                    verified_boot_ids=[deployed['runtime_boot_id']], libraries=original['SDK_libraries'],
                    SDK_autostart=False, automatic_retry=False,
                    files={p.relative_to(board).as_posix():sha(p) for p in board.rglob('*') if p.is_file()})
    write(board/'identity.json', identity)
    for script, action in [('start', 'start'), ('stop', 'stop'), ('status', 'status'), ('check', 'check')]:
        (release/(script+'.sh')).write_text('#!/bin/sh\nset -eu\nroot=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec python3 "$root/board/startup.py" '+action+' "$@"\n', newline='\n')
    for name in ('resident.mjs', 'presentation.mjs', 'full_record.mjs', 'resident_archive.mjs'):
        copy(ROOT/'software/pose180_pipeline/host'/name, release/'pc/software/pose180_pipeline/host'/name)
    copy(ROOT/'demo_v1/web/scene.js', release/'pc/demo_v1/web/scene.js')
    three = ROOT/'software/pc_viewer/node_modules/three'
    for name in ('build/three.module.js', 'build/three.core.js', 'examples/jsm/controls/OrbitControls.js', 'LICENSE'):
        copy(three/name, release/'pc/software/pc_viewer/node_modules/three'/name)
    (release/'start-pc.ps1').write_text('param([string]$Board="192.168.50.49")\n$ErrorActionPreference="Stop"\n& node (Join-Path $PSScriptRoot "pc/software/pose180_pipeline/host/resident.mjs") --board $Board --mode view --http-port 39380\nexit $LASTEXITCODE\n', newline='\n')
    count = source_snapshot(work, release/'core-sources.tar.gz')
    copy(RESIDENT/'STARTUP-PACKAGE.md', release/'README.md')
    for name in ('build.json', 'verification.json', 'no-threshold-test/result.json', 'startup-test/result.json'):
        copy(work/name, release/'validation'/name)
    manifest = dict(package=work.name, selection=identity['selection'], model=identity['model'],
                    input='live_csi/adaptive; original preprocessing', outputs=['HDMI', 'PC:39385'],
                    runtime_seconds_default=0, SDK_autostart=False, automatic_retry=False,
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
                  top_k=1, score_threshold=None, BOOT_sha256=identity['BOOT_sha256'], board_tested=False)
    write(work/'package.json', result)
    (output.with_suffix(output.suffix+'.sha256')).write_text(result['sha256']+'  '+output.name+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
