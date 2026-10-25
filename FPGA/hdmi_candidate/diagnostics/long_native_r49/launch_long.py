"""Detach the single authorized long controller from the monitoring SSH session."""
from pathlib import Path
import json, os, subprocess, sys

base = Path(__file__).resolve().parent
meta = base / 'metadata'
boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
admission = json.loads((base / 'startup-admission.json').read_text())
if not admission['passed'] or admission['boot_id'] != boot_id:
    raise RuntimeError('Startup admission or runtime differs')
argv = ['python3', str(base / 'ps_release_board.py'), 'long-test']
with (meta / 'long-controller.attempt.json').open('x') as f:
    json.dump(dict(boot_id=boot_id, argv=argv, automatic_retry=False), f)
with (base / 'long-controller.stdout.log').open('xb') as so, (base / 'long-controller.stderr.log').open('xb') as se:
    p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=so, stderr=se, start_new_session=True)
with (meta / 'long-controller-issued.json').open('x') as f:
    json.dump(dict(pid=p.pid, boot_id=boot_id, argv=argv), f)
print(json.dumps(dict(issued=True, pid=p.pid, boot_id=boot_id)), flush=True)
