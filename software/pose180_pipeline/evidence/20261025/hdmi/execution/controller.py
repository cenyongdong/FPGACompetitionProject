"""New bounded pose180 HDMI package; reuse qualified r53 BOOT/FAT primitives.

Preparation is not approval. No stage retries a failed SDK or device command.
BOOT metadata and the unchanged software guard's metadata are separate.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

BASE = Path(__file__).resolve().parent
CONTROL = BASE/'boot-control'
META = CONTROL/'metadata'
PACKAGE = BASE/'package'
PIPELINE = BASE/'pipeline'
ID = 'pose180-hdmi-20261025-r2'
CAPS = dict(candidate_starts=1, SDK_Open=1, original_fallbacks=1,
            frames=52800, input_hz=30, hard_seconds=2100)
cfg = b = c = None


def read(path):
    return json.loads(path.read_text())


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def save(path, value):
    b.save_new(path, value)
    return value


def initialize():
    global cfg, b, c
    cfg = read(BASE/'manifest.json')
    need(cfg['package_id'] == ID and cfg['base'] == str(BASE) and cfg['caps'] == CAPS,
         'Wrong new package or finite budget')
    spec = importlib.util.spec_from_file_location('_pose180_boot_support', BASE/'board_support.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    b.CFG, b.ROOT, b.META, b.PACKAGE, b.MOUNT = cfg, CONTROL, META, PACKAGE, CONTROL/'boot-mount'
    b.identity_record = lambda value: dict(value, package_id=ID)
    sys.path.insert(0, str(PACKAGE))
    import capture_deferred
    c = capture_deferred


def authorize():
    auth = read(BASE/'authorization.json')
    need(auth.get('active') is True and auth.get('package_id') == ID and auth.get('caps') == CAPS
         and isinstance(auth.get('user_confirmation'), str) and auth['user_confirmation'].strip(),
         'Explicit user approval for this new package is required')
    need(not (META/'closed.json').exists(), 'New package is closed')


def owners():
    return b.owners() + c.owners()


def reserve(stage, **extra):
    return save(META/(stage+'.attempt.json'), dict(boot_id=b.boot_id(),
                automatic_retry=False, package_id=ID, **extra))


def stopped():
    return (META/'stopped.json').exists()


def restored():
    row = read(META/'restore.json')
    identity = b.boot_id()
    need(row['passed'] and row['boot_id'] == identity
         and row['BOOT_sha256'] == cfg['original_boot_sha256']
         and row['other_startup_files_unchanged'] and row['boot_partition_unmounted']
         and not owners(), 'Original BOOT file, same candidate runtime, or owners differ')
    return identity


def prepare():
    # Verify transfer once. Later stages retain native BOOT readback and SDK gates.
    for name, row in cfg['files'].items():
        b.verify_file(BASE/name, row)
    CONTROL.mkdir(mode=0o700)
    META.mkdir(mode=0o700)
    (CONTROL/'boot-mount').mkdir(mode=0o700)
    audit = b.audit(cfg['original_boot_sha256'])
    need(not owners(), 'Other device work is active')
    PIPELINE.mkdir(mode=0o700)
    with tarfile.open(BASE/'software-package.tar.gz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            need(member.isfile() and not path.is_absolute() and '..' not in path.parts,
                 'Unsafe software archive member')
        archive.extractall(PIPELINE)
    # bootstrap retains its original paths and writes software/startup-mode.txt.
    (BASE/'software').mkdir(mode=0o700)
    save(META/'prepare.json', dict(passed=True, boot_id=b.boot_id(), audit=audit,
        package_id=ID, BOOT_writes=0, reboots=0, SDK=0, approval_added=False))
    return dict(passed=True, boot_id=b.boot_id(), BOOT_writes=0, reboots=0, SDK=0)


def reboot(stage, expected):
    b.audit(expected)
    need(not owners(), 'Device ownership differs before bounded reboot')
    reserve(stage)
    child = subprocess.Popen(['/bin/sh', '-c', 'sleep 2; exec /sbin/reboot'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)
    return save(META/(stage+'-issued.json'), dict(command_issued=True,
                helper_pid=child.pid, boot_id=b.boot_id(), package_id=ID))


def startup():
    identity = restored()
    reserve('startup', SDK=0)
    from bootstrap import bootstrap
    receipt = bootstrap(BASE, identity)
    need(receipt['passed'] and receipt['boot_id'] == identity
         and receipt['observer_generation'] == 4, 'Fresh startup admission differs')
    # The original evidence remains at BASE. Copy its exact bytes, not a new receipt.
    for source, target in ((BASE/'startup-admission.json', PIPELINE/'startup-admission.json'),
                           (BASE/'software/startup-mode.txt', PIPELINE/'startup-mode.txt')):
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
    need((PIPELINE/'startup-mode.txt').read_text().strip() == receipt['mode'], 'Mode copy differs')
    return save(META/'startup.json', receipt)


def run(session):
    need(isinstance(session, int) and session > 0, 'Positive actual host session is required')
    identity = restored()
    admission = read(BASE/'startup-admission.json')
    need(admission['passed'] and admission['boot_id'] == identity
         and admission['observer_generation'] == 4, 'Same-boot startup admission absent')
    b.audit(cfg['original_boot_sha256'], identity)
    reserve('long-test', SDK_Open=1, **{key: CAPS[key] for key in ('frames','input_hz','hard_seconds')})
    argv = [sys.executable, str(PIPELINE/'run_board.py'), '--session', str(session),
            '--frames', '52800', '--hdmi', '1', '--hard-seconds', '2100']
    start = time.monotonic()
    save(META/'long-command.json', dict(argv=argv, boot_id=identity, automatic_retry=False))
    with (META/'long.stdout.log').open('xb') as stdout, (META/'long.stderr.log').open('xb') as stderr:
        # No outer timeout kills or duplicates the native guard's bounded load.
        child = subprocess.Popen(argv, stdout=stdout, stderr=stderr, start_new_session=True)
        save(META/'long-process.json', dict(pid=child.pid,
             start_ticks=Path('/proc/%d/stat'%child.pid).read_text().split()[21],
             boot_id=identity, argv=argv))
        while child.poll() is None:
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(json.dumps(dict(stage='long-test', pid=child.pid,
                    elapsed_seconds=time.monotonic()-start)), flush=True)
    outcome = read(PIPELINE/'outcome.json') if (PIPELINE/'outcome.json').exists() else {}
    summary = read(PIPELINE/'run/summary.json') if (PIPELINE/'run/summary.json').exists() else {}
    events = [json.loads(line) for line in (PIPELINE/'run/hdmi.jsonl').read_text().splitlines()] \
             if (PIPELINE/'run/hdmi.jsonl').exists() else []
    passed = child.returncode == 0 and outcome.get('native_exit') == 0 and not outcome.get('stop_reason') \
             and b.boot_id() == identity and not owners() \
             and all(summary.get(key) == 52800 for key in
                     ('completed','received','host_archived','inferred','HDMI_adopted')) \
             and summary.get('engine_destroyed') is True \
             and sum(row.get('event') == 'stop_proved' for row in events) == 1 \
             and sum(row.get('event') == 'frames_released_after_stop' for row in events) == 1
    return save(META/'long-test.json', dict(passed=bool(passed), native_exit=child.returncode,
        seconds=time.monotonic()-start, boot_id=identity, startup_mode=admission['mode'],
        summary=summary, outcome=outcome, CSI_live=False, SDK_Open_attempts=1,
        physical_screen_verified=False, strict30Hz_requires_host_evidence=True,
        numerical_accuracy_accepted=False, automatic_retry=False))


def main(args):
    initialize()
    original = cfg['original_boot_sha256']
    candidate = cfg['files']['package/BOOT-candidate.bin']['sha256']
    stage = args.stage
    if stage == 'audit':
        return b.audit(original)
    if stage == 'prepare':
        return prepare()
    authorize()
    if stage in ('install','candidate-reboot','startup','run'):
        need(not stopped(), 'Affected package stopped; do not retry')
    if stage == 'install':
        prepared = read(META/'prepare.json')
        b.audit(original, prepared['boot_id'])
        need(not owners(), 'Other device work is active')
        b.verify_file(PACKAGE/'BOOT-original.bin', cfg['files']['package/BOOT-original.bin'])
        return b.replace_boot(PACKAGE/'BOOT-candidate.bin', original, candidate, 'install', 'install.json')
    if stage == 'candidate-reboot':
        installed = read(META/'install.json')
        need(installed['passed'] and installed['boot_id'] == b.boot_id(), 'Install or runtime absent')
        return reboot(stage, candidate)
    if stage == 'restore':
        previous = read(META/'candidate-reboot.attempt.json')['boot_id']
        need(previous != b.boot_id() and read(META/'candidate-reboot-issued.json')['command_issued'],
             'Single candidate startup not established')
        b.audit(candidate)
        need(not owners(), 'Other device work is active')
        return b.replace_boot(PACKAGE/'BOOT-original.bin', candidate, original, 'restore', 'restore.json')
    if stage == 'startup':
        return startup()
    if stage == 'run':
        return run(args.session)
    if stage == 'fallback-reboot':
        restored()
        return reboot(stage, original)
    if stage == 'close':
        previous = read(META/'fallback-reboot.attempt.json')['boot_id']
        identity = b.boot_id()
        need(previous != identity and read(META/'fallback-reboot-issued.json')['command_issued'],
             'Single original fallback startup not established')
        audit = b.audit(original, identity)
        need(not owners(), 'Owner remains after original fallback')
        save(META/'final-audit.json', audit)
        return save(META/'closed.json', dict(closed=True, boot_id=identity,
            candidate_starts=1, original_fallbacks=1,
            SDK_Open_attempts=int((META/'long-test.attempt.json').exists()),
            remaining=dict(candidate_starts=0, SDK_Open=0, original_fallbacks=0)))
    raise ValueError('Unknown stage')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('audit','prepare','install','candidate-reboot',
        'restore','startup','run','fallback-reboot','close'))
    parser.add_argument('--session', type=int)
    args = parser.parse_args()
    try:
        result = main(args)
        keys = ('passed','boot_id','mode','BOOT_sha256','closed','command_issued','native_exit','seconds')
        print(json.dumps({key: result[key] for key in keys if key in result}), flush=True)
        if result.get('passed') is False:
            raise RuntimeError('Native stage did not pass; original evidence preserved')
    except Exception as error:
        if b is not None and META.is_dir() and args.stage not in ('audit','restore','fallback-reboot','close') \
           and not stopped():
            save(META/'stopped.json', dict(stage=args.stage, error=str(error),
                 boot_id=b.boot_id(), automatic_retry=False))
        print(json.dumps(dict(error=str(error), automatic_retry=False)), file=sys.stderr)
        raise
