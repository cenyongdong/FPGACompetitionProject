"""身份与资源监测；外层等待超时不杀任务。SDK失败不重试，不改BOOT/SDK。"""
from pathlib import Path
import argparse, hashlib, json, os, re, signal, subprocess, sys, time

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()

def snapshot(root, name):
    (root / (name + '.dmesg')).write_bytes(subprocess.check_output(['dmesg']))
    (root / (name + '.meminfo')).write_bytes(Path('/proc/meminfo').read_bytes())
    (root / (name + '.boot-id')).write_text(Path('/proc/sys/kernel/random/boot_id').read_text())

def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage', required=True, choices=['basic','short','medium','stress'])
    p.add_argument('--session', type=int, required=True)
    p.add_argument('--run-name')
    p.add_argument('--frames', type=int)
    p.add_argument('--max-seconds', type=float)
    p.add_argument('--isolation-stage', choices=['static','live'])
    a = p.parse_args(); root = Path(__file__).resolve().parent
    target = {'basic': 3, 'short': 900, 'medium': 9000, 'stress': 54000}[a.stage]
    if a.frames is not None:
        if not 1 <= a.frames <= 54000: raise ValueError('Invalid frame bound')
        target = a.frames
    if a.max_seconds is not None and not 1 <= a.max_seconds <= 1800: raise ValueError('Invalid hard budget')
    name = a.run_name or a.stage
    if not re.fullmatch(r'[a-zA-Z0-9-]+', name): raise ValueError('Invalid run name')
    run = root / ('run-' + name); run.mkdir()
    batch_start = time.monotonic()
    ledger_path = root / 'isolation-budget.json'
    ledger = None
    if a.isolation_stage:
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {'loads':0,'elapsed_seconds':0,'stopped':False,'stages':[]}
        if ledger['stopped'] or ledger['loads']>=2: raise ValueError('Isolation batch closed; no new load')
        if a.isolation_stage=='static' and ledger['loads']!=0: raise ValueError('Static stage may execute only once')
        if a.isolation_stage=='live' and (ledger['loads']!=1 or ledger['stages'][0]['native_exit']!=0): raise ValueError('Live stage requires successful static control')
        stage_limit=300 if a.isolation_stage=='static' else 1200
        if a.max_seconds is None or a.max_seconds>stage_limit: raise ValueError('Isolation stage hard budget required')
        if ledger['elapsed_seconds']+a.max_seconds>1740: raise ValueError('Reserve 60 seconds within cumulative 1800-second budget')
    identity = json.loads((root / 'identity.json').read_text())
    subprocess.run([sys.executable, str(root / 'preflight.py'), str(run / 'preflight.json')], check=True)
    before = json.loads((run / 'preflight.json').read_text())
    if sorted(before['boot_files'], key=lambda x:x['name']) != sorted(identity['expected_boot_files'], key=lambda x:x['name']):
        raise ValueError('Actual BOOT partition identity changed; no SDK initialization')
    if before['fpga_state'] != 'operating': raise ValueError('FPGA not operating')
    if before['SDK_packages'] != ['customop arm64 3.39.0', 'icraft arm64 3.39.0']: raise ValueError('SDK version changed')
    for name, expected in identity['libraries'].items():
        if sha('/usr/lib/aarch64-linux-gnu/' + name) != expected: raise ValueError('SDK identity changed: ' + name)
    for name, expected in identity['files'].items():
        if sha(root / name) != expected: raise ValueError('Package identity changed: ' + name)
    for line in before['processes'].splitlines()[1:]:
        parts = line.split()
        if len(parts) > 1 and parts[1].startswith('pose_'): raise ValueError('Existing inference process')
    owners = []
    for fd in Path('/proc').glob('[0-9]*/fd/*'):
        try:
            name = os.readlink(str(fd))
            if name.startswith(('/dev/axi', '/dev/udmabuf', '/dev/u-dma', '/dev/video')): owners.append([str(fd),name])
        except OSError: pass
    if owners: raise ValueError('Device already owned: ' + repr(owners))
    if os.statvfs(str(root)).f_bavail * os.statvfs(str(root)).f_frsize < 4*1024**3: raise ValueError('Insufficient output disk space')
    snapshot(run, 'before')
    command = [str(root / 'pose_demo_v1'), str(root), str(run / 'results'), str(target), str(a.session), '39382']
    if a.isolation_stage=='static': command=[str(root/'pose_static_read'),str(run/'results'),str(target)]
    (run / 'command.json').write_text(json.dumps({'argv': command, 'HDMI': False, 'reboot': False, 'automatic_retry': False}))
    with (run / 'stderr.txt').open('wb') as err, (run / 'resources.jsonl').open('w') as resources:
        if ledger is not None:
            ledger['loads']+=1
            ledger['stopped']=True # Reserve one attempt before launch; crash cannot reopen it.
            ledger_path.write_text(json.dumps(ledger,indent=2))
        child = subprocess.Popen(command, stderr=err, start_new_session=True)
        (run / 'pid').write_text(str(child.pid)); start = time.monotonic()
        danger = None
        budget_expired = False
        while child.poll() is None:
            if a.max_seconds is not None and time.monotonic()-(batch_start if ledger is not None else start) >= a.max_seconds:
                budget_expired = True
                os.killpg(child.pid, signal.SIGTERM)
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL)
                break
            try:
                status = Path('/proc/%d/status' % child.pid).read_text()
                memory = Path('/proc/meminfo').read_text()
                def field(name, text):
                    m = re.search(r'^' + name + r':\s+(\d+)', text, re.M); return int(m.group(1)) if m else None
                row = {'elapsed': time.monotonic()-start, 'rss_kib': field('VmRSS',status),
                       'data_kib':field('VmData',status), 'threads':field('Threads',status),
                       'available_kib':field('MemAvailable',memory),
                       'fds':len(list(Path('/proc/%d/fd' % child.pid).iterdir()))}
                resources.write(json.dumps(row)+'\n'); resources.flush()
                if row['available_kib'] < 98304 or (row['rss_kib'] or 0) > 524288:
                    danger = row; os.killpg(child.pid, signal.SIGTERM)
                    try: child.wait(timeout=10)
                    except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL)
            except FileNotFoundError: pass
            time.sleep(2)
        code = child.wait()
    snapshot(run, 'after')
    boot_unchanged = (run/'before.boot-id').read_bytes() == (run/'after.boot-id').read_bytes()
    libraries_unchanged = all(sha('/usr/lib/aarch64-linux-gnu/'+n)==s for n,s in identity['libraries'].items())
    report = {'native_exit':code, 'boot_id_unchanged':boot_unchanged, 'SDK_unchanged':libraries_unchanged,
              'elapsed_seconds':time.monotonic()-start, 'hard_budget_seconds':a.max_seconds, 'budget_expired':budget_expired,
              'resource_danger':danger, 'kernel_log_changed':(run/'before.dmesg').read_bytes()!=(run/'after.dmesg').read_bytes()}
    (run/'guard-summary.json').write_text(json.dumps(report,indent=2))
    (run/'exit.txt').write_text(str(code)+'\n')
    if ledger is not None:
        ledger['elapsed_seconds']+=time.monotonic()-batch_start
        ledger['stages'].append({'stage':a.isolation_stage,'native_exit':code,'run':run.name,'elapsed_seconds':time.monotonic()-batch_start})
        ledger['stopped']=bool(code or budget_expired or danger or not boot_unchanged or not libraries_unchanged or a.isolation_stage=='live')
        ledger_path.write_text(json.dumps(ledger,indent=2))
    print('DEMO_GUARD_COMPLETE', json.dumps(report), flush=True)
    return code or (0 if boot_unchanged and libraries_unchanged and not danger else 1)

if __name__ == '__main__': raise SystemExit(main())
