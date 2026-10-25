"""Prepare this new package once; no network, SDK, EDA, BOOT or reboot IO."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BOARD = OUT/'board'
REMOTE = '/root/demo-v1-20261022-r1/pose180-hdmi-20261025-r2'
ID = 'pose180-hdmi-20261025-r2'
CAPS = dict(candidate_starts=1, SDK_Open=1, original_fallbacks=1,
            frames=52800, input_hz=30, hard_seconds=2100)


def identity(path):
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def copy(source, destination):
    if destination.exists():
        raise ValueError('Preserve previous asset: '+str(destination))
    shutil.copyfile(source, destination)


def main():
    old = ROOT/'tools/pose-v1/evidence/hdmi-pipeline-20261024-r53/deploy'
    cfg = json.loads((old/'config.json').read_text())
    support = ROOT/'tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/deploy/board_support.py'
    copy(support, BOARD/'board_support.py')
    source = ROOT/'FPGA/hdmi_candidate/diagnostics/native_rgb565_r53'
    copy(source/'bootstrap.py', BOARD/'bootstrap.py')
    diagnostic = ROOT/'tools/pose-v1/evidence/hp2-mmio32-20261024-r46/deploy/package'
    continuation = ROOT/'.local/hp2-mmio32-20261024-r46/continuation/package'
    for name in ('before_seed_gate.py','capture_hp2_cycletrace.py','capture_hp2_protocol.py',
                 'decode_hp2_cycletrace.py','decode_hp2_protocol.py','hp2_protocol_checks.py'):
        copy(diagnostic/name, BOARD/'package'/name)
    for name in ('capture_deferred.py','consume_gate.py'):
        copy(continuation/name, BOARD/'package'/name)
    copy(ROOT/'.local/hp2-mmio32-20261024-r46/package/libmmio32.so', BOARD/'package/libmmio32.so')
    copy(ROOT/'.local/hp2-deferred-consume-20261024-r45/boot-package/BOOT-hp2-deferred-consume-r45.bin',
         BOARD/'package/BOOT-candidate.bin')
    copy(ROOT/'tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/BOOT-original.readback.bin',
         BOARD/'package/BOOT-original.bin')
    copy(ROOT/'.local/pose180-pipeline-20261025-r1/software-package.tar.gz', BOARD/'software-package.tar.gz')
    # Reuse the established transport, UART identity checks and marker handshake.
    transport = (ROOT/'software/pose180_pipeline/tools/board.py').read_text()
    transport = transport.replace('ROOT=Path(__file__).resolve().parents[3]',
                                  'ROOT=Path(__file__).resolve().parents[2]')
    transport = transport.replace("out=ROOT/'.local/pose180-pipeline-20261025-r1'",
                                  'out=Path(__file__).resolve().parent')
    transport = transport.replace('module.getpass.getpass=authorized_password',
                                  'module.getpass.getpass=authorized_password\n    module.ROOT=out')
    (OUT/'board_call.py').write_text(transport)
    for name in ('start_candidate.py','start_fallback.py'):
        text = (source/name).read_text()
        text = text.replace("E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-pipeline-20261024-r53')",
                            'E=Path(__file__).resolve().parent')
        text = text.replace("BASE='/root/hdmi-pipeline-20261024-r53'", 'BASE='+repr(REMOTE))
        text = text.replace('HP2_R53_', 'POSE180_HDMI_R2_')
        text = text.replace('/ps_release_board.py', '/controller.py').replace(" --cycle '+str(cycle)", "'")
        (OUT/name).write_text(text)
    text = (source/'capture_uart.py').read_text()
    start = text.index('R=Path(')
    end = text.index('\ntag=sys.argv[1]', start)
    text = text[:start]+'E=Path(__file__).resolve().parent\n'+text[end:]
    text = text.replace("('resume','candidate-1','candidate-2','fallback')", "('candidate-1','fallback')")
    text = text.replace("(R/'FPGA/hdmi_candidate/scripts/capture_hdmi_startup.ps1')",
                        "Path(__file__).with_name('capture_hdmi_startup.ps1')")
    (OUT/'capture_uart.py').write_text(text)
    copy(ROOT/'FPGA/hdmi_candidate/scripts/capture_hdmi_startup.ps1', OUT/'capture_hdmi_startup.ps1')
    files = {path.relative_to(BOARD).as_posix(): identity(path)
             for path in sorted(BOARD.rglob('*')) if path.is_file()}
    for name, expected in (('package/BOOT-candidate.bin', cfg['files']['BOOT-candidate.bin']),
                           ('package/BOOT-original.bin', cfg['files']['BOOT-original.bin']),
                           ('board_support.py', cfg['support_identity']),
                           ('bootstrap.py', cfg['controller_files']['bootstrap.py'])):
        if files[name] != expected:
            raise ValueError('Qualified protected asset differs: '+name)
    for name in ('capture_deferred.py','consume_gate.py','before_seed_gate.py','capture_hp2_cycletrace.py',
                 'capture_hp2_protocol.py','decode_hp2_cycletrace.py','decode_hp2_protocol.py',
                 'hp2_protocol_checks.py','libmmio32.so'):
        if files['package/'+name] != cfg['files'][name]:
            raise ValueError('Existing diagnostic identity differs: '+name)
    if files['software-package.tar.gz']['sha256'] != '74222dde5bec673fe1953b0de273769c3ff10ccb781b4d6ee3b461afca345f97':
        raise ValueError('Previously built software archive changed')
    checked = []
    for path in sorted(OUT.rglob('*.py')):
        compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec')
        checked.append(path.relative_to(OUT).as_posix())
    manifest = dict(package_id=ID, base=REMOTE, caps=CAPS, files=files,
        original_boot_sha256=cfg['original_boot_sha256'], board=cfg['board'], known_FAT=cfg['known_FAT'],
        status='offline_prepared_pending_explicit_boot_authorization', hardware_rebuilt=False,
        source_commit='870aae27', numerical_accuracy_accepted=False, CSI_live=False,
        old_DATA='paused', D45_root_cause_investigation='paused', automatic_retry=False,
        qualification_reference=cfg['hardware_qualification'],
        boot_metadata='boot-control/metadata', software_metadata='pipeline/metadata',
        startup_admission_original='startup-admission.json',
        startup_mode_original='software/startup-mode.txt',
        startup_receipt_copies=['pipeline/startup-admission.json','pipeline/startup-mode.txt'],
        precondition='Fix and verify observed Host raw archive callback stall before joint SDK load; preserve complete first outputs and the existing one-second age limit',
        prior_run_fact='Original-BOOT run stopped at frame7840 after Host raw archive callback 1019.789ms; NPU frame output finite/identity/selection passed; do not classify as NPU tail',
        local_validation=dict(python_syntax_passed=True, python_files=checked, SDK=0, BOOT_writes=0, reboots=0))
    manifest['board']['remote_root'] = REMOTE
    manifest['board'].pop('pre_start_boot_id', None)
    (BOARD/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    authorization = dict(package_id=ID, active=False, caps=CAPS, user_confirmation=None,
        note='Preparation only. Activate solely after the actual user approves this specific package.')
    (BOARD/'authorization.json').write_text(json.dumps(authorization, indent=2)+'\n')
    archive = OUT/'board-package.tar.gz'
    with tarfile.open(archive, 'x:gz') as target:
        for path in sorted(BOARD.rglob('*')):
            if path.is_file():
                target.add(path, arcname=path.relative_to(BOARD).as_posix())
    print(json.dumps(dict(prepared=True, package_id=ID, archive=str(archive), **identity(archive),
        python_syntax_files=len(checked), SDK=0, BOOT_writes=0, reboots=0, authorization_active=False)))


if __name__ == '__main__':
    main()
