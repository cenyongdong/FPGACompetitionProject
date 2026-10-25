from pathlib import Path
import hashlib, json, tarfile
base = Path(__file__).resolve().parent
out = base / 'candidate-evidence.tar.gz'
if out.exists():
    raise RuntimeError('Preserve existing evidence archive')
with tarfile.open(out, 'x:gz') as tar:
    for name in ('metadata', 'startup', 'startup-admission.json', 'long-test',
                 'long-controller.stdout.log', 'long-controller.stderr.log',
                 'software/run-long-native', 'software/startup-mode.txt',
                 'config.json', 'authorization.json', 'host-session.json'):
        source = base / name
        if source.exists():
            tar.add(source, arcname=name, recursive=True)
print(json.dumps(dict(file=str(out), bytes=out.stat().st_size,
                     sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
