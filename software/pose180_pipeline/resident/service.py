"""One detached board supervisor; stop requests never kill/retry an SDK call."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from bounded_log import RingLog
from run_hdmi_trial import preflight, owners


def atomic(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False))
    os.replace(temporary, path)


def process_identity(pid):
    try:
        fields = Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, start_ticks=fields[19],
                    boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    except (OSError, IndexError):
        return None


def live(identity):
    return bool(identity) and process_identity(identity['pid']) == identity


def read_status(port):
    try:
        with socket.create_connection(('127.0.0.1', port), .2) as connection:
            data = b''
            while b'\n' not in data and len(data) < 8192:
                chunk = connection.recv(8192 - len(data))
                if not chunk:
                    break
                data += chunk
        return json.loads(data)
    except (OSError, ValueError):
        return None


def supervise(root, command, budget, status_port=39384):
    """Also exercised with an explicit mock binary; no hidden process retries."""
    metadata = root / 'metadata'
    samples = RingLog(metadata, 'resources', 262144, 2)
    read_fd, write_fd = os.pipe()
    # If the disk or logger stalls, only stdout/stderr bytes are lost. SDK
    # execution and the original resource ownership contract stay independent.
    os.set_blocking(write_fd, False)
    pump = subprocess.Popen([sys.executable, str(Path(__file__).with_name('bounded_log.py')),
                             str(read_fd), str(metadata)], pass_fds=(read_fd,),
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    os.close(read_fd)
    atomic(metadata / 'logger-process.json', process_identity(pump.pid))
    started = time.monotonic()
    child = None
    reason = None
    sent = False
    final = {}
    count = 0
    peak_rss = peak_fds = peak_threads = 0
    minimum_available = None
    stopping = [False]
    previous = {sig: signal.signal(sig, lambda *_: stopping.__setitem__(0, True))
                for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                 stdout=write_fd, stderr=write_fd)
        os.close(write_fd)
        write_fd = -1
        native_identity = process_identity(child.pid)
        atomic(metadata / 'process.json', dict(identity=native_identity, argv=command))
        while child.poll() is None:
            now = time.monotonic()
            state = read_status(status_port)
            if state:
                final = state
            mem = Path('/proc/meminfo').read_text()
            available = next(int(line.split()[1]) for line in mem.splitlines() if line.startswith('MemAvailable:'))
            minimum_available = available if minimum_available is None else min(minimum_available, available)
            try:
                status = Path('/proc/%d/status' % child.pid).read_text()
                fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
                rss = int(fields.get('VmRSS', '0').split()[0])
                threads = int(fields.get('Threads', '0').split()[0])
                fds = len(list(Path('/proc/%d/fd' % child.pid).iterdir()))
            except (OSError, ValueError):
                rss = threads = fds = 0
            peak_rss, peak_fds, peak_threads = max(peak_rss, rss), max(peak_fds, fds), max(peak_threads, threads)
            if available < 131072:
                reason = reason or 'MemAvailable below 128 MiB'
            if state and state.get('state') == 'isolated':
                reason = reason or 'Native isolated; no SDK restart'
            if stopping[0] or (root / 'stop.request').exists():
                reason = reason or 'Explicit local stop request'
            if now - started > budget:
                reason = reason or 'Finite stop-request budget reached; observing original SDK'
            if reason and not sent:
                child.send_signal(signal.SIGTERM)
                sent = True
            row = dict(elapsed=now-started, status=final, RSS_KiB=rss, fds=fds, threads=threads,
                       MemAvailable_KiB=available, stop_reason=reason, stop_sent=sent)
            samples.write((json.dumps(row) + '\n').encode())
            try:
                atomic(root / 'service-status.json', dict(supervisor=process_identity(os.getpid()),
                       native=native_identity, running=True, **row))
            except OSError:
                pass  # A diagnostic write failure must not terminate the SDK.
            count += 1
            time.sleep(.5)
        native_exit = child.wait()
        completion = root / 'run/completion.json'
        complete = json.loads(completion.read_text()) if completion.exists() else {}
        final = complete.get('status', final)
        outcome = dict(native_exit=native_exit, seconds=time.monotonic()-started,
                       stop_reason=reason, stop_sent=sent, final_status=final,
                       native_shutdown_complete=complete.get('native_shutdown_complete', False),
                       device_owners=owners(), SDK_attempts=1, automatic_retry=False,
                       samples=count, peak_RSS_KiB=peak_rss, peak_fds=peak_fds,
                       peak_threads=peak_threads, minimum_MemAvailable_KiB=minimum_available)
        atomic(root / 'outcome.json', outcome)
        atomic(root / 'service-status.json', dict(running=False, **outcome))
        return outcome
    finally:
        if write_fd >= 0:
            os.close(write_fd)
        # No exceptional monitor path may abandon or kill an active SDK.
        if child is not None and child.poll() is None:
            child.send_signal(signal.SIGTERM)
            while child.poll() is None:
                time.sleep(1)
        samples.close()
        try:
            pump.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pump.terminate()
            try:
                pump.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pump.kill()  # Logger created before SDK; owns no device handles.
                pump.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def authorize(root):
    auth = json.loads((root.parent / 'authorization.json').read_text())
    manifest = json.loads((root.parent / 'manifest.json').read_text())
    if (not auth.get('active') or not auth.get('user_confirmation') or
        auth['package_id'] != manifest['package_id'] or auth['caps'] != manifest['caps'] or
        (root.parent / 'boot-control/metadata/closed.json').exists()):
        raise ValueError('This new package lacks active authorization or is closed')
    return auth['caps']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('start', 'serve', 'status', 'stop'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.action == 'status':
        status = json.loads((root / 'service-status.json').read_text()) if (root / 'service-status.json').exists() else {}
        if (root / 'service-error.json').exists():
            status['supervisor_error'] = json.loads((root / 'service-error.json').read_text())
        if not status and (root / 'service-process.json').exists():
            status = json.loads((root / 'service-process.json').read_text())
            status['supervisor_alive'] = live(status.get('supervisor'))
        if status.get('running'):
            status['supervisor_alive'] = live(status.get('supervisor'))
            status['native_alive'] = live(status.get('native'))
        print(json.dumps(status))
        return
    if args.action == 'stop':
        (root / 'stop.request').touch(exist_ok=True)
        print(json.dumps(dict(stop_requested=True, forced_SDK_kill=False)))
        return
    caps = authorize(root)
    if args.action == 'start':
        # An exclusive marker prevents two starts even while preflight is running.
        with (root / 'service-start.attempt.json').open('x') as file:
            json.dump(dict(caps=caps, automatic_retry=False), file)
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'serve'],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
        result = dict(supervisor=process_identity(child.pid), detached=True)
        atomic(root / 'service-process.json', result)
        print(json.dumps(result))
        return
    with Path('/run/pose180-resident.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            identity, boot, metadata = preflight(root)
            with (root / 'sdk-attempt.json').open('x') as file:
                json.dump(dict(boot_id=boot, SDK_attempts=1, caps=caps), file)
            (metadata / 'before.dmesg').write_bytes(subprocess.check_output(['dmesg']))
            command = [str(root/'pose180_demo'), '--package', str(root), '--output', str(root/'run'),
                       '--bind', '0.0.0.0', '--session', str(identity['session']),
                       '--seconds', str(caps['runtime_seconds']), '--hdmi', '1', '--csi', str(root/'csi.conf')]
            supervise(root, command, caps['stop_request_seconds'])
            (metadata / 'after.dmesg').write_bytes(subprocess.check_output(['dmesg']))
        except Exception as error:
            atomic(root / 'service-error.json', dict(error=str(error), automatic_retry=False))
            raise


if __name__ == '__main__':
    main()
