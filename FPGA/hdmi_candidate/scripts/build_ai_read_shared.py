"""Fresh, bounded export/build of three-window HDMI with passive read observation.

Run only when the root executor is ready to own the stopped FPAI container.
This script never opens a board, writes BOOT, runs a model or starts EDA.
"""
from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess
import tarfile
import time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r3/read-shared-build-r2'
W = R / '.local/hdmi-live-20261017-r3/read-shared-build-r2'
S = R / '.local/shared-resident-source-20261015-r1'
ORIGIN = R / '.local/shared-stability-delivery-20261015-r2'
OLD_PACKAGE = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/build-shared-monitor-v2/package-files.json'
FROZEN_MANIFEST_SHA = 'd2853ef64e76aba71d7ee175c7d85655bd3bab2352fc7c0264ea460c45656f3c'
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
REMOTE = '/tmp/hdmi-live-read-shared-20261017-r3-build-r2'
MODELS = {
    'piw24_shared_ZG.json': 'a1395205eed11112ac0e23dacf8eec4c09d7dfec120e99b060a9361cb9c812cc',
    'piw24_shared_ZG.raw': 'd235ec300f2872f1b78ce6101bc98fd2cc13c47a53fe99f76e045587148279dd',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(okay, message):
    if not okay:
        raise RuntimeError(message)


def save_json(name, value):
    (E / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def replace_once(text, old, new):
    need(text.count(old) == 1, 'Export anchor is absent or ambiguous: ' + old[:100])
    return text.replace(old, new, 1)


def export_sources():
    need(sha(S / 'source-manifest.json') == FROZEN_MANIFEST_SHA, 'Frozen manifest identity changed')
    manifest = json.loads((S / 'source-manifest.json').read_text(encoding='utf-8'))
    need(len(manifest['files']) == 138, 'Frozen source file count changed')
    normalized = {}
    for relative, expected in manifest['files'].items():
        key = relative.replace('\\', '/')
        need(not Path(key).is_absolute() and '..' not in Path(key).parts, 'Unsafe frozen source path')
        need(sha(S / key) == expected, 'Frozen source identity changed: ' + key)
        normalized[key] = expected
    package_expected = json.loads(OLD_PACKAGE.read_text())
    fixed_expected = {name: value for name, value in package_expected.items()
                      if name.startswith(('fixtures/', 'models/'))}
    need(len(fixed_expected) == 14, 'Frozen fixture/model manifest changed')
    for relative, expected in fixed_expected.items():
        need(sha(ORIGIN / relative) == expected, 'Fixed input/model identity changed: ' + relative)
    for name, expected in MODELS.items():
        need(fixed_expected['models/' + name] == expected, 'Explicit protected model identity changed')
    shutil.copytree(S / 'baseline', W / 'baseline')
    for name in ('resident_support.hpp', 'shared_output_gate.hpp'):
        shutil.copyfile(S / name, W / name)
    for name in ('main.cpp', 'CMakeLists.txt'):
        shutil.copyfile(R / 'software/hdmi_demo' / name, W / name)
    for name in ('ai_read_monitor_sdk.hpp', 'ai_monitor_sdk.hpp'):
        shutil.copyfile(R / 'FPGA/hdmi_candidate/software' / name, W / name)
    for name in ('hdmi_output.hpp', 'hdmi_output.cpp', 'hdmi_format.hpp', 'hdmi_canvas.hpp',
                 'hdmi_canvas.cpp', 'skeleton_render.hpp', 'skeleton_render.cpp'):
        shutil.copyfile(R / 'software/core/display' / name, W / name)

    changes = []
    for name in ('application_core.hpp', 'application_core.cpp'):
        path = W / 'baseline' / name
        before = path.read_text(encoding='utf-8')
        if name.endswith('.hpp'):
            after = replace_once(before, '#include <string>',
                '#include <string>\n#include <functional>\n#include <exception>\n#include <icraft-xrt/core/device.h>')
            anchor = '        size_t timing_frames = 0;'
            after = replace_once(after, anchor, anchor + '''
        std::function<void(const icraft::xrt::Device&)> on_device_ready;
        std::function<void(const icraft::xrt::Device&)> on_device_opened;
        std::function<void(const icraft::xrt::Device&, const std::exception&)> on_apply_exception;''')
        else:
            anchor = '            { fc::Span sample("init.open_device"); device = open_device(c.evidence); }'
            after = replace_once(before, anchor, anchor + '\n            if (c.on_device_opened) c.on_device_opened(device);')
            anchor = '            validate_applied_bindings(session, graph, c.evidence);'
            after = replace_once(after, anchor, anchor + '\n            if (c.on_device_ready) c.on_device_ready(device);')
            after = replace_once(after,
                '            { fc::Span sample("init.session_apply"); session.apply(); }', r'''            try { fc::Span sample("init.session_apply"); session.apply(); }
            catch (const std::exception& original) {
                // Preserve the complete original error before any diagnostic I/O.
                std::cerr << "ORIGINAL_SESSION_APPLY_EXCEPTION " << original.what() << std::endl;
                try { if (c.on_apply_exception) c.on_apply_exception(device, original); }
                catch (const std::exception& diagnostic) { std::cerr << "APPLY_MONITOR_DIAGNOSTIC_FAILED " << diagnostic.what() << std::endl; }
                catch (...) { std::cerr << "APPLY_MONITOR_DIAGNOSTIC_FAILED unknown exception" << std::endl; }
                throw;
            }''')
        (E / (name + '.before')).write_bytes((S / 'baseline' / name).read_bytes())
        path.write_text(after, encoding='utf-8')
        changes.append({'file': name, 'before_sha256': normalized['baseline/' + name],
                        'after_sha256': sha(path),
                        'diff': ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                                           fromfile=name, tofile=name))})
    save_json('engine-interface-revision.json', changes)

    path = W / 'main.cpp'
    before_main = path.read_text(encoding='utf-8')
    main = '#include "ai_read_monitor_sdk.hpp"\n#include "ai_monitor_sdk.hpp"\n' + before_main
    main = replace_once(main, '    std::unique_ptr<app::Engine> engine;', r'''    // The log outlives Capture. The Device belongs to Engine::Impl; Capture
    // borrows it only while Engine is alive. Capture destruction performs no SDK.
    std::ofstream read_monitor_log;
    std::unique_ptr<app::Engine> engine;''')
    main = replace_once(main, '    std::unique_ptr<pose::hdmi::Output> display;', r'''    std::unique_ptr<pose::hdmi::Output> display;
    std::unique_ptr<pose::ai_read_monitor::Capture> read_capture;
    const icraft::xrt::Device* read_monitor_device = nullptr;''')
    anchor = '        engine = std::make_unique<app::Engine>(config);'
    main = replace_once(main, anchor, r'''        read_monitor_log.open(output / "ai-read-monitor.jsonl");
        need(bool(read_monitor_log), "Cannot create read monitor log before Engine");
        config.on_device_opened = [&](const icraft::xrt::Device& device) {
            // Device is the stable Impl member, never a temporary or second Open.
            read_monitor_device = &device;
            // This executable is exclusively the stage after the successful
            // bounded DMA probe. Never infer an epoch from observed registers.
            read_capture = std::make_unique<pose::ai_read_monitor::Capture>(
                device, read_monitor_log, pose::ai_read_monitor::Epoch::AfterSuccessfulProbe);
            read_capture->arm(); // Strict seq2/2 -> ARM3/3, one 100ms attempt.
            pose::ai_monitor::validate(device); // Existing MIG monitor identity only.
        };
        config.on_apply_exception = [&](const icraft::xrt::Device& device, const std::exception& original) {
            // Engine already flushed the original what() to stderr. Save it to
            // the owning evidence stream before either same-Device observation.
            read_monitor_log << "{\"event\":\"original_apply_exception\",\"error\":" << quote(original.what()) << "}\n";
            read_monitor_log.flush();
            need(bool(read_monitor_log), "Cannot preserve original apply exception");
            try {
                need(bool(read_capture) && read_capture->can_freeze(), "Read capture not armed at apply failure");
                read_capture->freeze();
            } catch (const std::exception& diagnostic) {
                std::cerr << "APPLY_READ_MONITOR_DIAGNOSTIC_FAILED " << diagnostic.what() << std::endl;
                try { if (read_capture) read_capture->save_cached(); } catch (...) {}
            } catch (...) {
                std::cerr << "APPLY_READ_MONITOR_DIAGNOSTIC_FAILED unknown exception" << std::endl;
            }
            // An independent optional MIG snapshot follows, never replaces the
            // first error or repairs/retries an incomplete read-path capture.
            try { pose::ai_monitor::save(device, read_monitor_log); }
            catch (const std::exception& diagnostic) { std::cerr << "APPLY_MIG_MONITOR_DIAGNOSTIC_FAILED " << diagnostic.what() << std::endl; }
            catch (...) { std::cerr << "APPLY_MIG_MONITOR_DIAGNOSTIC_FAILED unknown exception" << std::endl; }
        };
''' + anchor)
    anchor = '        save_diagnostics(engine.get(), output);\n        engine.reset();'
    main = replace_once(main, anchor, r'''        save_diagnostics(engine.get(), output);
        // All three complete outputs were saved and gated; close()/STOP and
        // release already succeeded. Engine still owns this same live Device.
        need(completed == 3 && cases.size() == 3, "Three successful windows required before success snapshot");
        need(bool(engine) && bool(read_capture) && read_monitor_device != nullptr,
             "Live Engine-owned read capture absent at successful close");
        read_capture->freeze();
        need(read_capture->verified(), "Successful read snapshot not verified");
        pose::ai_monitor::save(*read_monitor_device, read_monitor_log);
        read_monitor_log.flush();
        need(bool(read_monitor_log), "Cannot save successful monitor evidence");
        read_capture.reset();
        read_monitor_device = nullptr;
        engine.reset();''')
    # No SDK operation in the main catch, including partially constructed Engine.
    anchor = '        engine.reset();\n        std::cerr << "HDMI_SHARED_STOP "'
    main = replace_once(main, anchor, '        read_capture.reset();\n        read_monitor_device = nullptr;\n' + anchor)
    main = replace_once(main, r'",\"VPU_started\":false,\"RTSP_started\":false,',
                        r'",\"ai_read_monitor_snapshot_verified\":true,\"VPU_started\":false,\"RTSP_started\":false,')
    path.write_text(main, encoding='utf-8')
    save_json('main-adapter-revision.json', {
        'formal_main_changed': False,
        'before_sha256': hashlib.sha256(before_main.encode()).hexdigest(), 'after_sha256': sha(path),
        'diff': ''.join(difflib.unified_diff(before_main.splitlines(True), main.splitlines(True),
                                           fromfile='main.cpp', tofile='exported/main.cpp'))})
    path = W / 'CMakeLists.txt'
    cmake = path.read_text(encoding='utf-8')
    cmake = replace_once(cmake, '-Wall -Wextra -Wpedantic -ffp-contract=off',
                         '-Wall -Wextra -Wpedantic -Werror -ffp-contract=off')
    cmake += '''
# Two pre-existing unused helpers; no frozen source change or global relaxation.
set_source_files_properties(main.cpp ${B}/host_cpu_adapter.cpp
  PROPERTIES COMPILE_OPTIONS "-Wno-unused-function")
'''
    path.write_text(cmake, encoding='utf-8')
    baseline = {key: value for key, value in normalized.items() if key.startswith('baseline/')}
    changed = sorted(key for key, value in baseline.items() if sha(W / key) != value)
    unchanged = len(baseline) - len(changed)
    need(changed == ['baseline/application_core.cpp', 'baseline/application_core.hpp'] and unchanged == 128,
         'Exported baseline revisions exceed the two optional Engine callbacks')
    for name in ('resident_support.hpp', 'shared_output_gate.hpp'):
        need(sha(W / name) == normalized[name], 'Frozen support header changed: ' + name)
    save_json('frozen-source-review.json', {
        'frozen_manifest_sha256': FROZEN_MANIFEST_SHA, 'frozen_files_checked': len(normalized),
        'exported_baseline_files_unchanged': unchanged, 'only_exported_baseline_revisions': changed,
        'formal_core_changed': False, 'formal_main_changed': False,
        'model_math_CPU_registration_NPU_allocation_frame_protocol_changed': False})
    save_json('scope.json', {
        'working_directory': str(R), 'source': str(W), 'evidence': str(E),
        'SDK': '3.39.0.0 EXACT', 'compiler_required': 'aarch64 GCC 9.4.0',
        'compiler_flags': ['-Wall', '-Wextra', '-Wpedantic', '-Werror', '-ffp-contract=off'],
        'precise_legacy_warning_exceptions': {
            'main.cpp': 'resident_support.hpp anonymous elapsed: -Wno-unused-function',
            'baseline/host_cpu_adapter.cpp': 'anonymous need: -Wno-unused-function'},
        'warnings_zero_exception_claimed': False,
        'on_device_opened': 'same stable Impl member; AfterSuccessfulProbe fixed seq2/2 -> ARM3/3 before Session creation/apply',
        'read_monitor_epoch': 'AfterSuccessfulProbe',
        'required_initial_sequence': 2, 'expected_ARM_sequence': 3, 'expected_FREEZE_sequence': 4,
        'read_monitor_epoch_automatically_selected_from_hardware': False,
        'apply_exception': 'original stderr+owned log first; same Device FREEZE104, then old MIG; rethrow original',
        'success_capture': 'all three saved/gated; safe HDMI close/STOP/release then FREEZE before live Engine destruction',
        'normal_path_intermediate_snapshot_or_synchronization_added': False,
        'main_failure_path_SDK_access_added': False, 'board_executed': False,
        'docker_jobs': 1, 'build_threads': 2, 'stage_budget_seconds': 90,
        'stop_conditions': 'identity/compiler/compile/ELF/package mismatch, nonzero child or timeout; no retry'})
    save_json('exported-source-files.json', {p.relative_to(W).as_posix(): sha(p) for p in W.rglob('*') if p.is_file()})
    shutil.copytree(W, E / 'source')


