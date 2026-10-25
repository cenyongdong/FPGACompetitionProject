"""Explicit-file upload and host-key-checked SSH for this training branch."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile

PROJECT = Path(__file__).resolve().parents[2]
ALGORITHM = Path('D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo')
REMOTE = '/public/cyd/Person-in-WiFi-3D-repo'
SSH = 'C:/Windows/System32/OpenSSH/ssh.exe'
SCP = 'C:/Windows/System32/OpenSSH/scp.exe'
OPTIONS = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['upload', 'run', 'get'])
    parser.add_argument('argument', nargs='?')
    parser.add_argument('destination', nargs='?')
    args = parser.parse_args()
    if args.action == 'run':
        raise SystemExit(subprocess.call([SSH, *OPTIONS, 'gpu-server', args.argument]))
    if args.action == 'get':
        raise SystemExit(subprocess.call([SCP, *OPTIONS, 'gpu-server:' + args.argument, args.destination]))
    files = list((ALGORITHM / 'opera/models/pose180').glob('*.py'))
    files += list((ALGORITHM / 'tools/pose180').glob('*.py'))
    files += [ALGORITHM / ('configs/wifi/' + name) for name in
              ('petr_wifi_pose180_shared.py', 'petr_wifi_pose180_smoke.py')]
    manifest = {}
    archive = PROJECT / 'tools/pose180/delivery.tar'
    with tarfile.open(archive, 'w') as package:
        for path in sorted(files):
            ast.parse(path.read_text(encoding='utf-8'))
            name = path.relative_to(ALGORITHM).as_posix()
            manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            package.add(path, arcname=name)
        data = json.dumps(manifest, indent=2).encode()
        entry = tarfile.TarInfo('pose180-upload-manifest.json')
        entry.size = len(data)
        package.addfile(entry, io.BytesIO(data))
    (archive.parent / 'upload-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    temporary = '/public/cyd/pose180-upload-20261022-r1.tar'
    subprocess.run([SCP, *OPTIONS, str(archive), 'gpu-server:' + temporary], check=True)
    code = '''import hashlib,json,tarfile
from pathlib import Path
root=Path(%r).resolve()
with tarfile.open(%r) as archive:
 manifest=json.load(archive.extractfile('pose180-upload-manifest.json'))
 prior=root/'tools/pose180/upload-manifest.json'
 previous=json.loads(prior.read_text()) if prior.exists() else {}
 for name,expected in manifest.items():
  target=(root/name).resolve()
  if root not in target.parents: raise ValueError('Upload path escapes project')
  if target.exists() and name not in previous: raise ValueError('Refuse to overwrite pre-existing file: '+name)
  if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=previous[name]: raise ValueError('Remote file changed outside upload: '+name)
 for name,expected in manifest.items():
  target=root/name; content=archive.extractfile(name).read()
  if hashlib.sha256(content).hexdigest()!=expected: raise ValueError('Upload content mismatch')
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
 prior.write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps(dict(uploaded=len(manifest),files=list(manifest))))
''' % (REMOTE, temporary)
    subprocess.run([SSH, *OPTIONS, 'gpu-server', 'python3 -c ' + shlex.quote(code)], check=True)


if __name__ == '__main__':
    main()
