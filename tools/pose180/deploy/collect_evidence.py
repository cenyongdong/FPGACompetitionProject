"""Archive a completed model stress run without touching SDK/device state."""
import hashlib
import json
import lzma
from pathlib import Path
import sys
import tarfile
import time


root = Path(sys.argv[1]).resolve()
run = root/'run-stress'
if not (run/'exit.txt').is_file() or not (run/'guard-summary.json').is_file():
    raise RuntimeError('Run still active or final guard evidence missing; do not archive')
archive = root/'stress-evidence.tar.xz'
started = time.monotonic()
members = ['run-stress', 'identity.json', 'stress-policy.json',
           'numerical-policy.json', 'controller.json', 'controller.log']
with archive.open('xb') as target:
    with lzma.LZMAFile(target, mode='w', preset=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|') as bundle:
            for name in members:
                source = root/name
                if source.exists():
                    bundle.add(str(source), arcname=name)
                print(json.dumps(dict(archived=name, elapsed=time.monotonic()-started)), flush=True)
digest = hashlib.sha256()
with archive.open('rb') as source:
    for block in iter(lambda: source.read(1048576), b''):
        digest.update(block)
report = dict(archive=str(archive), bytes=archive.stat().st_size,
              sha256=digest.hexdigest(), elapsed=time.monotonic()-started,
              native_exit=json.loads((run/'guard-summary.json').read_text())['native_exit'],
              method='tar.xz preset0; completed run only; no device/SDK load')
(root/'collection.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
