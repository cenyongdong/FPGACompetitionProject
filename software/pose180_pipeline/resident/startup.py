"""Manual release launcher. One SDK owner; reuse the bounded, graceful supervisor.

No startup hook, BOOT write, reboot, router login or automatic SDK retry.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from service import atomic, live, process_identity, supervise
from run_hdmi_trial import owners
from boot_audit import fat_files
import startup_network


def read(path):
    return json.loads(path.read_text())


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            value.update(block)
    return value.hexdigest()


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def verify_files(root, identity):
    for name, expected in identity['files'].items():
        if sha(root/name) != expected:
            raise ValueError('Release file changed: '+name)
    if not os.access(root/'pose180_demo', os.X_OK):
        raise ValueError('Native executable permission missing')


def verify_boot(identity):
    if Path('/sys/class/fpga_manager/fpga0/state').read_text().strip() != 'operating':
        raise ValueError('FPGA is not operating')
    actual = {entry['name']: entry['sha256'] for entry in fat_files()}
    for name, expected in identity['boot_files'].items():
        if actual.get(name) != expected:
            raise ValueError('Qualified startup file differs: '+name)
    return actual['BOOT.BIN']


def authorize_boot(root, identity):
    current = boot_id()
    verify_boot(identity)
    if current in identity['verified_boot_ids']:
        return current
    receipt = root/'next-boot.json'
    prepared = read(receipt) if receipt.exists() else {}
    if (prepared.get('BOOT_sha256') != identity['BOOT_sha256'] or
            not prepared.get('previous_boot_id') or prepared['previous_boot_id'] == current):
        raise ValueError('Unknown running BOOT. Run prepare-boot, then explicitly reboot before starting')
    # Read-only before/after startup-file identity plus a changed Linux boot ID.
    # The native functional ABI/idle/drain checks remain the final device gate.
    return current


def previous_run(root):
    latest = root/'latest.json'
    if not latest.exists():
        return None
    name = read(latest)['run']
    if Path(name).name != name:
        raise ValueError('Invalid run directory')
    return root/'runs'/name


def check_previous(root, current_boot):
    previous = previous_run(root)
    if previous is None:
        return
    process = previous/'supervisor.json'
    if process.exists() and live(read(process)):
        raise ValueError('Release supervisor already running')
    attempted = previous/'sdk-attempt.json'
    if not attempted.exists():
        return
    outcome = read(previous/'outcome.json') if (previous/'outcome.json').exists() else {}
    safe = (outcome.get('native_exit') == 0 and outcome.get('native_shutdown_complete') is True
            and outcome.get('device_owners') == [])
    if not safe and read(attempted).get('boot_id') == current_boot:
        raise ValueError('Previous SDK attempt lacks a safe completion; no same-boot retry')


def preflight(root, identity):
    if os.geteuid() != 0:
        raise ValueError('Board root is required')
    verify_files(root, identity)
    current = authorize_boot(root, identity)
    packages = subprocess.check_output(['dpkg-query', '-W', '-f=${Package} ${Architecture} ${Version}\n',
                                        'icraft:arm64', 'customop:arm64'], universal_newlines=True).splitlines()
    if sorted(packages) != ['customop arm64 3.39.0', 'icraft arm64 3.39.0']:
        raise ValueError('Requires the existing ARM64 Icraft/customop 3.39.0 SDK')
    for name, expected in identity['libraries'].items():
        if sha(Path('/usr/lib/aarch64-linux-gnu')/name) != expected:
            raise ValueError('SDK library identity differs: '+name)
    if owners():
        raise ValueError('Device already owned')
    check_previous(root, current)
    return current


def command(root, run, session, seconds):
    return [str(root/'pose180_demo'), '--package', str(root), '--output', str(run/'run'),
            '--bind', '0.0.0.0', '--session', str(session), '--seconds', str(seconds),
            '--top-k', '1', '--score-threshold', 'none',
            '--hardware-profile', 'probe-free-drain-filter-v1', '--filter-backend', 'cpu',
            '--min-cutoff', '0.5', '--beta', '0.3', '--d-cutoff', '1',
            '--hdmi', '1', '--csi', str(root/'csi.conf'), '--input-port', '0',
            '--result-port', '39383', '--status-port', '39384', '--view-port', '39385']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'serve', 'status', 'stop', 'check', 'prepare-boot'))
    parser.add_argument('--seconds', type=int, default=0, help='0: run until a manual stop; no automatic restart')
    parser.add_argument('--run', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.seconds < 0:
        parser.error('Runtime must be nonnegative')
    root = Path(__file__).resolve().parent
    identity = read(root/'identity.json')
    previous = previous_run(root)
    if args.action in ('status', 'stop'):
        if previous is None:
            print(json.dumps(dict(running=False, started=False)))
            return
        supervisor = read(previous/'supervisor.json') if (previous/'supervisor.json').exists() else None
        running = live(supervisor)
        if args.action == 'stop':
            (previous/'stop.request').touch(exist_ok=True)
            print(json.dumps(dict(stop_requested=running, forced_SDK_kill=False, run=str(previous))))
        else:
            state = read(previous/'service-status.json') if (previous/'service-status.json').exists() else {}
            state.update(supervisor_alive=running, run=str(previous))
            if (previous/'error.json').exists():
                state['error'] = read(previous/'error.json')
            print(json.dumps(state))
        return
    if args.action == 'prepare-boot':
        verify_files(root, identity)
        if owners():
            raise ValueError('Stop all device owners before boot preparation')
        actual = verify_boot(identity)
        atomic(root/'next-boot.json', dict(previous_boot_id=boot_id(), BOOT_sha256=actual))
        print(json.dumps(dict(prepared=True, reboot_performed=False, next_step='Explicit operator reboot, then start')))
        return
    if args.action == 'check':
        current = preflight(root, identity)
        print(json.dumps(dict(ready=True, boot_id=current, SDK_started=False, top_k=1, score_threshold=None)))
        return
    if args.action == 'start':
        with (root/'start.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            current = preflight(root, identity)
            name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+str(time.time_ns())
            run = root/'runs'/name
            (run/'metadata').mkdir(parents=True)
            atomic(run/'request.json', dict(boot_id=current, seconds=args.seconds))
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'serve', '--run', name],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, start_new_session=True)
            supervisor = process_identity(child.pid)
            atomic(run/'supervisor.json', supervisor)
            atomic(root/'latest.json', dict(run=name))
            print(json.dumps(dict(started=True, supervisor=supervisor, run=str(run), automatic_retry=False)))
        return
    if not args.run or Path(args.run).name != args.run:
        raise ValueError('Internal supervisor needs a valid run directory')
    run = root/'runs'/args.run
    network = None
    try:
        # Same global ownership lock as the finite validated service.
        with Path('/run/pose180-resident.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            request = read(run/'request.json')
            if request['boot_id'] != boot_id() or owners():
                raise ValueError('Boot or device ownership changed before launch')
            if (run/'stop.request').exists():
                return
            network = startup_network.add()
            atomic(run/'network.json', network)
            with (run/'sdk-attempt.json').open('x') as stream:
                json.dump(dict(boot_id=boot_id(), automatic_retry=False), stream)
            session = time.time_ns() // 1000
            seconds = request['seconds']
            outcome = supervise(run, command(root, run, session, seconds), seconds+120 if seconds else float('inf'))
            if outcome.get('native_shutdown_complete') and not outcome.get('device_owners'):
                startup_network.remove(network)
                atomic(run/'network-closed.json', dict(removed_owned_alias=network['added']))
    except Exception as error:
        atomic(run/'error.json', dict(error=str(error), automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