def build():
    steps = []

    def run(label, args, budget=90):
        started = time.monotonic()
        proc = subprocess.Popen([DOCKER, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeout = False
        try:
            out, err = proc.communicate(timeout=budget)
        except subprocess.TimeoutExpired:
            timeout = True
            proc.kill()  # This CLI only; owned container is stopped in finally.
            out, err = proc.communicate(timeout=15)
        (E / (label + '.stdout.txt')).write_bytes(out)
        (E / (label + '.stderr.txt')).write_bytes(err)
        steps.append({'label': label, 'args': args, 'exit': proc.returncode, 'timeout': timeout,
                      'seconds': time.monotonic() - started, 'budget': budget, 'pid': proc.pid})
        save_json('execution.json', steps)
        need(proc.returncode == 0 and not timeout, label + ' failed; preserve and stop')
        return out

    need(run('01-state', ['inspect', '--format', '{{.State.Status}}', 'FPAI']).strip() == b'exited',
         'FPAI not stopped; do not interrupt another owner')
    primary_failure = None
    try:
        run('02-start', ['start', 'FPAI'], 30)
        expected = json.loads((R / 'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())['libraries']
        actual = run('03-SDK', ['exec', 'FPAI', 'sha256sum', *['/usr/lib/aarch64-linux-gnu/' + n for n in expected]]).decode()
        need({Path(line.split()[1]).name: line.split()[0] for line in actual.splitlines()} == expected,
             'Six SDK library identities changed')
        version = run('04-compiler', ['exec', 'FPAI', 'aarch64-linux-gnu-g++', '-dumpfullversion', '-dumpversion']).decode().strip()
        need(version == '9.4.0', 'Cross compiler changed: ' + version)
        run('05-fresh', ['exec', 'FPAI', 'test', '!', '-e', REMOTE])
        run('06-source', ['cp', str(W), 'FPAI:' + REMOTE])
        run('07-configure', ['exec', 'FPAI', 'cmake', '-S', REMOTE, '-B', REMOTE + '/build',
                            '-DCMAKE_SYSTEM_NAME=Linux', '-DCMAKE_SYSTEM_PROCESSOR=aarch64',
                            '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++', '-DCMAKE_PREFIX_PATH=/usr/cmake',
                            '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'])
        run('08-build', ['exec', 'FPAI', 'cmake', '--build', REMOTE + '/build', '--parallel', '2'])
        run('09-commands', ['cp', 'FPAI:' + REMOTE + '/build/compile_commands.json', str(E / 'compile_commands.json')])
        commands = json.loads((E / 'compile_commands.json').read_text())
        legacy_seen = set()
        for command in commands:
            text = command['command']
            need(all(flag in text.split() for flag in ('-Wall', '-Wextra', '-Werror', '-ffp-contract=off')),
                 'Required compile flag missing')
            if '-Wno-unused-function' in text:
                name = Path(command['file']).name
                need(name in ('main.cpp', 'host_cpu_adapter.cpp'), 'Warning suppression broadened')
                legacy_seen.add(name)
        need(legacy_seen == {'main.cpp', 'host_cpu_adapter.cpp'}, 'Scoped legacy warning flags missing')
        run('10-binary', ['cp', 'FPAI:' + REMOTE + '/build/pose_hdmi_demo', str(E / 'pose_hdmi_demo')])
        elf = run('11-ELF', ['exec', 'FPAI', 'aarch64-linux-gnu-readelf', '-h', '-d', REMOTE + '/build/pose_hdmi_demo'])
        need(b'AArch64' in elf and b'libicraft_zg330backend.so' in elf and b'libicraft_hostbackend.so' in elf,
             'Built ELF identity/dependencies differ')
        save_json('build-review.json', {'compiled': True, 'board_executed': False,
                  'binary_sha256': sha(E / 'pose_hdmi_demo'), 'SDK': expected, 'compiler': version,
                  'precise_legacy_warning_exceptions_verified': sorted(legacy_seen)})
    except BaseException as error:
        primary_failure = error
        save_json('build-failure.json', {'error': str(error), 'retry': False})
        raise
    finally:
        try:
            run('12-stop', ['stop', 'FPAI'], 30)
        except BaseException as cleanup_error:
            save_json('cleanup-failure.json', {'error': str(cleanup_error), 'primary_error_preserved': primary_failure is not None})
            if primary_failure is None:
                raise


def package():
    for relative, expected_hash in json.loads((E / 'exported-source-files.json').read_text()).items():
        need(sha(W / relative) == expected_hash and sha(E / 'source' / relative) == expected_hash,
             'Exported source changed during build: ' + relative)
    package_dir = E / 'package'
    package_dir.mkdir()
    shutil.copyfile(E / 'pose_hdmi_demo', package_dir / 'pose_hdmi_demo')
    expected = json.loads(OLD_PACKAGE.read_text())
    fixed_files = {name: value for name, value in expected.items() if name.startswith(('fixtures/', 'models/'))}
    need(len(fixed_files) == 14 and sum(name.startswith('fixtures/') for name in fixed_files) == 12,
         'Expected fixed three-window package changed')
    for relative, expected_hash in fixed_files.items():
        source = ORIGIN / relative
        need(sha(source) == expected_hash, 'Fixed fixture/model identity changed: ' + relative)
        if relative.startswith('models/'):
            need(MODELS[Path(relative).name] == expected_hash, 'Model differs from protected explicit hash')
        target = package_dir / relative
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
        need(sha(target) == expected_hash, 'Package copy mismatch: ' + relative)
    identities = {p.relative_to(package_dir).as_posix(): sha(p) for p in package_dir.rglob('*') if p.is_file()}
    need(len(identities) == 15, 'Unexpected package members')
    save_json('package-files.json', identities)
    with tarfile.open(E / 'package.tar', 'w') as archive:
        for path in sorted(package_dir.rglob('*')):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(package_dir).as_posix())
    with tarfile.open(E / 'package.tar', 'r') as archive:
        readback = {member.name: hashlib.sha256(archive.extractfile(member).read()).hexdigest()
                    for member in archive.getmembers() if member.isfile()}
    need(readback == identities, 'Complete package archive readback differs')
    result = {'compiled': True, 'package_verified': True, 'board_executed': False,
              'files': len(identities), 'package_bytes': (E / 'package.tar').stat().st_size,
              'package_sha256': sha(E / 'package.tar'), 'binary_sha256': identities['pose_hdmi_demo'],
              'fixed_files_identical_to_monitor_v2_package': 14,
              'models': MODELS, 'baseline_files_unchanged': 128,
              'read_monitor_epoch': 'AfterSuccessfulProbe',
              'requires_successfully_completed_fixed_DMA_probe': True,
              'full_chain_board_passed': False}
    save_json('result.json', result)
    print(json.dumps(result), flush=True)


def main():
    E.mkdir(exist_ok=False)
    W.mkdir(exist_ok=False)
    shutil.copyfile(Path(__file__), E / 'actual-build-driver.py')
    export_sources()
    build()
    package()


if __name__ == '__main__':
    main()
