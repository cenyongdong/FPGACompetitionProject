"""Compile isolated HDMI utilities against the exact existing ARM SDK."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[3]
revision = sys.argv[1]
assert revision.replace('-', '').isalnum()
saved = revision.startswith('saved-')
target = 'hdmi_saved_skeleton' if saved else 'hdmi_frame_probe'
E = R / 'tools/pose-v1/evidence/hdmi-display-20261017-r1' / ('build-' + revision)
W = R / '.local/hdmi-display-20261017-r1' / ('source-' + revision)
E.mkdir(exist_ok=False)
W.mkdir(exist_ok=False)
for rel, name in [
    ('FPGA/hdmi_candidate/software/' + ('CMakeLists-saved.txt' if saved else 'CMakeLists-frame.txt'), 'CMakeLists.txt'),
    ('FPGA/hdmi_candidate/software/frame_probe.cpp', 'frame_probe.cpp'),
    ('software/core/display/hdmi_output.hpp', 'hdmi_output.hpp'),
    ('software/core/display/hdmi_format.hpp', 'hdmi_format.hpp'),
    ('software/core/display/hdmi_output.cpp', 'hdmi_output.cpp'),
]:
    shutil.copyfile(R / rel, W / name)
if saved:
    shutil.copyfile(R / 'FPGA/hdmi_candidate/software/saved_skeleton.cpp', W / 'saved_skeleton.cpp')
    for name in ['hdmi_canvas.cpp', 'hdmi_canvas.hpp', 'skeleton_render.cpp', 'skeleton_render.hpp']:
        shutil.copyfile(R / 'software/core/display' / name, W / name)
shutil.copytree(W, E / 'source')
remote = '/tmp/hdmi-display-20261017-r1-' + revision
docker = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
steps = []


def run(label, args, budget=90):
    start = time.monotonic()
    p = subprocess.run([docker, *args], capture_output=True, timeout=budget)
    (E / (label + '.stdout.txt')).write_bytes(p.stdout)
    (E / (label + '.stderr.txt')).write_bytes(p.stderr)
    steps.append({'label': label, 'args': args, 'exit': p.returncode,
                  'seconds': time.monotonic() - start, 'budget': budget})
    (E / 'execution.json').write_text(json.dumps(steps, indent=2) + '\n')
    if p.returncode:
        raise RuntimeError(label + ' failed; preserve and stop')
    return p.stdout


state = run('01-state', ['inspect', '--format', '{{.State.Status}}', 'FPAI']).strip()
assert state == b'exited', 'Existing container owner; do not interrupt'
run('02-start', ['start', 'FPAI'])
try:
    expected = json.loads((R / 'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())['libraries']
    output = run('03-SDK', ['exec', 'FPAI', 'sha256sum',
                            *['/usr/lib/aarch64-linux-gnu/' + n for n in expected]]).decode()
    got = {Path(line.split()[1]).name: line.split()[0] for line in output.splitlines()}
    assert got == expected, 'ARM SDK identity changed'
    run('04-fresh', ['exec', 'FPAI', 'test', '!', '-e', remote])
    run('05-copy', ['cp', str(W), 'FPAI:' + remote])
    run('06-configure', ['exec', 'FPAI', 'cmake', '-S', remote, '-B', remote + '/build',
                         '-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
                         '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++',
                         '-DCMAKE_PREFIX_PATH=/usr/cmake', '-DCMAKE_BUILD_TYPE=Release'])
    run('07-build', ['exec', 'FPAI', 'cmake', '--build', remote + '/build', '--parallel', '2'])
    run('08-copy-binary', ['cp', 'FPAI:' + remote + '/build/' + target, str(E / target)])
    elf = run('09-ELF', ['exec', 'FPAI', 'aarch64-linux-gnu-readelf', '-h', '-d', remote + '/build/' + target])
    assert b'AArch64' in elf and b'libicraft_zg330backend.so' in elf
    (E / 'result.json').write_text(json.dumps({'compiled': True, 'board_executed': False,
        'binary_sha256': hashlib.sha256((E / target).read_bytes()).hexdigest(),
        'SDK_libraries': got}, indent=2) + '\n')
    print('ARM HDMI frame utility built; board validation pending', flush=True)
finally:
    run('10-stop', ['stop', 'FPAI'], 30)
