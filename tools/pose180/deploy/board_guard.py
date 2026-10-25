"""One verification session, then one authorized 1800-second saturation run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def owners():
    result = []
    for fd in Path('/proc').glob('[0-9]*/fd/*'):
        try:
            target = os.readlink(str(fd))
            if target.startswith(('/dev/axi', '/dev/udmabuf', '/dev/u-dma', '/dev/video')):
                result.append([str(fd), target])
        except OSError:
            pass
    return result


def snapshot(folder, name):
    (folder/(name+'.dmesg')).write_bytes(subprocess.check_output(['dmesg']))
    (folder/(name+'.meminfo')).write_bytes(Path('/proc/meminfo').read_bytes())
    (folder/(name+'.boot-id')).write_bytes(Path('/proc/sys/kernel/random/boot_id').read_bytes())


def stop(child):
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=('verify', 'stress'), required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    run = root/('run-'+args.stage)
    run.mkdir()
    package = load(root/'identity.json')
    child = None
    native = None
    failure = None
    try:
        direct_stress = args.stage=='stress' and (root/'stress-policy.json').exists() and load(root/'stress-policy.json')['user_approved_ignore_numeric_error']
        if not direct_stress and (not load(root/'prior-first-review.json')['approved_gate_passed'] or not load(root/'numerical-policy.json')['user_confirmed']):
            raise ValueError('First saved values or new model policy not approved')
        if args.stage == 'stress' and not direct_stress:
            if (root/'run-verify/exit.txt').read_text().strip() != '0' or not load(root/'run-verify/results/summary.json')['passed']:
                raise ValueError('New-model numerical verification did not pass')
        for name, digest in package['files'].items():
            if sha(root/name) != digest:
                raise ValueError('Delivery identity differs: '+name)
        subprocess.run([sys.executable, str(root/'preflight.py'), str(run/'preflight.json')], check=True)
        before = load(run/'preflight.json')
        if sorted(before['boot_files'], key=lambda x:x['name']) != sorted(package['expected_boot_files'], key=lambda x:x['name']):
            raise ValueError('BOOT identity differs; no device initialization')
        if before['fpga_state'] != 'operating' or before['SDK_packages'] != ['customop arm64 3.39.0','icraft arm64 3.39.0']:
            raise ValueError('Device or SDK package identity differs')
        for name, digest in package['libraries'].items():
            if sha(Path('/usr/lib/aarch64-linux-gnu')/name) != digest:
                raise ValueError('SDK library identity differs: '+name)
        if owners():
            raise ValueError('Existing device owner; preserve other work')
        free = os.statvfs(str(root))
        if free.f_bavail*free.f_frsize < (8 if args.stage == 'stress' else 1)*1024**3:
            raise ValueError('Insufficient output disk space')
        snapshot(run,'before')
        command = [str(root/'pose180_validate'), str(root), str(run/'results'), args.stage]
        save(run/'command.json', dict(argv=command, automatic_retry=False, reboot=False, HDMI=False))
        started = time.monotonic()
        with (run/'stdout.log').open('wb') as stdout, (run/'stderr.log').open('wb') as stderr, (run/'resources.jsonl').open('w') as resources:
            child = subprocess.Popen(command, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, start_new_session=True)
            stat = Path('/proc/%d/stat'%child.pid).read_text()
            save(run/'process.json', dict(pid=child.pid, start_ticks=stat[stat.rfind(')')+2:].split()[19], started=time.time()))
            previous_kernel = (run/'before.dmesg').read_bytes()
            while child.poll() is None:
                try:
                    status = Path('/proc/%d/status'%child.pid).read_text()
                    memory = Path('/proc/meminfo').read_text()
                    def field(name, content):
                        match = re.search(r'^'+name+r':\s+(\d+)',content,re.M)
                        return int(match.group(1)) if match else None
                    row = dict(elapsed=time.monotonic()-started,rss_kib=field('VmRSS',status),data_kib=field('VmData',status),
                               available_kib=field('MemAvailable',memory),threads=field('Threads',status),
                               fds=len(list(Path('/proc/%d/fd'%child.pid).iterdir())))
                    resources.write(json.dumps(row)+'\n');resources.flush()
                    if row['available_kib'] < 98304 or (row['rss_kib'] or 0) > 524288:
                        raise RuntimeError('Actual memory safety cap exceeded')
                    free = os.statvfs(str(root))
                    if free.f_bavail*free.f_frsize < 512*1024**2:
                        raise RuntimeError('Output disk safety reserve reached')
                    kernel = subprocess.check_output(['dmesg'])
                    if kernel != previous_kernel:
                        additions = kernel[len(previous_kernel):] if kernel.startswith(previous_kernel) else kernel
                        if re.search(rb'Out of memory|oom-kill|Oops:|Kernel panic|Bus error|Call Trace:', additions, re.I):
                            raise RuntimeError('New critical kernel error; preserve and stop')
                        previous_kernel = kernel
                except (FileNotFoundError, ProcessLookupError):
                    if child.poll() is not None:
                        break
                    raise
                # Bound only this explicitly authorized run, not a quiet-tool heuristic.
                if time.monotonic()-started > (1930 if args.stage=='stress' else 180):
                    raise RuntimeError('Explicit phase time budget exhausted')
                time.sleep(2)
            native = child.wait()
        if native:
            raise RuntimeError('Native validation failed; no retry or stress continuation')
    except BaseException as error:
        failure = repr(error)
        if child and child.poll() is None:
            stop(child)
            native = child.returncode
    finally:
        snapshot(run,'after')
        unchanged = all(sha(Path('/usr/lib/aarch64-linux-gnu')/n)==d for n,d in package['libraries'].items())
        same_boot = not (run/'before.boot-id').exists() or (run/'before.boot-id').read_bytes()==(run/'after.boot-id').read_bytes()
        subprocess.run([sys.executable,str(root/'preflight.py'),str(run/'post-preflight.json')],check=True)
        post = load(run/'post-preflight.json')
        boot_files_match = sorted(post['boot_files'], key=lambda x:x['name']) == sorted(package['expected_boot_files'],key=lambda x:x['name'])
        remaining = owners()
        code = 0 if native==0 and failure is None and unchanged and same_boot and boot_files_match and not remaining else 1
        save(run/'guard-summary.json',dict(native_exit=native,wrapper_error=failure,SDK_unchanged=unchanged,
             boot_id_unchanged=same_boot,boot_files_match=boot_files_match,device_owners=remaining,automatic_retry=False))
        (run/'exit.txt').write_text(str(code)+'\n')
        print(json.dumps(load(run/'guard-summary.json')),flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
