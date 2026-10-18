"""Offline v3 ICAP/BOOT/bundle stages. No deployment, board access or reboot.

Invoke one fresh mode at a time only after its recorded predecessor passes.
The package binds the r2 software pair with fixed diagnostic epochs; no older
candidate's files are accepted as an execution source.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
WORK = ROOT / '.local/hdmi-live-20261017-r3'
ORIGINAL = ROOT / 'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
ORIGINAL_BOOT_SHA = 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
ORIGINAL_BIT_SHA = '6818b7f8dea8e0f9dbda1b0d11127255ee1ba8876326bc7708a633641784f72e'
EPOCH_HELPER_SHA = 'da850ba04620d9cd12d978b44330ae8b0df362eb6783a150e66496075b73b60f'
MODELS = {
    'piw24_shared_ZG.json': 'a1395205eed11112ac0e23dacf8eec4c09d7dfec120e99b060a9361cb9c812cc',
    'piw24_shared_ZG.raw': 'd235ec300f2872f1b78ce6101bc98fd2cc13c47a53fe99f76e045587148279dd',
}
NAMES = {'icap': 'read-v3-icap', 'boot': 'read-v3-boot', 'bundle': 'controlled-startup-read-v3'}
PLANNER_GATE_SHA = '2e6b57a9351caffa648251e89799bcaf02d412d42d77a224a041789a12a0b65a'
DERIVED_NAMES = ('call_procise_disable_icap.bat', 'procise_run_disable_icap.tcl')
ISOLATION_POLICY = 'exact-two-absolute-open-write-targets-only'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def need(okay, message):
    if not okay:
        raise ValueError(message)


def checkpoint_helper(stage):
    """Load only the frozen public pure gate; never call manifest/EDA/CLI."""
    path = WORK / 'controlled_read_v3.py'
    stage.read(path, PLANNER_GATE_SHA)
    specification = importlib.util.spec_from_file_location('offline_package_checkpoint_gate', path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def factory_derived_gate(stage, sources, bit_identity):
    """Bind both redirected factory writes; no batch/script is ever executed."""
    directory = EVIDENCE / 'read-v3r5-bit'
    need('procise_run_disable_icap.tcl' in sources and 'call_procise_disable_icap.bat' not in sources,
         'Factory derived protected-source classification changed')
    descriptor = bit_identity.get('factory_derived_isolation', {})
    proof_path = directory / 'factory-derived-isolation.json'
    need(isinstance(descriptor, dict) and set(descriptor) == {'path', 'SHA256'}
         and Path(descriptor['path']).resolve() == proof_path.resolve(),
         'Factory derived-isolation identity/path missing')
    proof = json.loads(stage.read(proof_path, descriptor['SHA256']).decode('utf-8'))
    bit_input = stage.json(directory / 'bit-input-proof.json')
    plan = bit_input.get('factory_derived_isolation_plan', {})
    preservation = stage.json(directory / 'derived-output-preservation.json')
    need(plan.get('policy') == proof.get('policy') == ISOLATION_POLICY
         and plan.get('original_sources_unchanged_required') is True
         and plan.get('raw_batch_execution_forbidden') is True
         and proof.get('original_sources_unchanged') is True
         and proof.get('raw_batch_executed') is False,
         'Factory derived-isolation policy or original-source protection failed')
    plans, outputs = plan.get('outputs', {}), proof.get('outputs', {})
    need(set(plans) == set(outputs) == set(preservation) == set(DERIVED_NAMES),
         'Factory derived-isolation must cover exactly both fixed outputs')
    checked = {}
    for name in DERIVED_NAMES:
        original = WORK / 'reference' / name
        redirected = directory / 'factory-derived' / name
        before, after, retained = plans[name], outputs[name], preservation[name]
        protected = name in sources
        need(Path(before.get('original_path', '')).resolve() == original.resolve()
             and Path(after.get('original_path', '')).resolve() == original.resolve()
             and Path(before.get('redirected_path', '')).resolve() == redirected.resolve()
             and Path(after.get('redirected_path', '')).resolve() == redirected.resolve()
             and before.get('original_protected') is protected
             and after.get('original_protected') is protected
             and after.get('original_bytes_unchanged') is True
             and type(after.get('write_count')) is int and after['write_count'] == 1,
             'Factory derived target/protection/write-count differs: ' + name)
        existed = before.get('original_exists_before')
        need(type(existed) is bool and (not protected or existed),
             'Factory derived original existence/protected identity differs: ' + name)
        expected = before.get('original_before_SHA256')
        need(after.get('original_before_SHA256') == expected
             and after.get('original_after_SHA256') == expected
             and Path(retained.get('path', '')).resolve() == original.resolve()
             and retained.get('exists_before') is existed and retained.get('exists_after') is existed
             and retained.get('before_SHA256') == retained.get('after_SHA256') == expected
             and retained.get('original_bytes_unchanged') is True,
             'Factory derived original/archived before-after identity differs: ' + name)
        if existed:
            need(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected) is not None
                 and (not protected or expected == sources[name]),
                 'Factory derived original protected SHA differs: ' + name)
            raw = stage.read(original, expected)
            for label in ('before', 'after'):
                need(stage.read(directory / ('derived-' + label + '-' + name), expected) == raw,
                     'Factory derived original archive bytes differ: ' + name)
        else:
            need(expected is None and not os.path.lexists(str(original)),
                 'Originally absent derived source appeared: ' + name)
        count, digest = after.get('redirected_bytes'), after.get('redirected_SHA256')
        need(type(count) is int and 0 < count <= 4*1024*1024
             and isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) is not None
             and redirected.is_file() and not redirected.is_symlink(),
             'Factory redirected output size/SHA/file missing: ' + name)
        need(len(stage.read(redirected, digest)) == count, 'Factory redirected full bytes differ: ' + name)
        checked[name] = {'bytes': count, 'sha256': digest, 'original_protected': protected,
                         'original_bytes_unchanged': True, 'raw_execution': False}
    return {'policy': ISOLATION_POLICY, 'proof_sha256': descriptor['SHA256'],
            'outputs': checked, 'raw_batch_executed': False, 'original_sources_unchanged': True}


class Stage:
    def __init__(self, mode):
        self.mode, self.name = mode, NAMES[mode]
        self.out, self.work = EVIDENCE / self.name, WORK / self.name
        self.out.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.inputs = {}
        self.process_result = None
        self.parser = None
        self.bit_gate = None
        shutil.copyfile(__file__, self.out / 'actual-packager.py')

    def read(self, path, expected=None):
        path = path.resolve()
        data = path.read_bytes()
        actual = sha(data)
        need(expected is None or actual == expected, 'Input identity mismatch: ' + str(path))
        prior = self.inputs.get(str(path))
        row = {'bytes': len(data), 'sha256': actual}
        need(prior is None or prior == row, 'Input changed within stage: ' + str(path))
        self.inputs[str(path)] = row
        return data

    def json(self, path, expected=None):
        return json.loads(self.read(path, expected).decode('utf-8-sig'))

    def save(self, name, data):
        with (self.out / name).open('xb') as stream:
            stream.write(data)

    def check_inputs(self):
        for path, record in self.inputs.items():
            data = Path(path).read_bytes()
            need(len(data) == record['bytes'] and sha(data) == record['sha256'],
                 'Immutable input changed during execution: ' + path)
        need(time.monotonic() - self.started < 240,
             'Offline stage controller exceeded 180s tool plus bounded cleanup allowance')

    def load_parser(self):
        parser_path = ROOT / 'tools/pose-v1/inspect_selected_boot.py'
        self.read(parser_path, '1f91a799f387c1c3de29d9fa890d0dd1d39c1678566b8e6f9919907ba9a4ed16')
        specification = importlib.util.spec_from_file_location('read_package_bit_parser', parser_path)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)  # Its CLI main is __name__ guarded.
        self.parser = module.bit_payload

    def gate(self):
        review = self.json(EVIDENCE / 'read-v3r5-reports/review.json')
        need(review.get('bit_generation_prerequisite_pass') is True,
             'read-v3 routed report gate does not permit bit generation')
        need(review.get('candidate_run') == 'route_read_v3r5' and review.get('managed_run') is False,
             'Final gate is not bound to actual checkpoint-only continuation')
        constraints = self.json(EVIDENCE / 'read-v3r3-constraints-r3/review.json')
        helper = checkpoint_helper(self)
        evidence = {}
        lineage = helper.verify_checkpoint_lineage(constraints, review, evidence)
        for relative, expected in evidence.items():
            path = helper.INSTALLED_LEDGER if relative == 'checkpoint/installed-ledger' else EVIDENCE / relative
            self.read(path, expected)
        for relative, expected in constraints['source_sha256'].items():
            self.read(WORK / 'reference' / relative, expected)
        installed = self.json(helper.INSTALLED_LEDGER)
        for relative, expected in installed['actual'].items():
            self.read(helper.TOOLCHAIN / relative, expected)
        self.read(EVIDENCE / 'checkpoints-before-route-r4/ai7030_edif_top_physopt.dcp', helper.PHYSOPT_SHA)
        self.read(EVIDENCE / 'checkpoints-before-route-r4/ai7030_edif_top.tcl', helper.ORIGINAL_NATIVE_SHA)
        routed, bit = lineage['routed_checkpoint'], lineage['bit_identity']
        self.read(Path(routed['path']), routed['SHA256'])
        self.read(Path(bit['path']), bit['SHA256'])
        isolation = factory_derived_gate(self, constraints['source_sha256'], bit)
        self.bit_gate = {'candidate_run': 'route_read_v3r5', 'managed_run': False,
                         'planner_gate_sha256': PLANNER_GATE_SHA,
                         'bit_identity_sha256': sha(self.read(EVIDENCE / 'read-v3r5-bit/bit-identity.json')),
                         'routed_checkpoint_sha256': routed['SHA256'], 'raw_bit_sha256': bit['SHA256'],
                         'factory_derived_isolation': isolation}

    def baseline(self):
        rollback = self.json(ORIGINAL / 'rollback-identity.json',
                             '3dd515f89bb9357453886f7619921d903cd99ea3514755c3656d44611f593ad9')
        control = self.json(ORIGINAL / 'boot-control-utf8-r2/inputs.json',
                            '9dfb57c54a81d8bb8c84e96f6f1c3d55f1fb76436fa20fd48084039567a31552')
        need(rollback['BOOT_sha256'] == ORIGINAL_BOOT_SHA
             and rollback['rollback_bit_sha256'] == ORIGINAL_BIT_SHA
             and rollback['board_BOOT_match'] is True
             and rollback['BOOT_PL_offset_bytes'] == 186816
             and rollback['BOOT_PL_bytes'] == 5980464, 'Original rollback contract changed')
        source = Path(rollback['source_directory'])
        boot = self.read(source / 'BOOT.bin', ORIGINAL_BOOT_SHA)
        bit = self.read(ORIGINAL / 'rollback/ai7030_top_disable_icap.bit', ORIGINAL_BIT_SHA)
        payload, _ = self.parser(bit)
        offset, length = rollback['BOOT_PL_offset_bytes'], rollback['BOOT_PL_bytes']
        partition = boot[offset:offset + length]
        need(len(boot) == 7023552 and len(partition) == length and length % 4 == 0,
             'Original BOOT/PL bounds changed')
        decoded = b''.join(partition[i:i + 4][::-1] for i in range(0, len(partition), 4))
        need(decoded[:len(payload)] == payload and len(decoded) - len(payload) == 4,
             'Original BOOT PL no longer matches original patched bit/padding contract')
        for name in ['FSBL251210_ddr400_demo.out', 'bl31.elf', 'u-boot']:
            data = self.read(source / name, control[name]['sha256'])
            need(len(data) == control[name]['bytes'], 'Original PS component length changed: ' + name)
        return source, rollback, control, boot

    def procise(self, code):
        self.work.mkdir(parents=True, exist_ok=False)
        code = code.replace('@@WORK@@', self.work.as_posix())
        self.save('stage.tcl', code.encode('ascii'))
        (self.work / 'stage.tcl').write_text(code, encoding='ascii')
        tool = Path('C:/FudanMicro/Procise')
        executable = tool / 'bin/procise.exe'
        self.read(executable)
        environment = os.environ.copy()
        environment.update(APP_DIR=str(tool), ICTIME_HOME=str(tool), FMSH_DB=str(tool / 'db'),
                           TCL_LIBRARY=str(tool / 'tcl8.4'))
        environment['PATH'] = str(tool / 'dll') + os.pathsep + environment.get('PATH', '')
        started, timed_out = time.monotonic(), False
        with (self.out / 'stdout.txt').open('xb') as stdout, (self.out / 'stderr.txt').open('xb') as stderr:
            process = subprocess.Popen([str(executable), 'stage.tcl'], cwd=self.work,
                                       env=environment, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            dump(self.out / 'owned-process.json', {'pid': process.pid, 'work': str(self.work),
                                                  'argv': [str(executable), 'stage.tcl'], 'budget_seconds': 180})
            try:
                process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    if os.name == 'nt':
                        kill = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                              capture_output=True, timeout=20)
                        (self.out / 'cleanup.txt').write_bytes(kill.stdout + kill.stderr)
                    else:
                        process.kill()
                    process.wait(timeout=20)
                except Exception as error:
                    dump(self.out / 'cleanup-failure.json', {'error': str(error), 'exit': process.poll()})
        self.process_result = {'exit': process.poll(), 'seconds': time.monotonic() - started,
                               'budget_seconds': 180, 'timeout': timed_out, 'board_operation': False}
        dump(self.out / 'execution.json', self.process_result)
        need(not timed_out and process.poll() == 0, 'Procise failed/timed out; preserve and stop')


def icap(stage):
    source, _, _, _ = stage.baseline()
    # Only this exact v3 run is a candidate source. No prior candidate fallback.
    raw_path = WORK / 'reference/fpai_demo_vivado.runs/route_read_v3r5/ai7030_edif_top.bit'
    raw = stage.read(raw_path)
    _, raw_header = stage.parser(raw)
    stage.save('ai-read-v3.bit', raw)
    code = '''if {[catch {
 set_device JFMQL30TAI676H
 increment_bit_cfg_v3 {INPUT} {@@WORK@@/ai-read-v3_disable_icap.bit} -disable_icap
 puts "AI_READ_V3_ICAP_COMPLETE_OFFLINE"
} result]} {puts "AI_READ_V3_ICAP_FAILED $result";exit 1}
exit
'''.replace('INPUT', raw_path.as_posix())
    stage.procise(code)
    patched = (stage.work / 'ai-read-v3_disable_icap.bit').read_bytes()
    stage.save('ai-read-v3_disable_icap.bit', patched)
    payload, header = stage.parser(patched)
    need('Patched=DISABLE_ICAP' in header['a'], 'Patched bit does not declare disabled ICAP')
    original_bit = stage.read(ORIGINAL / 'rollback/ai7030_top_disable_icap.bit', ORIGINAL_BIT_SHA)
    original_payload, original_header = stage.parser(original_bit)
    need(raw_header['b'] == original_header['b'] == header['b']
         and len(payload) == len(original_payload) and len(payload) % 4 == 0,
         'Candidate target device/payload size changed from the qualified original part')
    need(payload != original_payload, 'Candidate payload unexpectedly equals original')
    need(sha(stage.read(raw_path)) == sha(raw), 'Procise modified source bit')
    stage.check_inputs()
    dump(stage.out / 'review.json', {'Procise_execution': stage.process_result,
         'raw_sha256': sha(raw), 'raw_bytes': len(raw), 'patched_sha256': sha(patched),
         'patched_bytes': len(patched), 'payload_sha256': sha(payload), 'payload_bytes': len(payload),
         'payload_differs_from_original': True, 'header': header,
         'candidate_run': 'route_read_v3r5', 'managed_run': False, 'baseline_source_directory': str(source),
         'r5_bit_gate': stage.bit_gate,
         'deployed': False, 'rebooted': False})


def boot(stage):
    source, rollback, control, original = stage.baseline()
    patch = stage.json(EVIDENCE / 'read-v3-icap/review.json')
    predecessor = stage.json(EVIDENCE / 'read-v3-icap/controller-result.json')
    need(predecessor['success'] is True and predecessor['mode'] == 'icap',
         'ICAP controller did not finish all input/review checks')
    need(patch['candidate_run'] == 'route_read_v3r5' and patch['managed_run'] is False and patch['Procise_execution']['exit'] == 0
         and not patch['Procise_execution']['timeout'], 'ICAP predecessor did not pass')
    candidate_path = EVIDENCE / 'read-v3-icap/ai-read-v3_disable_icap.bit'
    bit = stage.read(candidate_path, patch['patched_sha256'])
    payload, _ = stage.parser(bit)
    need(sha(payload) == patch['payload_sha256'] and len(payload) == patch['payload_bytes'],
         'ICAP payload identity changed')
    inputs = WORK / 'read-v3-boot-inputs'
    inputs.mkdir(parents=True, exist_ok=False)
    identities = {}
    for name in ['FSBL251210_ddr400_demo.out', 'bl31.elf', 'u-boot']:
        data = stage.read(source / name, control[name]['sha256'])
        (inputs / name).write_bytes(data)
        identities[name] = {'bytes': len(data), 'sha256': sha(data), 'source': str(source / name)}
    (inputs / 'ai-read-v3_disable_icap.bit').write_bytes(bit)
    bif = '''//arch = fmql; split = false; format = BIN
the_ROM_image:
{
 [bootloader, destination_device = ps]@/FSBL251210_ddr400_demo.out
 [destination_device = pl]@/ai-read-v3_disable_icap.bit
 [destination_cpu = apu_0, destination_device = ps]@/bl31.elf
 [destination_cpu = apu_0, destination_device = ps]@/u-boot
 [fsbl_config]apu_x32
}
'''.replace('@', inputs.as_posix())
    (inputs / 'candidate.bif').write_text(bif, encoding='ascii')
    stage.save('candidate.bif', bif.encode('ascii'))
    dump(stage.out / 'inputs.json', identities)
    code = ('if {[catch {\n create_boot_image {' + (inputs / 'candidate.bif').as_posix()
            + '} {@@WORK@@/BOOT-ai-read-v3.bin} -fmql\n puts "AI_READ_V3_BOOT_OFFLINE_COMPLETE"\n'
            + '} result]} {puts "AI_READ_V3_BOOT_FAILED $result";exit 1}\nexit\n')
    stage.procise(code)
    new = (stage.work / 'BOOT-ai-read-v3.bin').read_bytes()
    stage.save('BOOT-ai-read-v3.bin', new)
    offset, length = rollback['BOOT_PL_offset_bytes'], rollback['BOOT_PL_bytes']
    end = offset + length
    swapped = b''.join(new[i:i + 4][::-1] for i in range(offset, end, 4))
    review = {'bytes': len(new), 'sha256': sha(new), 'original_sha256': sha(original),
              'PL_offset': offset, 'PL_bytes': length,
              'all_bytes_outside_PL_identical': len(new) == len(original)
                  and new[:offset] == original[:offset] and new[end:] == original[end:],
              'PL_matches_candidate_after_word_swap': swapped[:len(payload)] == payload,
              'padding_identical': new[offset + len(payload):end] == original[offset + len(payload):end],
              'differing_PL_bytes': sum(a != b for a, b in zip(original[offset:end], new[offset:end])),
              'candidate_bit_sha256': sha(bit), 'candidate_payload_sha256': sha(payload),
              'candidate_run': 'route_read_v3r5', 'managed_run': False, 'deployed': False, 'rebooted': False}
    dump(stage.out / 'review.json', review)
    need(review['all_bytes_outside_PL_identical'] and review['PL_matches_candidate_after_word_swap']
         and review['padding_identical'] and review['differing_PL_bytes'] > 0,
         'BOOT/non-PL/padding/word-swap gate failed')
    stage.check_inputs()


def bundle(stage):
    source, rollback, _, original = stage.baseline()
    review = stage.json(EVIDENCE / 'read-v3-boot/review.json')
    predecessor = stage.json(EVIDENCE / 'read-v3-boot/controller-result.json')
    need(predecessor['success'] is True and predecessor['mode'] == 'boot',
         'BOOT controller did not finish all input/review checks')
    need(all(review.get(key) is True for key in ('all_bytes_outside_PL_identical',
         'PL_matches_candidate_after_word_swap', 'padding_identical'))
         and review['differing_PL_bytes'] > 0 and review['candidate_run'] == 'route_read_v3r5'
         and review['managed_run'] is False,
         'BOOT review does not permit an offline bundle')
    expected_path = ROOT / 'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json'
    sdk = stage.json(expected_path, '19b3a995678023c34244e02ca8c92e400e07520442debc73ee786743a49f2f10')['libraries']
    probe_root = EVIDENCE / 'build-read-probe-r2'
    probe = stage.json(probe_root / 'result.json')
    need(probe.get('compiled') is True and probe.get('complete') is True
         and probe['container_confirmed_stopped'] is True and probe['SDK'] == sdk,
         'Actual r2 probe build/SDK/cleanup not qualified')
    shared_root = EVIDENCE / 'read-shared-build-r2'
    shared = stage.json(shared_root / 'result.json')
    build = stage.json(shared_root / 'build-review.json')
    need(shared.get('compiled') is True and shared.get('package_verified') is True
         and shared['files'] == 15 and shared['models'] == MODELS
         and shared['baseline_files_unchanged'] == 128 and build['SDK'] == sdk,
         'Actual r2 shared package/SDK/model/frozen-source contract failed')
    for root in (probe_root, shared_root):
        stage.read(root / 'source/ai_read_monitor_sdk.hpp', EPOCH_HELPER_SHA)
        stage.read(root / 'source/ai_monitor_sdk.hpp',
                   '77b3ef8341ad791518e64861daafbb74df330ac399bd00f6f3c1ffec3c8c4f53')
    stage.read(probe_root / 'source/ai_read_dma_probe.cpp',
               '59d04e24051d06ba5f9a0899b577d73c9d4e7eb054a6530142cf546fa4e4e67b')
    need(b'Epoch::AfterSuccessfulProbe' in stage.read(shared_root / 'source/main.cpp'),
         'Shared r2 source does not explicitly select the post-probe epoch')
    archive = stage.read(shared_root / 'package.tar', shared['package_sha256'])
    need(len(archive) == shared['package_bytes'] and len(archive) <= 50 * 1024 * 1024,
         'Shared archive size changed or exceeded existing bounded package')
    files = stage.json(shared_root / 'package-files.json')
    need(len(files) == 15 and all(files['models/' + key] == value for key, value in MODELS.items()),
         'Shared package file/model manifest changed')
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        for member in tar.getmembers():
            path = PurePosixPath(member.name)
            need(member.isfile() and member.name not in seen and not path.is_absolute()
                 and '..' not in path.parts and member.name in files,
                 'Unsafe, duplicate, or unexpected shared tar member')
            seen.add(member.name)
            stream = tar.extractfile(member)
            need(stream is not None and sha(stream.read()) == files[member.name],
                 'Shared archive member identity mismatch: ' + member.name)
    need(seen == set(files) and files['pose_hdmi_demo'] == shared['binary_sha256'],
         'Shared archive membership/binary mismatch')
    items = [
        (EVIDENCE / 'read-v3-boot/BOOT-ai-read-v3.bin', 'BOOT-ai-read-v3.bin', review['sha256']),
        (source / 'BOOT.bin', 'BOOT-original.bin', ORIGINAL_BOOT_SHA),
        (EVIDENCE / 'read-v3-icap/ai-read-v3_disable_icap.bit', 'ai-read-v3_disable_icap.bit', review['candidate_bit_sha256']),
        (probe_root / 'ai_read_dma_probe', 'ai_read_dma_probe', probe['binary_sha256']),
        (shared_root / 'package.tar', 'shared-package.tar', shared['package_sha256']),
    ]
    patch = stage.json(EVIDENCE / 'read-v3-icap/review.json')
    # Recompute the BOOT comparison at the final bundle boundary as well.
    new_boot = stage.read(EVIDENCE / 'read-v3-boot/BOOT-ai-read-v3.bin', review['sha256'])
    candidate_bit = stage.read(EVIDENCE / 'read-v3-icap/ai-read-v3_disable_icap.bit', review['candidate_bit_sha256'])
    payload, _ = stage.parser(candidate_bit)
    offset, length = rollback['BOOT_PL_offset_bytes'], rollback['BOOT_PL_bytes']
    end = offset + length
    swapped = b''.join(new_boot[i:i + 4][::-1] for i in range(offset, end, 4))
    need(len(new_boot) == len(original) and new_boot[:offset] == original[:offset]
         and new_boot[end:] == original[end:] and swapped[:len(payload)] == payload
         and new_boot[offset + len(payload):end] == original[offset + len(payload):end],
         'Final bundle independent non-PL/word-swap/padding comparison failed')
    items.append((EVIDENCE / 'read-v3-icap/ai-read-v3.bit', 'ai-read-v3.bit', patch['raw_sha256']))
    manifest = {}
    for path, name, expected in items:
        data = stage.read(path, expected)
        stage.save(name, data)
        need(sha((stage.out / name).read_bytes()) == expected, 'Bundle copy readback mismatch: ' + name)
        manifest[name] = {'source': str(path), 'bytes': len(data), 'sha256': expected}
    for name, data in [('shared-package-files.json', files), ('probe-build-result.json', probe),
                       ('shared-build-result.json', shared), ('shared-build-review.json', build),
                       ('SDK-model-identities.json', {'SDK': sdk, 'models': MODELS,
                        'helper_sha256': EPOCH_HELPER_SHA, 'probe_epoch': [0, 1, 2],
                        'shared_epoch_after_successful_probe': [2, 3, 4]})]:
        dump(stage.out / name, data)
        blob = (stage.out / name).read_bytes()
        manifest[name] = {'bytes': len(blob), 'sha256': sha(blob), 'source': 'verified metadata above'}
    stage.check_inputs()
    dump(stage.out / 'manifest.json', {'files': manifest,
         'scope': 'offline candidate package only; original BOOT unchanged',
         'deployed': False, 'rebooted': False, 'board_executed': False,
         'deployment_or_reboot_authorization': False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=tuple(NAMES))
    args = parser.parse_args()
    stage = Stage(args.mode)
    success = False
    try:
        stage.load_parser()
        stage.gate()
        {'icap': icap, 'boot': boot, 'bundle': bundle}[args.mode](stage)
        success = True
        print('Offline ' + args.mode + ' complete; no deployment/board/reboot', flush=True)
        return 0
    except Exception as error:
        dump(stage.out / 'failure.json', {'error': str(error), 'traceback': traceback.format_exc(),
                                         'process_result': stage.process_result})
        print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        dump(stage.out / 'input-identities.json', stage.inputs)
        dump(stage.out / 'controller-result.json', {'mode': args.mode, 'success': success,
             'time': datetime.now(timezone(timedelta(hours=8))).isoformat(),
             'seconds': time.monotonic() - stage.started, 'cwd': str(Path.cwd()),
             'working_directory': str(stage.work), 'process': stage.process_result,
             'r5_bit_gate': stage.bit_gate,
             'deployed': False, 'rebooted': False, 'board_executed': False})
        artifacts = [{'path': path.relative_to(stage.out).as_posix(), 'bytes': path.stat().st_size,
                      'sha256': sha(path.read_bytes())} for path in sorted(stage.out.rglob('*'))
                     if path.is_file() and path.name != 'artifacts.json']
        dump(stage.out / 'artifacts.json', {'files': artifacts})


if __name__ == '__main__':
    raise SystemExit(main())
