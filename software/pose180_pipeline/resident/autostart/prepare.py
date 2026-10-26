"""Build a router-only persistent package from qualified radio assets.

No board/BOOT/SDK payload, no router access. New guard and capture must already
be cross-compiled in OUTPUT/build. Historical finite packages stay immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parent
ROLES = {
    'rx1': ('192.168.50.1', '04:d4:c4:b5:83:40'),
    'tx': ('192.168.50.2', 'f0:2f:74:39:45:68'),
    'rx2': ('192.168.50.3', '04:d9:f5:92:29:20'),
    'rx3': ('192.168.50.4', '04:d4:c4:1a:cb:68'),
}


def prepare(out):
    old = ROOT / '.local/pose180-resident-witness-20261025-r9/radios'
    receipts = {}
    for role, (ip, mac) in ROLES.items():
        folder = out / 'packages' / role
        runtime = folder / 'runtime'
        runtime.mkdir(parents=True)
        names = ['dhd-csi.ko', 'nexutil']
        names += ['tx.lease', 'run.params'] if role == 'tx' else ['makecsiparams', 'capture-metadata']
        for name in names:
            shutil.copyfile(old / role / name, runtime / name)
        shutil.copyfile(out / 'build/router_guard', runtime / 'router_guard')
        if role != 'tx':
            shutil.copyfile(out / 'build/capture-metadata-stream', runtime / 'capture-metadata-stream')
        for name in ('load.sh', 'restore.sh'):
            content = (old / role / name).read_text().replace(
                f'/tmp/nexmon-resident-witness-20261025-r9-{role}', '/tmp/pose180-csi')
            if name == 'restore.sh' and role == 'tx':
                # No speculative second free when stop proof was unavailable.
                # Configuration may never have started (load failure/stop).
                content = content.replace(
                    'if [ ! -e tx.released ]; then\n ./nexutil -Ieth6 -s431 || true\n ./nexutil -Ieth6 -s432 || true\nfi',
                    'if [ -e source.attempt ] && [ ! -e tx.released ]; then\n'
                    ' echo "TX release not proven; leaving firmware lease to expire; no unload"\n exit 76\nfi')
            (runtime / name).write_text(content, newline='\n')
        (runtime / 'identity.conf').write_text(
            f"ROUTER_IP={ip}\nROUTER_MAC={mac}\nGUARD_ROLE={'tx' if role == 'tx' else 'rx'}\n", newline='\n')
        shutil.copyfile(SOURCE / 'watchdog.sh', runtime / 'watchdog.sh')
        shutil.copyfile(SOURCE / 'service.sh', folder / 'service.sh')
        (folder / 'enabled').touch()
        archive = out / f'{role}-autostart.tar.gz'
        with tarfile.open(archive, 'x:gz') as tar:
            for path in sorted(folder.rglob('*')):
                if path.is_file():
                    info = tar.gettarinfo(str(path), arcname=path.relative_to(folder).as_posix())
                    info.mode = 0o700 if path.suffix == '.sh' or path.name in (
                        'nexutil', 'makecsiparams', 'capture-metadata', 'capture-metadata-stream', 'router_guard') else 0o600
                    with path.open('rb') as file:
                        tar.addfile(info, file)
        receipts[role] = dict(ip=ip, mac=mac, archive_bytes=archive.stat().st_size,
                              sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    (out / 'package.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(json.dumps(receipts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    prepare(parser.parse_args().output.resolve())
