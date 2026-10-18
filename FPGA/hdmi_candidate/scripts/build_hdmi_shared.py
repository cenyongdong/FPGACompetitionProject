"""Export frozen shared Engine and add only an explicit device-owner hook."""
from pathlib import Path
import hashlib
import difflib
import json
import shutil
import subprocess
import sys
import time
import tarfile

R = Path(__file__).resolve().parents[3]
revision = sys.argv[1] if len(sys.argv) > 1 else 'r1'
assert revision.replace('-', '').isalnum()
monitor = revision == 'monitor-v2'
E = R / ('tools/pose-v1/evidence/' + ('hdmi-live-20261017-r2' if monitor else 'hdmi-display-20261017-r1') + '/build-shared-' + revision)
W = R / ('.local/' + ('hdmi-live-20261017-r1' if monitor else 'hdmi-display-20261017-r1') + '/source-shared-' + revision)
S = R / '.local/shared-resident-source-20261015-r1'
E.mkdir(exist_ok=False)
W.mkdir(exist_ok=False)
manifest = json.loads((S / 'source-manifest.json').read_text(encoding='utf-8'))
for relative, expected in manifest['files'].items():
    assert hashlib.sha256((S / relative).read_bytes()).hexdigest() == expected, relative
shutil.copytree(S / 'baseline', W / 'baseline')
for name in ['resident_support.hpp', 'shared_output_gate.hpp']:
    shutil.copyfile(S / name, W / name)
for name in ['main.cpp', 'CMakeLists.txt']:
    shutil.copyfile(R / 'software/hdmi_demo' / name, W / name)
if monitor:
    shutil.copyfile(R / 'FPGA/hdmi_candidate/software/ai_monitor_sdk.hpp', W / 'ai_monitor_sdk.hpp')
    p = W / 'main.cpp'
    text = p.read_text(encoding='utf-8')
    text = '#include "ai_monitor_sdk.hpp"\n' + text
    anchor = '        engine = std::make_unique<app::Engine>(config);'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '''        config.on_device_opened = [&](const icraft::xrt::Device& device) {
            pose::ai_monitor::validate(device);
        };
        config.on_apply_exception = [&](const icraft::xrt::Device& device, const std::exception& error) {
            // Preserve the actual SDK error before observing the same Device.
            std::ofstream log(output / "apply-failure-monitor.jsonl");
            log << "{\\"event\\":\\"original_apply_exception\\",\\"error\\":" << quote(error.what()) << "}\\n";
            log.flush();
            if (!log) throw std::runtime_error("Cannot save original apply exception");
            pose::ai_monitor::save(device, log);
        };
''' + anchor)
    p.write_text(text, encoding='utf-8')
for name in ['hdmi_output.hpp', 'hdmi_output.cpp', 'hdmi_format.hpp', 'hdmi_canvas.hpp', 'hdmi_canvas.cpp',
             'skeleton_render.hpp', 'skeleton_render.cpp']:
    shutil.copyfile(R / 'software/core/display' / name, W / name)

revisions = []
for name in ['application_core.hpp', 'application_core.cpp']:
    p = W / 'baseline' / name
    before = p.read_text(encoding='utf-8')
    if name.endswith('.hpp'):
        after = before.replace('#include <string>', '#include <string>\n#include <functional>\n#include <icraft-xrt/core/device.h>')
        anchor = '        size_t timing_frames = 0;'
        assert after.count(anchor) == 1
        after = after.replace(anchor, anchor + '\n        std::function<void(const icraft::xrt::Device&)> on_device_ready;')
        if monitor:
            after = after.replace('        std::function<void(const icraft::xrt::Device&)> on_device_ready;',
                '        std::function<void(const icraft::xrt::Device&)> on_device_ready;\n'
                '        std::function<void(const icraft::xrt::Device&)> on_device_opened;\n'
                '        std::function<void(const icraft::xrt::Device&, const std::exception&)> on_apply_exception;')
    else:
        anchor = '            validate_applied_bindings(session, graph, c.evidence);'
        assert before.count(anchor) == 1
        after = before.replace(anchor, anchor + '\n            if (c.on_device_ready) c.on_device_ready(device);')
        if monitor:
            opened = '            { fc::Span sample("init.open_device"); device = open_device(c.evidence); }'
            apply = '            { fc::Span sample("init.session_apply"); session.apply(); }'
            assert after.count(opened) == after.count(apply) == 1
            after = after.replace(opened, opened + '\n            if (c.on_device_opened) c.on_device_opened(device);')
            after = after.replace(apply, '''            try { fc::Span sample("init.session_apply"); session.apply(); }
            catch (const std::exception& original) {
                try { if (c.on_apply_exception) c.on_apply_exception(device, original); }
                catch (const std::exception& diagnostic) { std::cerr << "APPLY_MONITOR_DIAGNOSTIC_FAILED " << diagnostic.what() << std::endl; }
                catch (...) { std::cerr << "APPLY_MONITOR_DIAGNOSTIC_FAILED unknown exception" << std::endl; }
                throw; // Rethrow the original SDK exception unchanged.
            }''')
    assert after != before
    (E / (name + '.before')).write_text(before, encoding='utf-8')
    p.write_text(after, encoding='utf-8')
    revisions.append({'file': name, 'before_SHA256': hashlib.sha256((S / 'baseline' / name).read_bytes()).hexdigest(),
                      'after_SHA256': hashlib.sha256(p.read_bytes()).hexdigest(),
                      'diff': ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name, tofile=name))})
