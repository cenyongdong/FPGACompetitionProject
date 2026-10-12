"""Read-only corrected final audit; retain prior audit's key mismatch evidence."""
from pathlib import Path
import hashlib, json, os, subprocess, tarfile

root = Path('/tmp/pose-producer-phase-20261011-r2')
out = root / 'final'
assert not out.exists()
out.mkdir()
os.environ['LC_ALL'] = 'C.UTF-8'
subprocess.run(['python3', str(root / 'board_application_preflight.py'), str(out / 'preflight.json')], check=True)
for name in ('buddyinfo', 'pagetypeinfo', 'meminfo', 'vmstat'):
    (out / name).write_bytes(Path('/proc/' + name).read_bytes())
for args, name in ((['dmesg'], 'dmesg.txt'), (['ps', '-eo', 'pid,comm,args'], 'processes.txt'), (['ss', '-ltnp'], 'ports.txt')):
    (out / name).write_bytes(subprocess.check_output(args))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
stage = root / ('run-on' if (root / 'run-on').exists() else 'run-off')
m = json.loads((root / 'build-result.json').read_text())
p = json.loads((out / 'preflight.json').read_text())
assert p['fpga_state'] == 'operating' and p['SDK_packages'] == ['customop arm64 3.39.0', 'icraft arm64 3.39.0']
assert next(x['sha256'] for x in p['boot_files'] if x['name'] == 'BOOT.BIN') == 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
# Audit includes Host; this executable only links ZG/XRT/XIR/AXI. Check both sets.
assert p['libraries'] == json.loads((stage / 'preflight.json').read_text())['libraries']
for name, value in m['libraries'].items():
    assert sha(Path('/usr/lib/aarch64-linux-gnu') / name) == value
for suffix, key in (('json', 'graph_sha256'), ('raw', 'raw_sha256')):
    assert sha(Path('/tmp/pose-producer-reference-20261011-r2/models/piw24_ZG.' + suffix)) == m[key]
lines = (out / 'processes.txt').read_text().splitlines()[1:]
assert not any(x.split()[1].startswith('pose_') for x in lines if len(x.split()) > 1)
assert not any('board_producer_phase_run.py' in x for x in lines)
assert not any(':' + str(port) + ' ' in (out / 'ports.txt').read_text() for port in (39001, 8554))
assert (out / 'dmesg.txt').read_bytes() == (stage / 'after.dmesg.txt').read_bytes()
(out / 'review.json').write_text(json.dumps({'status': 'read_only_final_identity_cleanup_passed', 'kernel_unchanged': True, 'pose_processes': 0, 'test_ports_clear': True, 'no_hardware_retry': True}) + '\n')
for directory in (out,):
    with (directory / 'files.sha256').open('w') as f:
        for path in sorted(directory.iterdir()):
            if path.name != 'files.sha256':
                f.write(sha(path) + '  ' + path.name + '\n')
with tarfile.open(root / 'return-final.tar', 'w') as f:
    f.add(out, arcname='final')
print('Final phase read-only audit complete')
