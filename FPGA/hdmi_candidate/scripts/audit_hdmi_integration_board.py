"""Fresh bounded read-only board state; no SDK initialization or register access."""
from pathlib import Path
import json, shlex, shutil, subprocess, sys, time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
W = R / '.local/hdmi-integration-20261016-r1'
O = E / 'board-resume-readonly'
O.mkdir(exist_ok=False)
old = R / 'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
transport = (R / '.local/hdmi-board-reference-20261016-r1/secure_transport.py').read_text(encoding='utf-8')
transport = transport.replace("REMOTE = '/tmp/hdmi-board-reference-20261016-r1/'", "REMOTE = '/tmp/hdmi-integration-20261016-r1/'")
(W / 'secure_transport.py').write_text(transport, encoding='utf-8')
code = (old / 'board-readonly-code.py').read_text(encoding='utf-8')
(O / 'board-readonly-code.py').write_text(code, encoding='utf-8')
t = time.monotonic()
p = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'ssh',
                    'python3 -c ' + shlex.quote(code), '--timeout', '30',
                    '--log', str(O / 'remote.txt')], capture_output=True, timeout=40)
(O / 'stdout.txt').write_bytes(p.stdout)
(O / 'stderr.txt').write_bytes(p.stderr)
(O / 'execution.json').write_text(json.dumps({'exit': p.returncode, 'seconds': time.monotonic() - t,
    'transport_budget_seconds': 30, 'outer_budget_seconds': 40, 'configuration_writes': False}, indent=2) + '\n')
shutil.copyfile(Path(__file__), O / Path(__file__).name)
if p.returncode:
    raise SystemExit('Board read-only audit failed; stop dependent board operations')
data = json.loads((O / 'remote.txt').read_text(encoding='utf-8'))
(O / 'audit.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: data[k] for k in ['BOOT', 'boot_id', 'fpga_state', 'device_owners', 'fpga_sysfs', 'devcfg_devices']}, indent=2))