(E / 'engine-interface-revision.json').write_text(json.dumps(revisions, indent=2) + '\n')
shutil.copytree(W, E / 'source')

docker = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
remote = '/tmp/hdmi-display-20261017-shared-' + revision
steps = []


def run(label, args, budget=120):
    start = time.monotonic()
    p = subprocess.run([docker, *args], capture_output=True, timeout=budget)
    (E / (label + '.stdout.txt')).write_bytes(p.stdout)
    (E / (label + '.stderr.txt')).write_bytes(p.stderr)
    steps.append({'label': label, 'args': args, 'exit': p.returncode, 'seconds': time.monotonic() - start, 'budget': budget})
    (E / 'execution.json').write_text(json.dumps(steps, indent=2) + '\n')
    if p.returncode:
        raise RuntimeError(label + ' failed; preserve and stop')
    return p.stdout


assert run('01-state', ['inspect', '--format', '{{.State.Status}}', 'FPAI']).strip() == b'exited'
run('02-start', ['start', 'FPAI'])
try:
    expected = json.loads((R / 'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())['libraries']
    sdk = run('03-SDK', ['exec', 'FPAI', 'sha256sum', *['/usr/lib/aarch64-linux-gnu/' + n for n in expected]]).decode()
    assert {Path(line.split()[1]).name: line.split()[0] for line in sdk.splitlines()} == expected
    run('04-fresh', ['exec', 'FPAI', 'test', '!', '-e', remote])
    run('05-source', ['cp', str(W), 'FPAI:' + remote])
    run('06-configure', ['exec', 'FPAI', 'cmake', '-S', remote, '-B', remote + '/build', '-DCMAKE_SYSTEM_NAME=Linux',
                         '-DCMAKE_SYSTEM_PROCESSOR=aarch64', '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++',
                         '-DCMAKE_PREFIX_PATH=/usr/cmake', '-DCMAKE_BUILD_TYPE=Release'])
    run('07-build', ['exec', 'FPAI', 'cmake', '--build', remote + '/build', '--parallel', '2'])
    run('08-binary', ['cp', 'FPAI:' + remote + '/build/pose_hdmi_demo', str(E / 'pose_hdmi_demo')])
finally:
    run('09-stop', ['stop', 'FPAI'], 30)

package = E / 'package'
package.mkdir()
shutil.copyfile(E / 'pose_hdmi_demo', package / 'pose_hdmi_demo')
origin = R / '.local/shared-stability-delivery-20261015-r2'
shutil.copytree(origin / 'fixtures', package / 'fixtures')
(package / 'models').mkdir()
for name, expected in [('piw24_shared_ZG.json', 'a1395205eed11112ac0e23dacf8eec4c09d7dfec120e99b060a9361cb9c812cc'),
                       ('piw24_shared_ZG.raw', 'd235ec300f2872f1b78ce6101bc98fd2cc13c47a53fe99f76e045587148279dd')]:
    p = origin / 'models' / name
    assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
    shutil.copyfile(p, package / 'models' / name)
identities = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in package.rglob('*') if p.is_file()}
(E / 'package-files.json').write_text(json.dumps(identities, indent=2) + '\n')
with tarfile.open(E / 'package.tar', 'w') as tar:
    for p in package.rglob('*'):
        if p.is_file():
            tar.add(p, arcname=p.relative_to(package).as_posix())
print(json.dumps({'compiled': True, 'board_executed': False, 'files': len(identities),
                  'package_bytes': (E / 'package.tar').stat().st_size,
                  'engine_change': ('exported optional identity/apply-error/ready callbacks' if monitor
                                    else 'optional public device-owner hook only')}), flush=True)
