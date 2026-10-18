"""One-time local evidence collection. No network or device operations."""
import base64
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / '.local/nexmon-rtac86u-20261017-r1'
EVIDENCE = Path(__file__).resolve().parent
DELIVERY = TASK / 'delivery'


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    DELIVERY.mkdir(exist_ok=False)
    for name in ['dhd.ko', 'dlarray_4366c0.bin', 'nexutil-aarch64',
                 'makecsiparams-aarch64', 'makecsiparams-x86_64']:
        shutil.copy2(TASK / 'artifacts/build-r8' / name, DELIVERY / name)
    shutil.copy2(TASK / 'artifacts/capture-r2/capture-udp5500-aarch64', DELIVERY)
    shutil.copy2(ROOT / 'tools/nexmon/router/preflight.sh', DELIVERY)
    delivery_files = sorted(DELIVERY.iterdir())
    (DELIVERY / 'SHA256SUMS').write_text(
        ''.join(f'{sha(p)}  {p.name}\n' for p in delivery_files), encoding='ascii')
    logs = EVIDENCE / 'logs'
    logs.mkdir(exist_ok=False)
    for path in TASK.glob('*.log'):
        shutil.copy2(path, logs / path.name)
    shutil.copytree(TASK / 'final-audit/build-log', EVIDENCE / 'firmware-native-log')
    for relative in ['final-audit/audit.log', 'final-audit/module-verification.json',
                     'final-audit/syntax-params-archive.log', 'final-audit/image-identity.txt',
                     'final-audit/container-cleanup.txt', 'final-audit/containers-after.txt',
                     'reference-check-r1/upstream-reference.json', 'loopback-smoke-r1/result.json']:
        source = TASK / relative
        target = EVIDENCE / ('loopback-result.json' if relative.endswith('result.json') else source.name)
        shutil.copy2(source, target)
    shutil.copy2(DELIVERY / 'SHA256SUMS', EVIDENCE / 'delivery-SHA256SUMS')
    params_log = (TASK / 'final-audit/syntax-params-archive.log').read_text(encoding='utf-8-sig')
    valid = next(line for line in params_log.splitlines() if line.startswith('JNAB'))
    decoded = base64.b64decode(valid, validate=True)
    assert len(decoded) == 34 and decoded[:4] == bytes.fromhex('24d00117')
    assert decoded[6:8] == b'\x01\x00' and decoded[8:14] == bytes.fromhex('021122334455')
    assert 'INVALID_TOOL_EXIT=0' in params_log and 'SOURCE_ARCHIVE_READABLE=1' in params_log
    (EVIDENCE / 'parameter-verification.json').write_text(json.dumps(dict(
        passed=True, device_operation=False, example_only=True, length=len(decoded),
        chanspec=hex(int.from_bytes(decoded[:2], 'little')), core_mask=7, stream_mask=1,
        source_mac='02:11:22:33:44:55', invalid_upstream_tool_exit=0), indent=2))
    artifact_paths = delivery_files + [TASK / 'final-audit/linux-build-checkpoint.tar.gz',
                                     TASK / 'final-audit/dhd-original.ko']
    script_paths = sorted(p for p in (ROOT / 'tools/nexmon').rglob('*')
                          if p.is_file() and (p.suffix in ('.py', '.sh', '.c')
                                              or p.parent.name == 'environment')
                          and '__pycache__' not in p.parts and 'firmware-native-log' not in p.parts)
    manifest = dict(schema=1, date='2026-10-17', hardware_test=False,
                    image='fpga-nexmon-rtac86u:20261017-r3',
                    image_id='sha256:101bab0d9b2f7a5b70133e6611aa5d8ca484046646871efbf78029d605f5be85',
                    volume='nexmon-rtac86u-20261017-r1',
                    sources=dict(nexmon='68720406f54ff16cad28fd3c51f2392aefad9fb7',
                                 nexmon_csi='1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e'),
                    artifacts=[dict(path=str(p.relative_to(ROOT)).replace('\\', '/'),
                                    bytes=p.stat().st_size, sha256=sha(p)) for p in artifact_paths],
                    scripts=[dict(path=str(p.relative_to(ROOT)).replace('\\', '/'),
                                  sha256=sha(p)) for p in script_paths])
    (EVIDENCE / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(dict(delivery_files=len(delivery_files), evidence_logs=len(list(logs.iterdir())),
                          artifact_checksums=len(artifact_paths), passed=True)))


if __name__ == '__main__':
    main()
